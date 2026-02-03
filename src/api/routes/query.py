"""
查询接口路由
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from src.query.search import query_by_mood, query_by_tags, query_scene_preset, find_similar_songs, random_songs
from src.core.database import sem_db_context
from src.utils.logger import setup_logger

logger = setup_logger("api_query", "api.log", level=logging.INFO)

router = APIRouter()


class QueryByMoodRequest(BaseModel):
    """按情绪查询请求模型"""
    mood: str = Field(..., min_length=1, max_length=50, description="情绪标签")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


class QueryByTagsRequest(BaseModel):
    """按标签组合查询请求模型"""
    mood: Optional[str] = Field(None, max_length=50, description="情绪标签")
    energy: Optional[str] = Field(None, max_length=50, description="能量标签")
    genre: Optional[str] = Field(None, max_length=50, description="流派标签")
    region: Optional[str] = Field(None, max_length=50, description="地区标签")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


class QuerySceneRequest(BaseModel):
    """场景查询请求模型"""
    scene: str = Field(..., min_length=1, max_length=50, description="场景标签")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


class FindSimilarRequest(BaseModel):
    """找相似歌曲请求模型"""
    title: str = Field(..., min_length=1, max_length=200, description="歌曲标题")
    artist: str = Field(..., min_length=1, max_length=100, description="歌手名称")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


class RandomRequest(BaseModel):
    """随机推荐请求模型"""
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


@router.post("/mood")
async def query_by_mood_api(request: QueryByMoodRequest):
    """
    按情绪查询歌曲
    
    - **mood**: 情绪标签（如：Energetic, Peaceful, Sad 等）
    - **limit**: 返回数量，默认20
    """
    try:
        with sem_db_context() as sem_conn:
            songs = query_by_mood(sem_conn, request.mood, request.limit)
        
        # 转换为字典列表
        result = [
            {
                "title": song['title'],
                "artist": song['artist'],
                "album": song['album'],
                "mood": song['mood'],
                "energy": song['energy'],
                "genre": song['genre'],
                "region": song['region'],
                "confidence": song['confidence']
            }
            for song in songs
        ]
        
        logger.info(f"按情绪 {request.mood} 查询，返回 {len(result)} 首歌曲")
        return {"songs": result, "count": len(result)}
        
    except Exception as e:
        logger.error(f"按情绪查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tags")
async def query_by_tags_api(request: QueryByTagsRequest):
    """
    按标签组合查询歌曲
    
    - **mood**: 情绪标签（可选）
    - **energy**: 能量标签（可选）
    - **genre**: 流派标签（可选）
    - **region**: 地区标签（可选）
    - **limit**: 返回数量，默认20
    """
    try:
        with sem_db_context() as sem_conn:
            songs = query_by_tags(
            sem_conn,
            mood=request.mood,
            energy=request.energy,
            genre=request.genre,
            region=request.region,
            limit=request.limit
        )
        
        # 转换为字典列表
        result = [
            {
                "title": song['title'],
                "artist": song['artist'],
                "album": song['album'],
                "mood": song['mood'],
                "energy": song['energy'],
                "genre": song['genre'],
                "region": song['region'],
                "confidence": song['confidence']
            }
            for song in songs
        ]
        
        logger.info(f"按标签组合查询，返回 {len(result)} 首歌曲")
        return {"songs": result, "count": len(result)}
        
    except Exception as e:
        logger.error(f"按标签组合查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scene")
async def query_scene_api(request: QuerySceneRequest):
    """
    按预设场景查询歌曲
    
    可用场景：深夜、运动、学习、开车、放松、派对、伤心、励志
    
    - **scene**: 场景名称
    - **limit**: 返回数量，默认20
    """
    try:
        with sem_db_context() as sem_conn:
            songs = query_scene_preset(sem_conn, request.scene, request.limit)
        
        # 转换为字典列表
        result = [
            {
                "title": song['title'],
                "artist": song['artist'],
                "album": song['album'],
                "mood": song['mood'],
                "energy": song['energy'],
                "genre": song['genre'],
                "region": song['region'],
                "confidence": song['confidence']
            }
            for song in songs
        ]
        
        logger.info(f"按场景 {request.scene} 查询，返回 {len(result)} 首歌曲")
        return {"songs": result, "count": len(result)}
        
    except Exception as e:
        logger.error(f"按场景查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similar")
async def find_similar_api(request: FindSimilarRequest):
    """
    找相似歌曲
    
    - **title**: 歌曲标题
    - **artist**: 歌手名称
    - **limit**: 返回数量，默认20
    """
    try:
        with sem_db_context() as sem_conn:
            songs = find_similar_songs(sem_conn, request.title, request.artist, request.limit)
        
        # 转换为字典列表
        result = [
            {
                "title": song['title'],
                "artist": song['artist'],
                "album": song['album'],
                "mood": song['mood'],
                "energy": song['energy'],
                "genre": song['genre'],
                "region": song['region'],
                "confidence": song['confidence']
            }
            for song in songs
        ]
        
        logger.info(f"查找与 {request.artist} - {request.title} 相似的歌曲，返回 {len(result)} 首")
        return {"songs": result, "count": len(result)}
        
    except Exception as e:
        logger.error(f"找相似歌曲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/random")
async def random_api(request: RandomRequest):
    """
    随机推荐歌曲
    
    - **limit**: 返回数量，默认20
    """
    try:
        with sem_db_context() as sem_conn:
            songs = random_songs(sem_conn, request.limit)
        
        # 转换为字典列表
        result = [
            {
                "title": song['title'],
                "artist": song['artist'],
                "album": song['album'],
                "mood": song['mood'],
                "energy": song['energy'],
                "genre": song['genre'],
                "region": song['region'],
                "confidence": song['confidence']
            }
            for song in songs
        ]
        
        logger.info(f"随机推荐，返回 {len(result)} 首歌曲")
        return {"songs": result, "count": len(result)}
        
    except Exception as e:
        logger.error(f"随机推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/labels")
async def get_labels():
    """
    获取所有可用的标签列表
    """
    from config.constants import ALLOWED_LABELS
    
    return {
        "mood": list(ALLOWED_LABELS.get('mood', set())),
        "energy": list(ALLOWED_LABELS.get('energy', set())),
        "genre": list(ALLOWED_LABELS.get('genre', set())),
        "region": list(ALLOWED_LABELS.get('region', set())),
        "scenes": ["深夜", "运动", "学习", "开车", "放松", "派对", "伤心", "励志"]
    }


@router.get("/")
async def query_songs(
    mood: Optional[str] = None,
    energy: Optional[str] = None,
    genre: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 50
):
    """
    按标签组合查询歌曲（前端专用）
    """
    try:
        with sem_db_context() as sem_conn:
            # 构建查询条件
            conditions = []
            params = []
            
            if mood:
                conditions.append("mood = ?")
                params.append(mood)
            if energy:
                conditions.append("energy = ?")
                params.append(energy)
            if genre:
                conditions.append("genre = ?")
                params.append(genre)
            if region:
                conditions.append("region = ?")
                params.append(region)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 查询歌曲
            query = f"""
                SELECT file_id, title, artist, album, mood, energy, scene, region, subculture, genre, confidence
                FROM music_semantic
                WHERE {where_clause}
                LIMIT ?
            """
            params.append(limit)
            
            results = sem_conn.execute(query, params).fetchall()
        
        songs = [
            {
                "file_id": row[0],
                "title": row[1],
                "artist": row[2],
                "album": row[3],
                "mood": row[4],
                "energy": row[5],
                "scene": row[6],
                "region": row[7],
                "subculture": row[8],
                "genre": row[9],
                "confidence": row[10]
            }
            for row in results
        ]
        
        logger.info(f"查询歌曲: {len(songs)} 首")
        
        return {"success": True, "data": songs}
        
    except Exception as e:
        logger.error(f"查询歌曲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options")
async def get_query_options():
    """
    获取查询选项（前端专用）
    """
    try:
        from config.constants import ALLOWED_LABELS
        
        return {
            "success": True,
            "data": {
                "moods": list(ALLOWED_LABELS.get('mood', set())),
                "energies": list(ALLOWED_LABELS.get('energy', set())),
                "genres": list(ALLOWED_LABELS.get('genre', set())),
                "regions": list(ALLOWED_LABELS.get('region', set()))
            }
        }
        
    except Exception as e:
        logger.error(f"获取查询选项失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
