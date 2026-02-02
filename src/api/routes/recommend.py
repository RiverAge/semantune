"""
推荐接口路由
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from src.recommend.engine import recommend, get_user_id, get_user_songs
from src.core.database import connect_nav_db
from src.utils.logger import setup_logger

logger = setup_logger("api_recommend", "api.log", level=logging.INFO)

router = APIRouter()


class RecommendRequest(BaseModel):
    """推荐请求模型"""
    user_id: Optional[str] = None  # 用户ID，不传则自动选择第一个用户
    limit: int = 30  # 推荐数量
    filter_recent: bool = True  # 是否过滤最近听过的歌曲
    diversity: bool = True  # 是否启用多样性控制


class RecommendResponse(BaseModel):
    """推荐响应模型"""
    user_id: str
    recommendations: List[dict]
    stats: dict


@router.post("/", response_model=RecommendResponse)
async def get_recommendations(request: RecommendRequest):
    """
    获取个性化推荐
    
    - **user_id**: 用户ID（可选，不传则自动选择第一个用户）
    - **limit**: 推荐数量，默认30
    - **filter_recent**: 是否过滤最近听过的歌曲，默认True
    - **diversity**: 是否启用多样性控制，默认True
    """
    try:
        # 获取用户ID
        nav_conn = connect_nav_db()
        if request.user_id:
            user_id = request.user_id
        else:
            user_id = get_user_id(nav_conn)
        
        # 获取用户歌曲数
        user_songs = get_user_songs(nav_conn, user_id)
        nav_conn.close()
        
        # 生成推荐
        recommendations = recommend(
            user_id=user_id,
            limit=request.limit,
            filter_recent=request.filter_recent,
            diversity=request.diversity,
            verbose=False
        )
        
        # 统计信息
        stats = {
            "total_recommendations": len(recommendations),
            "user_songs_count": len(user_songs),
            "unique_artists": len(set(r['artist'] for r in recommendations)),
            "unique_albums": len(set(r['album'] for r in recommendations))
        }
        
        logger.info(f"用户 {user_id} 请求推荐，返回 {len(recommendations)} 首歌曲")
        
        return RecommendResponse(
            user_id=user_id,
            recommendations=recommendations,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users():
    """
    获取所有用户列表
    """
    try:
        nav_conn = connect_nav_db()
        cursor = nav_conn.execute("SELECT id, user_name FROM user")
        users = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        nav_conn.close()
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
