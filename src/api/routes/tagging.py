"""
标签生成接口路由
"""
import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from src.tagging.worker import nim_classify, process_all_songs
from src.core.database import nav_db_context, sem_db_context
from src.core.schema import init_semantic_db
from src.utils.logger import setup_logger

logger = setup_logger("api_tagging", "api.log", level=logging.INFO)

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
        tags, raw_response = nim_classify(request.title, request.artist, request.album)
        
        if not tags:
            raise HTTPException(status_code=500, detail="标签生成失败")
        
        logger.info(f"为 {request.artist} - {request.title} 生成标签成功")
        
        return {
            "success": True,
            "data": {
                "title": request.title,
                "artist": request.artist,
                "album": request.album,
                "tags": tags,
                "raw_response": raw_response
            }
        }
        
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
        
        logger.info(f"开始批量生成标签，共 {len(request.songs)} 首歌曲")
        
        return {
            "message": "批量标签生成任务已启动",
            "total": len(request.songs),
            "status": "processing"
        }
        
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
        init_semantic_db()
        
        # 连接数据库
        with nav_db_context() as nav_conn, sem_db_context() as sem_conn:
            # 获取所有歌曲
            cursor = nav_conn.execute("""
                SELECT id, title, album_artist, album
                FROM media_file
                WHERE media_file_type = 'music'
            """)
            songs = cursor.fetchall()
            
            # 获取已处理的歌曲ID
            cursor = sem_conn.execute("SELECT file_id FROM music_semantic")
            processed_ids = {row[0] for row in cursor.fetchall()}
            
            # 筛选未处理的歌曲
            new_songs = [song for song in songs if song[0] not in processed_ids]
        
        logger.info(f"找到 {len(new_songs)} 首新歌曲需要生成标签")
        
        return {
            "message": "同步任务准备完成",
            "total_songs": len(songs),
            "processed_songs": len(processed_ids),
            "new_songs": len(new_songs)
        }
        
    except Exception as e:
        logger.error(f"同步标签失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_batch_tags(songs: List[dict]):
    """
    后台处理批量标签生成
    """
    try:
        # 初始化语义数据库
        init_semantic_db()
        
        # 连接数据库
        sem_conn = connect_sem_db()
        
        for idx, song in enumerate(songs):
            try:
                # 生成标签
                tags, _ = nim_classify(song["title"], song["artist"], song.get("album", ""))
                
                if tags:
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
                        tags.get("mood"),
                        tags.get("energy"),
                        tags.get("genre"),
                        tags.get("region"),
                        tags.get("subculture"),
                        tags.get("scene"),
                        tags.get("confidence", 0.0)
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
        with nav_db_context() as nav_conn, sem_db_context() as sem_conn:
            # 初始化语义数据库
            init_semantic_db(sem_conn)
            
            # 获取 Navidrome 中的所有歌曲
            nav_songs = nav_conn.execute("""
                SELECT id, title, album_artist
                FROM media_file
                ORDER BY id
            """).fetchall()
            total = len(nav_songs)
            
            # 获取已标签的歌曲
            tagged = sem_conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]
            
            # 获取待处理的歌曲
            pending = total - tagged
            
            # 获取失败的歌曲（这里简化处理，实际可能需要更复杂的逻辑）
            failed = 0
            
            # 计算进度
            progress = (tagged / total * 100) if total > 0 else 0
        
        return {
            "success": True,
            "data": {
                "total": total,
                "processed": tagged,
                "pending": pending,
                "failed": failed,
                "progress": progress,
                "task_status": tagging_progress["status"]  # 返回任务状态
            }
        }
        
    except Exception as e:
        logger.error(f"获取标签生成状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview")
async def preview_tagging(
    limit: int = Field(default=5, ge=1, le=20, description="预览数量，范围1-20")
):
    """
    预览标签生成（前端专用）
    """
    try:
        with nav_db_context() as nav_conn:
            # 获取一些未标签的歌曲
            songs = nav_conn.execute("""
                SELECT id, title, album_artist
                FROM media_file
                LIMIT ?
            """, (limit,)).fetchall()
            
            # 为每首歌生成标签
            previews = []
            for song in songs:
                file_id, title, artist = song
                try:
                    tags = nim_classify(title, artist, "")
                    previews.append({
                        "title": title,
                        "artist": artist,
                        "tags": tags
                    })
                except Exception as e:
                    logger.error(f"生成标签失败: {title} - {artist}: {e}")
        
        return {"success": True, "data": previews}
        
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
            return {
                "success": False,
                "message": "标签生成任务正在运行中"
            }
        
        # 初始化进度
        tagging_progress["total"] = 0
        tagging_progress["processed"] = 0
        tagging_progress["status"] = "processing"
        
        # 广播初始状态
        await broadcast_progress()
        
        # 添加后台任务
        background_tasks.add_task(run_tagging_task)
        
        logger.info("标签生成任务已启动")
        
        return {
            "success": True,
            "message": "标签生成任务已启动"
        }
        
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
            return {
                "success": False,
                "message": "没有正在运行的任务"
            }
        
        # 设置状态为已中止
        tagging_progress["status"] = "stopped"
        await broadcast_progress()
        
        logger.info("标签生成任务已中止")
        
        return {
            "success": True,
            "message": "标签生成任务已中止"
        }
        
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
        sem_conn = connect_sem_db()
        
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
        
        sem_conn.close()
        
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
        
        return {
            "success": True,
            "data": {
                "items": history,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def run_tagging_task():
    """
    后台任务：处理所有未标签的歌曲
    """
    try:
        # 获取待处理歌曲数量
        nav_conn = connect_nav_db()
        sem_conn = connect_sem_db()
        
        init_semantic_db(sem_conn)
        
        # 获取所有歌曲
        nav_songs = nav_conn.execute("""
            SELECT id, title, artist, album
            FROM media_file
        """).fetchall()
        
        # 获取已处理的歌曲ID
        processed_ids = {row['file_id'] for row in sem_conn.execute("SELECT file_id FROM music_semantic").fetchall()}
        
        # 筛选未处理的歌曲
        todo_songs = [s for s in nav_songs if str(s['id']) not in processed_ids]
        
        nav_conn.close()
        sem_conn.close()
        
        # 更新总数
        tagging_progress["total"] = len(todo_songs)
        await broadcast_progress()
        
        if len(todo_songs) == 0:
            tagging_progress["status"] = "completed"
            await broadcast_progress()
            logger.info("没有需要处理的歌曲")
            return
        
        # 调用处理函数
        result = process_all_songs()
        
        # 更新最终状态
        tagging_progress["status"] = "completed"
        await broadcast_progress()
        logger.info(f"标签生成任务完成: {result}")
        
    except Exception as e:
        logger.error(f"标签生成任务失败: {e}")
        tagging_progress["status"] = "failed"
        await broadcast_progress()
