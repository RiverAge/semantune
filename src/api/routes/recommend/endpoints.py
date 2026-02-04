"""
推荐接口路由端点
"""
import logging
import os
import csv
import io
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.core.database import nav_db_context, sem_db_context, dbs_context
from src.core.response import ApiResponse
from src.core.exceptions import SemantuneException
from src.repositories.user_repository import UserRepository
from src.repositories.semantic_repository import SemanticRepository
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger
from .models import RecommendRequest, RecommendResponse
from .utils import find_user_id_by_username, find_user_by_id_or_username

# 从环境变量读取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logger = setup_logger("api", level=log_level, console_level=log_level)

router = APIRouter()


@router.post("/", response_model=ApiResponse[RecommendResponse])
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

            # 获取用户信息
            user = find_user_by_id_or_username(user_repo, user_id=request.user_id)
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

            logger.debug(f"用户 {user_id} 请求推荐，返回 {len(recommendations)} 首歌曲")

            return ApiResponse.success_response(
                data=RecommendResponse(
                    user_id=user_id,
                    recommendations=recommendations,
                    stats=stats
                )
            )

    except SemantuneException as e:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users():
    """
    获取所有用户列表（前端专用）
    """
    try:
        with nav_db_context() as nav_conn:
            user_repo = UserRepository(nav_conn)
            users = user_repo.get_all_users()
            # 前端期望的是用户名列表（字符串数组），而不是对象数组
            user_names = [user['name'] for user in users if user.get('name')]

        return {
            "success": True,
            "data": {
                "users": user_names
            }
        }

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

            # 查找用户ID
            try:
                user_id = find_user_id_by_username(user_repo, username)
            except HTTPException as e:
                logger.warning(f"用户 {username} 不存在")
                return {
                    "success": False,
                    "error": {
                        "message": str(e.detail),
                        "type": "user_not_found"
                    }
                }

            logger.info(f"找到用户 ID: {user_id}")

            # 获取推荐
            recommend_service = ServiceFactory.create_recommend_service(nav_conn, sem_conn)
            recommendations = recommend_service.recommend(user_id=user_id, limit=limit)
            logger.info(f"生成 {len(recommendations)} 条推荐")

            # 添加 reason 字段（前端需要）
            for rec in recommendations:
                similarity = rec.get('similarity', 0)
                mood = rec.get('mood', '未知')
                genre = rec.get('genre', '未知')
                rec['reason'] = f"基于您的偏好推荐，相似度 {similarity:.2f}，{mood}风格，{genre}类型"

            logger.info(f"获取推荐成功: {len(recommendations)} 首")

            return {
                "success": True,
                "data": recommendations
            }

    except Exception as e:
        logger.error(f"获取推荐失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{username}")
async def get_user_profile(username: str):
    """
    获取用户画像（前端专用）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            user_repo = UserRepository(nav_conn)

            # 查找用户ID
            try:
                user_id = find_user_id_by_username(user_repo, username)
            except HTTPException:
                return {
                    "success": False,
                    "error": {
                        "message": f"用户 {username} 不存在",
                        "type": "user_not_found"
                    }
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


@router.get("/export")
async def export_all(
    username: str = Query(..., min_length=1, max_length=100, description="用户名"),
    limit: int = Query(default=30, ge=1, le=100, description="推荐数量，范围1-100")
):
    """
    导出推荐歌曲和用户画像数据为Markdown文件
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            user_repo = UserRepository(nav_conn)

            # 查找用户ID
            user_id = find_user_id_by_username(user_repo, username)

            # 获取推荐
            recommend_service = ServiceFactory.create_recommend_service(nav_conn, sem_conn)
            recommendations = recommend_service.recommend(user_id=user_id, limit=limit)

            # 获取播放历史
            play_history = user_repo.get_play_history(user_id)
            
            # 获取歌单歌曲
            playlist_songs = user_repo.get_playlist_songs(user_id)
            
            # 获取歌单列表
            playlists = nav_conn.execute("""
                SELECT id, name, updated_at
                FROM playlist
                WHERE owner_id = ?
                ORDER BY name
            """, (user_id,)).fetchall()

            # 获取语义标签
            sem_repo = SemanticRepository(sem_conn)

            # 创建Markdown内容
            lines = []
            
            # 标题
            lines.append(f"# 个性化推荐报告")
            lines.append("")
            lines.append(f"**用户名**: {username}")
            lines.append(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

            # 统计信息
            total_plays = sum(play_history.get(song_id, {}).get('play_count', 0) for song_id in play_history)
            starred_count = sum(1 for song_id, data in play_history.items() if data.get('starred', False))
            
            lines.append("## 📊 用户画像统计")
            lines.append("")
            lines.append(f"- **总播放次数**: {total_plays}")
            lines.append(f"- **听过歌曲数**: {len(play_history)}")
            lines.append(f"- **收藏歌曲数**: {starred_count}")
            lines.append(f"- **歌单数量**: {len(playlists)}")
            lines.append("")

            # 播放历史
            lines.append("## 🎵 播放历史")
            lines.append("")
            lines.append("| 序号 | 歌曲ID | 标题 | 歌手 | 专辑 | 播放次数 | 收藏 | 最后播放时间 | 情绪 | 能量 | 流派 | 地区 |")
            lines.append("|------|--------|------|------|------|----------|------|--------------|------|------|------|------|")
            
            for idx, (song_id, play_data) in enumerate(sorted(play_history.items(), key=lambda x: x[1].get('play_count', 0), reverse=True), 1):
                # 获取歌曲信息
                song_info = nav_conn.execute("""
                    SELECT title, artist, album
                    FROM media_file
                    WHERE id = ?
                """, (song_id,)).fetchone()
                
                if song_info:
                    title, artist, album = song_info
                else:
                    title, artist, album = '', '', ''
                
                # 获取语义标签
                tags = sem_repo.get_song_tags(song_id)
                
                play_date_str = ''
                if play_data.get('play_date'):
                    try:
                        play_date_str = datetime.fromtimestamp(play_data.get('play_date', 0)).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                lines.append(f"| {idx} | {song_id} | {title} | {artist} | {album} | {play_data.get('play_count', 0)} | {'✓' if play_data.get('starred', False) else ''} | {play_date_str} | {tags.get('mood', '')} | {tags.get('energy', '')} | {tags.get('genre', '')} | {tags.get('region', '')} |")
            
            lines.append("")

            # 收藏歌曲
            starred_songs = [song_id for song_id, data in play_history.items() if data.get('starred', False)]
            if starred_songs:
                lines.append("## ⭐ 收藏歌曲")
                lines.append("")
                lines.append("| 序号 | 歌曲ID | 标题 | 歌手 | 专辑 | 情绪 | 能量 | 流派 | 地区 |")
                lines.append("|------|--------|------|------|------|------|------|------|------|")
                
                for idx, song_id in enumerate(starred_songs, 1):
                    song_info = nav_conn.execute("""
                        SELECT title, artist, album
                        FROM media_file
                        WHERE id = ?
                    """, (song_id,)).fetchone()
                    
                    if song_info:
                        title, artist, album = song_info
                    else:
                        title, artist, album = '', '', ''
                    
                    tags = sem_repo.get_song_tags(song_id)
                    
                    lines.append(f"| {idx} | {song_id} | {title} | {artist} | {album} | {tags.get('mood', '')} | {tags.get('energy', '')} | {tags.get('genre', '')} | {tags.get('region', '')} |")
                
                lines.append("")

            # 歌单信息
            if playlists:
                lines.append("## 📋 歌单信息")
                lines.append("")
                
                for playlist_id, playlist_name, updated_at in playlists:
                    lines.append(f"### {playlist_name}")
                    lines.append("")
                    lines.append("| 序号 | 歌曲ID | 标题 | 歌手 | 专辑 | 情绪 | 能量 | 流派 | 地区 |")
                    lines.append("|------|--------|------|------|------|------|------|------|------|")
                    
                    songs = nav_conn.execute("""
                        SELECT pt.media_file_id, m.title, m.artist, m.album
                        FROM playlist_tracks pt
                        JOIN media_file m ON pt.media_file_id = m.id
                        WHERE pt.playlist_id = ?
                    """, (playlist_id,)).fetchall()
                    
                    for idx, (song_id, title, artist, album) in enumerate(songs, 1):
                        tags = sem_repo.get_song_tags(song_id)
                        lines.append(f"| {idx} | {song_id} | {title} | {artist} | {album} | {tags.get('mood', '')} | {tags.get('energy', '')} | {tags.get('genre', '')} | {tags.get('region', '')} |")
                    
                    lines.append("")

            # 推荐歌曲
            lines.append("## ✨ 推荐歌曲")
            lines.append("")
            lines.append(f"基于您的音乐偏好，为您推荐以下 {len(recommendations)} 首歌曲：")
            lines.append("")
            lines.append("| 序号 | 歌曲ID | 标题 | 歌手 | 专辑 | 年份 | 情绪 | 能量 | 流派 | 地区 | 相似度 | 推荐理由 |")
            lines.append("|------|--------|------|------|------|------|------|------|------|------|--------|----------|")

            for idx, rec in enumerate(recommendations, 1):
                lines.append(f"| {idx} | {rec.get('file_id', '')} | {rec.get('title', '')} | {rec.get('artist', '')} | {rec.get('album', '')} | {rec.get('year', '')} | {rec.get('mood', '')} | {rec.get('energy', '')} | {rec.get('genre', '')} | {rec.get('region', '')} | {rec.get('similarity', 0):.2%} | {rec.get('reason', '')} |")
            
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("*本报告由 Semantune 自动生成*")

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recommendation_report_{username}_{timestamp}.md"

            # 返回Markdown文件
            content = '\n'.join(lines)
            return StreamingResponse(
                io.BytesIO(content.encode('utf-8')),
                media_type='text/markdown; charset=utf-8',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
