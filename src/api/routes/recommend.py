"""
推荐接口路由
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from src.core.database import nav_db_context, sem_db_context, dbs_context
from src.repositories.user_repository import UserRepository
from src.services.service_factory import ServiceFactory
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
        with dbs_context() as (nav_conn, sem_conn):
            user_repo = UserRepository(nav_conn)

            # 获取用户ID
            if request.user_id:
                user_id = request.user_id
            else:
                # API 环境下自动选择第一个用户
                user = user_repo.get_first_user()
                if not user:
                    raise HTTPException(status_code=404, detail="未找到用户")
                user_id = user['id']

            # 获取用户歌曲数
            user_songs = user_repo.get_user_songs(user_id)

            # 创建推荐服务并生成推荐
            recommend_service = ServiceFactory.create_recommend_service(nav_conn, sem_conn)
            recommendations = recommend_service.recommend(
                user_id=user_id,
                limit=request.limit,
                filter_recent=request.filter_recent,
                diversity=request.diversity
            )

            # 统计信息
            stats = {
                "total_recommendations": len(recommendations),
                "user_songs_count": len(user_songs),
                "unique_artists": len(set(r.get('artist') for r in recommendations if r.get('artist'))),
                "unique_albums": len(set(r.get('album') for r in recommendations if r.get('album')))
            }

            logger.info(f"用户 {user_id} 请求推荐，返回 {len(recommendations)} 首歌曲")

            return RecommendResponse(
                user_id=user_id,
                recommendations=recommendations,
                stats=stats
            )

    except HTTPException:
        raise
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
            user_repo = UserRepository(nav_conn)
            users = user_repo.get_all_users()

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
        with dbs_context() as (nav_conn, sem_conn):
            user_repo = UserRepository(nav_conn)
            users = user_repo.get_all_users()

            # 查找用户
            user_id = None
            for user in users:
                if user['name'] == username:
                    user_id = user['id']
                    break

            if not user_id:
                return {
                    "success": False,
                    "error": f"用户 {username} 不存在"
                }

            # 获取推荐
            recommend_service = ServiceFactory.create_recommend_service(nav_conn, sem_conn)
            recommendations = recommend_service.recommend(user_id=user_id, limit=limit)

            logger.info(f"获取推荐: {len(recommendations)} 首")

            return {
                "success": True,
                "data": recommendations
            }

    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{username}")
async def get_user_profile(username: str):
    """
    获取用户画像（前端专用）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            user_repo = UserRepository(nav_conn)
            users = user_repo.get_all_users()

            # 查找用户
            user_id = None
            for user in users:
                if user['name'] == username:
                    user_id = user['id']
                    break

            if not user_id:
                return {
                    "success": False,
                    "error": f"用户 {username} 不存在"
                }

            # 获取用户画像
            profile_service = ServiceFactory.create_profile_service(nav_conn, sem_conn)
            profile = profile_service.build_user_profile(user_id)

            # 获取歌单数量
            playlist_songs = user_repo.get_playlist_songs(user_id)
            playlist_count = len(set(
                nav_conn.execute(
                    "SELECT DISTINCT playlist_id FROM playlist_tracks pt "
                    "JOIN playlist p ON pt.playlist_id = p.id WHERE p.owner_id = ?",
                    (user_id,)
                ).fetchall()
            ))

            # 获取用户听过的歌曲标签统计
            played_songs = user_repo.get_user_songs(user_id)

            # 使用语义仓库获取标签统计
            from src.repositories.semantic_repository import SemanticRepository
            sem_repo = SemanticRepository(sem_conn)

            if played_songs:
                tagged_songs = sem_repo.get_songs_by_ids(played_songs)

                # 统计
                artist_counts = {}
                mood_counts = {}
                energy_counts = {}
                genre_counts = {}

                for song in tagged_songs:
                    artist = song.get('artist')
                    mood = song.get('mood')
                    energy = song.get('energy')
                    genre = song.get('genre')

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
                    "total_plays": profile['stats']['total_plays'],
                    "unique_songs": profile['stats']['unique_songs'],
                    "starred_count": profile['stats']['starred_count'],
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
