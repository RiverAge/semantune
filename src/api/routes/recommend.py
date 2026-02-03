"""
推荐接口路由
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from src.recommend.engine import recommend, get_user_songs
from src.core.database import nav_db_context
from src.utils.logger import setup_logger

logger = setup_logger("api", level=logging.INFO)

router = APIRouter()


class RecommendRequest(BaseModel):
    """推荐请求模型"""
    user_id: Optional[str] = None  # 用户ID，不传则自动选择第一个用户
    limit: int = Field(default=30, ge=1, le=100, description="推荐数量，范围1-100")
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
        with nav_db_context() as nav_conn:
            if request.user_id:
                user_id = request.user_id
            else:
                # API 环境下自动选择第一个用户（避免调用 input()）
                cursor = nav_conn.execute("SELECT id FROM user LIMIT 1")
                user_row = cursor.fetchone()
                if not user_row:
                    raise HTTPException(status_code=404, detail="未找到用户")
                user_id = user_row[0]
            
            # 获取用户歌曲数
            user_songs = get_user_songs(nav_conn, user_id)
        
        # 生成推荐
        recommendations = recommend(
            user_id=user_id,
            limit=request.limit,
            filter_recent=request.filter_recent,
            diversity=request.diversity
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
        with nav_db_context() as nav_conn:
            cursor = nav_conn.execute("SELECT id, user_name FROM user")
            users = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def get_recommendations_get(
    username: str = Query(..., min_length=1, max_length=100, description="用户名"),
    limit: int = Query(default=30, ge=1, le=100, description="推荐数量，范围1-100")
):
    """
    获取个性化推荐（前端专用，GET 方法）
    """
    try:
        # 通过用户名获取用户 ID
        with nav_db_context() as nav_conn:
            user_id_result = nav_conn.execute(
                "SELECT id FROM user WHERE user_name = ?",
                (username,)
            ).fetchone()
        
        if not user_id_result:
            return {
                "success": False,
                "error": f"用户 {username} 不存在"
            }
        
        user_id = user_id_result[0]
        
        # 获取推荐（recommend 函数内部会自己连接数据库）
        recommendations = recommend(user_id=user_id, limit=limit)
        
        logger.info(f"获取推荐: {len(recommendations)} 首")
        
        return {
            "success": True,
            "data": recommendations
        }
        
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{username}")
async def get_user_profile(
    username: str
):
    """
    获取用户画像（前端专用）
    """
    try:
        from src.core.database import nav_db_context, sem_db_context
        
        with nav_db_context() as nav_conn, sem_db_context() as sem_conn:
            # 获取用户 ID
            user_id = nav_conn.execute(
            "SELECT id FROM user WHERE user_name = ?",
            (username,)
            ).fetchone()
            
            if not user_id:
                return {
                    "success": False,
                    "error": f"用户 {username} 不存在"
                }
            
            user_id = user_id[0]
            
            # 总播放次数
            total_plays = nav_conn.execute(
            "SELECT COUNT(*) FROM annotation WHERE user_id = ? AND item_type = 'media_file'",
            (user_id,)
            ).fetchone()[0]
            
            # 听过的歌曲数
            unique_songs = nav_conn.execute(
            "SELECT COUNT(DISTINCT item_id) FROM annotation WHERE user_id = ? AND item_type = 'media_file'",
            (user_id,)
            ).fetchone()[0]
            
            # 收藏的歌曲数
            starred_count = nav_conn.execute(
            "SELECT COUNT(*) FROM annotation WHERE user_id = ? AND item_type = 'media_file' AND starred = 1",
            (user_id,)
            ).fetchone()[0]
            
            # 歌单数量
            playlist_count = nav_conn.execute(
            "SELECT COUNT(*) FROM playlist WHERE owner_id = ?",
            (user_id,)
            ).fetchone()[0]
            
            # 获取用户听过的歌曲 ID
            played_songs = nav_conn.execute(
            "SELECT DISTINCT item_id FROM annotation WHERE user_id = ? AND item_type = 'media_file'",
            (user_id,)
            ).fetchall()
            played_song_ids = [row[0] for row in played_songs]
            
            # 获取这些歌曲的标签
            if played_song_ids:
                placeholders = ','.join(['?' for _ in played_song_ids])
                tagged_songs = sem_conn.execute(
                f"SELECT artist, mood, energy, genre FROM music_semantic WHERE file_id IN ({placeholders})",
                played_song_ids
                ).fetchall()
                
                # 统计喜欢的歌手
                artist_counts = {}
                mood_counts = {}
                energy_counts = {}
                genre_counts = {}
                
                for row in tagged_songs:
                    artist, mood, energy, genre = row
                    if artist and artist != 'None':
                        artist_counts[artist] = artist_counts.get(artist, 0) + 1
                    if mood and mood != 'None':
                        mood_counts[mood] = mood_counts.get(mood, 0) + 1
                    if energy and energy != 'None':
                        energy_counts[energy] = energy_counts.get(energy, 0) + 1
                    if genre and genre != 'None':
                        genre_counts[genre] = genre_counts.get(genre, 0) + 1
                
                # 排序并取前 10
                top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                top_moods = sorted(mood_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                top_energies = sorted(energy_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            else:
                top_artists = []
                top_moods = []
                top_energies = []
                top_genres = []
        
            logger.info(f"获取用户画像: {username}")
            
            return {
                "success": True,
                "data": {
                    "username": username,
                    "total_plays": total_plays,
                    "unique_songs": unique_songs,
                    "starred_count": starred_count,
                    "playlist_count": playlist_count,
                    "top_artists": [{"artist": a, "count": c} for a, c in top_artists],
                    "top_moods": [{"mood": m, "count": c} for m, c in top_moods],
                    "top_energies": [{"energy": e, "count": c} for e, c in top_energies],
                    "top_genres": [{"genre": g, "count": c} for g, c in top_genres]
                }
            }
        
    except Exception as e:
        logger.error(f"获取用户画像失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
