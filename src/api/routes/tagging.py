"""
标签生成接口路由
"""
import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from src.core.database import nav_db_context, sem_db_context, dbs_context
from src.core.schema import init_semantic_db
from src.core.response import ApiResponse
from src.core.exceptions import SemantuneException
from src.repositories.navidrome_repository import NavidromeRepository
from src.repositories.semantic_repository import SemanticRepository
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

logger = setup_logger("api", level=logging.INFO)

router = APIRouter()


class TagRequest(BaseModel):
    """标签生成请求模型"""
    title: str = Field(..., min_length=1, max_length=200, description="歌曲标题")
    artist: str = Field(..., min_length=1, max_length=100, description="歌手名称")
    album: str = Field(default="", max_length=200, description="专辑名称")


class TagResponse(BaseModel):
    """标签生成响应模型"""
    title: str
    artist: str
    album: str
    tags: dict
    raw_response: str


class BatchTagRequest(BaseModel):
    """批量标签生成请求模型"""
    songs: List[dict] = Field(..., min_items=1, max_items=50, description="歌曲列表，最多50首")


class TagProgressResponse(BaseModel):
    """标签生成进度响应模型"""
    total: int
    processed: int
    remaining: int
    status: str


# 全局进度跟踪
tagging_progress = {
    "total": 0,
    "processed": 0,
    "status": "idle"
}

# SSE 客户端队列
sse_clients = []


async def broadcast_progress():
    """向所有 SSE 客户端广播进度"""
    if sse_clients:
        message = f"data: {tagging_progress}\n\n"
        for queue in sse_clients:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"发送进度失败: {e}")


@router.post("/generate")
async def generate_tag(request: TagRequest):
    """
    为单首歌曲生成语义标签

    - **title**: 歌曲标题
    - **artist**: 歌手名称
    - **album**: 专辑名称（可选）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
            result = tagging_service.generate_tag(request.title, request.artist, request.album)

            logger.debug(f"为 {request.artist} - {request.title} 生成标签成功")

            return ApiResponse.success_response(data=result)

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"标签生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_generate_tags(request: BatchTagRequest, background_tasks: BackgroundTasks):
    """
    批量生成语义标签（后台任务）

    - **songs**: 歌曲列表，每首歌曲包含 title, artist, album
    """
    try:
        # 初始化进度
        tagging_progress["total"] = len(request.songs)
        tagging_progress["processed"] = 0
        tagging_progress["status"] = "processing"

        # 添加后台任务
        background_tasks.add_task(process_batch_tags, request.songs)

        logger.debug(f"开始批量生成标签，共 {len(request.songs)} 首歌曲")

        return ApiResponse.success_response(
            data={
                "message": "批量标签生成任务已启动",
                "total": len(request.songs),
                "status": "processing"
            }
        )

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"批量标签生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress", response_model=TagProgressResponse)
async def get_tagging_progress():
    """
    获取批量标签生成进度
    """
    return TagProgressResponse(
        total=tagging_progress["total"],
        processed=tagging_progress["processed"],
        remaining=tagging_progress["total"] - tagging_progress["processed"],
        status=tagging_progress["status"]
    )


@router.post("/sync")
async def sync_tags_to_db():
    """
    同步标签到数据库（从 Navidrome 读取歌曲并生成标签）
    """
    try:
        # 初始化语义数据库
        with sem_db_context() as sem_conn:
            init_semantic_db(sem_conn)

        # 连接数据库
        with dbs_context() as (nav_conn, sem_conn):
            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)

            # 获取所有歌曲
            songs = nav_repo.get_all_songs()

            # 获取已处理的歌曲ID
            tagged_ids = set()
            cursor = sem_conn.execute("SELECT file_id FROM music_semantic")
            for row in cursor.fetchall():
                tagged_ids.add(row[0])

            # 筛选未处理的歌曲
            new_songs = [s for s in songs if s['id'] not in tagged_ids]

        logger.debug(f"找到 {len(new_songs)} 首新歌曲需要生成标签")

        return ApiResponse.success_response(
            data={
                "message": "同步任务准备完成",
                "total_songs": len(songs),
                "processed_songs": len(tagged_ids),
                "new_songs": len(new_songs)
            }
        )

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"同步标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_batch_tags(songs: List[dict]):
    """
    后台处理批量标签生成
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            # 初始化语义数据库
            init_semantic_db(sem_conn)

            for idx, song in enumerate(songs):
                try:
                    # 生成标签
                    tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
                    result = tagging_service.generate_tag(
                        song["title"],
                        song["artist"],
                        song.get("album", "")
                    )

                    if result:
                        # 保存到数据库
                        sem_conn.execute("""
                            INSERT OR REPLACE INTO music_semantic
                            (file_id, title, artist, album, mood, energy, genre, region, subculture, scene, confidence)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            f"song_{idx}",  # 临时ID
                            song["title"],
                            song["artist"],
                            song.get("album", ""),
                            result['tags'].get("mood"),
                            result['tags'].get("energy"),
                            result['tags'].get("genre"),
                            result['tags'].get("region"),
                            result['tags'].get("subculture"),
                            result['tags'].get("scene"),
                            result['tags'].get("confidence", 0.0)
                        ))
                        sem_conn.commit()

                    # 更新进度
                    tagging_progress["processed"] += 1

                except Exception as e:
                    logger.error(f"处理歌曲 {song['artist']} - {song['title']} 失败: {e}")
                    continue

            tagging_progress["status"] = "completed"
            logger.info(f"批量标签生成完成，共处理 {len(songs)} 首歌曲")

    except Exception as e:
        logger.error(f"批量标签生成失败: {e}")
        tagging_progress["status"] = "failed"


@router.get("/status")
async def get_tagging_status():
    """
    获取标签生成状态（前端专用）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            # 初始化语义数据库
            init_semantic_db(sem_conn)

            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)

            # 获取 Navidrome 中的所有歌曲
            total = nav_repo.get_total_count()

            # 获取已标签的歌曲
            tagged = sem_repo.get_total_count()

            # 获取待处理的歌曲
            pending = total - tagged

            # 获取失败的歌曲（这里简化处理，实际可能需要更复杂的逻辑）
            failed = 0

            # 计算进度
            progress = (tagged / total * 100) if total > 0 else 0

        return ApiResponse.success_response(
            data={
                "total": total,
                "processed": tagged,
                "pending": pending,
                "failed": failed,
                "progress": progress,
                "task_status": tagging_progress["status"]  # 返回任务状态
            }
        )

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"获取标签生成状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview")
async def preview_tagging(
    limit: int = Query(default=5, ge=1, le=20, description="预览数量，范围1-20")
):
    """
    预览标签生成（前端专用）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            nav_repo = NavidromeRepository(nav_conn)
            songs = nav_repo.get_all_songs()

            # 为每首歌生成标签
            previews = []
            for song in songs[:limit]:
                try:
                    tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
                    result = tagging_service.generate_tag(
                        song['title'],
                        song['artist'],
                        song.get('album', '')
                    )
                    previews.append({
                        "title": song['title'],
                        "artist": song['artist'],
                        "tags": result['tags']
                    })
                except Exception as e:
                    logger.error(f"生成标签失败: {song['title']} - {song['artist']}: {e}")

        return ApiResponse.success_response(data=previews)

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"预览标签生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream")
async def stream_progress():
    """
    SSE 端点：实时推送标签生成进度
    """
    async def event_generator():
        queue = asyncio.Queue()
        sse_clients.append(queue)

        try:
            # 发送初始状态
            yield f"data: {tagging_progress}\n\n"

            # 如果任务已经完成，立即发送 DONE
            if tagging_progress["status"] in ["completed", "failed"]:
                yield "data: [DONE]\n\n"
                return

            while True:
                # 等待进度更新
                message = await queue.get()
                yield message

                # 如果任务完成，关闭连接
                if tagging_progress["status"] in ["completed", "failed"]:
                    yield "data: [DONE]\n\n"
                    break

        except asyncio.CancelledError:
            pass
        finally:
            if queue in sse_clients:
                sse_clients.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/start")
async def start_tagging(background_tasks: BackgroundTasks):
    """
    开始标签生成（前端专用）
    """
    try:
        # 检查是否已经在运行
        if tagging_progress["status"] == "processing":
            return ApiResponse.error_response(
                message="标签生成任务正在运行中",
                error_type="TaskRunning"
            )

        # 初始化进度
        tagging_progress["total"] = 0
        tagging_progress["processed"] = 0
        tagging_progress["status"] = "processing"

        # 广播初始状态
        await broadcast_progress()

        # 添加后台任务
        background_tasks.add_task(run_tagging_task)

        logger.debug("标签生成任务已启动")

        return ApiResponse.success_response(message="标签生成任务已启动")

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"启动标签生成失败: {e}")
        tagging_progress["status"] = "failed"
        await broadcast_progress()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_tagging():
    """
    中止标签生成任务
    """
    try:
        if tagging_progress["status"] != "processing":
            return ApiResponse.error_response(
                message="没有正在运行的任务",
                error_type="NoRunningTask"
            )

        # 设置状态为已中止
        tagging_progress["status"] = "stopped"
        await broadcast_progress()

        logger.debug("标签生成任务已中止")

        return ApiResponse.success_response(message="标签生成任务已中止")

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"中止标签生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_tagging_history(limit: int = 20, offset: int = 0):
    """
    获取标签生成历史记录

    - **limit**: 每页数量，默认 20
    - **offset**: 偏移量，默认 0
    """
    try:
        with sem_db_context() as sem_conn:
            # 获取历史记录
            cursor = sem_conn.execute("""
                SELECT file_id, title, artist, album, mood, energy, scene,
                       region, subculture, genre, confidence, updated_at
                FROM music_semantic
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

            rows = cursor.fetchall()

            # 获取总数
            total = sem_conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]

            history = []
            for row in rows:
                history.append({
                    "file_id": row[0],
                    "title": row[1],
                    "artist": row[2],
                    "album": row[3],
                    "tags": {
                        "mood": row[4],
                        "energy": row[5],
                        "scene": row[6],
                        "region": row[7],
                        "subculture": row[8],
                        "genre": row[9],
                        "confidence": row[10]
                    },
                    "updated_at": row[11]
                })

        return ApiResponse.success_response(
            data={
                "items": history,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        )

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_tagging_task():
    """
    后台任务：处理所有未标签的歌曲
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            init_semantic_db(sem_conn)

            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)

            # 获取所有歌曲
            nav_songs = nav_repo.get_all_songs()

            # 获取已处理的歌曲ID
            processed_ids = set()
            cursor = sem_conn.execute("SELECT file_id FROM music_semantic")
            for row in cursor.fetchall():
                processed_ids.add(row[0])

            # 筛选未处理的歌曲
            todo_songs = [s for s in nav_songs if s['id'] not in processed_ids]

            # 更新总数
            tagging_progress["total"] = len(todo_songs)
            await broadcast_progress()

            if len(todo_songs) == 0:
                tagging_progress["status"] = "completed"
                await broadcast_progress()
                logger.info("没有需要处理的歌曲")
                return

        # 调用处理函数
        with dbs_context() as (nav_conn, sem_conn):
            tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
            result = tagging_service.process_all_songs()

        # 更新最终状态
        tagging_progress["status"] = "completed"
        await broadcast_progress()
        logger.info(f"标签生成任务完成: {result}")

    except Exception as e:
        logger.error(f"标签生成任务失败: {e}")
        tagging_progress["status"] = "failed"
        await broadcast_progress()
