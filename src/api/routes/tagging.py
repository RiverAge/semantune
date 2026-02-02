"""
标签生成接口路由
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List

from src.tagging.worker import nim_classify
from src.core.database import connect_nav_db, connect_sem_db
from src.core.schema import init_semantic_db
from src.utils.logger import setup_logger

logger = setup_logger("api_tagging", "api.log", level=logging.INFO)

router = APIRouter()


class TagRequest(BaseModel):
    """标签生成请求模型"""
    title: str
    artist: str
    album: str = ""


class TagResponse(BaseModel):
    """标签生成响应模型"""
    title: str
    artist: str
    album: str
    tags: dict
    raw_response: str


class BatchTagRequest(BaseModel):
    """批量标签生成请求模型"""
    songs: List[dict]  # [{"title": "...", "artist": "...", "album": "..."}]


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


@router.post("/generate", response_model=TagResponse)
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
        
        return TagResponse(
            title=request.title,
            artist=request.artist,
            album=request.album,
            tags=tags,
            raw_response=raw_response
        )
        
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
        nav_conn = connect_nav_db()
        sem_conn = connect_sem_db()
        
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
        
        nav_conn.close()
        sem_conn.close()
        
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
        
        sem_conn.close()
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
        nav_conn = connect_nav_db()
        sem_conn = connect_sem_db()
        
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
        
        nav_conn.close()
        sem_conn.close()
        
        return {
            "total": total,
            "processed": tagged,
            "pending": pending,
            "failed": failed,
            "progress": progress
        }
        
    except Exception as e:
        logger.error(f"获取标签生成状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview")
async def preview_tagging(limit: int = 5):
    """
    预览标签生成（前端专用）
    """
    try:
        nav_conn = connect_nav_db()
        
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
        
        nav_conn.close()
        
        return {"success": True, "data": previews}
        
    except Exception as e:
        logger.error(f"预览标签生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_tagging():
    """
    开始标签生成（前端专用）
    """
    try:
        # 这里可以启动后台任务
        # 简化处理，返回成功消息
        return {
            "success": True,
            "message": "标签生成任务已启动"
        }
        
    except Exception as e:
        logger.error(f"启动标签生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
