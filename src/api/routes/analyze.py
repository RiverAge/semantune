"""
分析接口路由
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.utils.analyze import analyze_distribution, analyze_combinations, analyze_by_region, analyze_quality
from src.core.database import connect_sem_db
from src.utils.logger import setup_logger

logger = setup_logger("api_analyze", "api.log", level=logging.INFO)

router = APIRouter()


class DistributionResponse(BaseModel):
    """分布分析响应模型"""
    field: str
    field_name: str
    distribution: List[Dict[str, Any]]


class CombinationResponse(BaseModel):
    """组合分析响应模型"""
    combinations: List[Dict[str, Any]]


class QualityResponse(BaseModel):
    """质量分析响应模型"""
    total_songs: int
    average_confidence: float
    low_confidence_count: int
    low_confidence_percentage: float
    none_stats: Dict[str, Dict[str, Any]]


class RegionGenreResponse(BaseModel):
    """地区流派分析响应模型"""
    regions: Dict[str, List[Dict[str, Any]]]


@router.get("/distribution/{field}")
async def get_distribution(field: str):
    """
    获取指定字段的分布分析
    
    可用字段：mood, energy, genre, region, scene, subculture
    
    - **field**: 字段名称
    """
    try:
        valid_fields = ['mood', 'energy', 'genre', 'region', 'scene', 'subculture']
        if field not in valid_fields:
            raise HTTPException(status_code=400, detail=f"无效的字段，可用字段: {', '.join(valid_fields)}")
        
        sem_conn = connect_sem_db()
        cursor = sem_conn.execute(f"""
            SELECT {field}, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as percentage
            FROM music_semantic
            GROUP BY {field}
            ORDER BY count DESC
        """)
        
        distribution = []
        for row in cursor:
            distribution.append({
                "label": row[0] if row[0] else "(空值)",
                "count": row[1],
                "percentage": row[2]
            })
        
        sem_conn.close()
        
        logger.info(f"获取 {field} 分布分析，共 {len(distribution)} 个标签")
        
        return DistributionResponse(
            field=field,
            field_name=field.capitalize(),
            distribution=distribution
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分布分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/combinations")
async def get_combinations():
    """
    获取最常见的 Mood + Energy 组合
    """
    try:
        sem_conn = connect_sem_db()
        cursor = sem_conn.execute("""
            SELECT mood, energy, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as pct
            FROM music_semantic
            GROUP BY mood, energy
            ORDER BY count DESC
            LIMIT 15
        """)
        
        combinations = []
        for row in cursor:
            combinations.append({
                "mood": row[0],
                "energy": row[1],
                "count": row[2],
                "percentage": row[3]
            })
        
        sem_conn.close()
        
        logger.info(f"获取组合分析，共 {len(combinations)} 个组合")
        
        return CombinationResponse(combinations=combinations)
        
    except Exception as e:
        logger.error(f"组合分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/region-genre")
async def get_region_genre():
    """
    获取各地区的流派分布
    """
    try:
        sem_conn = connect_sem_db()
        
        # 获取所有地区
        regions_cursor = sem_conn.execute("SELECT DISTINCT region FROM music_semantic WHERE region != 'None'")
        regions = [row[0] for row in regions_cursor.fetchall()]
        
        result = {}
        for region in regions:
            cursor = sem_conn.execute("""
                SELECT genre, COUNT(*) as count
                FROM music_semantic
                WHERE region = ? AND genre != 'None'
                GROUP BY genre
                ORDER BY count DESC
                LIMIT 5
            """, (region,))
            
            genres = []
            for row in cursor:
                genres.append({
                    "genre": row[0],
                    "count": row[1]
                })
            
            result[region] = genres
        
        sem_conn.close()
        
        logger.info(f"获取地区流派分析，共 {len(result)} 个地区")
        
        return RegionGenreResponse(regions=result)
        
    except Exception as e:
        logger.error(f"地区流派分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality")
async def get_quality():
    """
    获取数据质量分析
    """
    try:
        sem_conn = connect_sem_db()
        
        # 总数
        total = sem_conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]
        
        # 平均置信度
        avg_confidence = sem_conn.execute("SELECT AVG(confidence) FROM music_semantic").fetchone()[0]
        avg_confidence = round(avg_confidence, 2) if avg_confidence else 0.0
        
        # 低置信度歌曲
        low_confidence = sem_conn.execute("SELECT COUNT(*) FROM music_semantic WHERE confidence < 0.5").fetchone()[0]
        low_confidence_pct = round(low_confidence * 100.0 / total, 2) if total > 0 else 0.0
        
        # None 值统计
        none_stats = {}
        for field in ['mood', 'energy', 'scene', 'region', 'subculture', 'genre']:
            none_count = sem_conn.execute(f"SELECT COUNT(*) FROM music_semantic WHERE {field} = 'None'").fetchone()[0]
            none_pct = round(none_count * 100.0 / total, 2) if total > 0 else 0.0
            none_stats[field] = {
                "count": none_count,
                "percentage": none_pct
            }
        
        sem_conn.close()
        
        logger.info("获取数据质量分析")
        
        return QualityResponse(
            total_songs=total,
            average_confidence=avg_confidence,
            low_confidence_count=low_confidence,
            low_confidence_percentage=low_confidence_pct,
            none_stats=none_stats
        )
        
    except Exception as e:
        logger.error(f"质量分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary():
    """
    获取数据概览
    """
    try:
        sem_conn = connect_sem_db()
        
        # 总数
        total = sem_conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]
        
        # 各字段唯一值数量
        unique_counts = {}
        for field in ['mood', 'energy', 'genre', 'region', 'scene', 'subculture']:
            count = sem_conn.execute(f"SELECT COUNT(DISTINCT {field}) FROM music_semantic WHERE {field} != 'None'").fetchone()[0]
            unique_counts[field] = count
        
        # 最新更新时间
        latest = sem_conn.execute("SELECT MAX(created_at) FROM music_semantic").fetchone()[0]
        
        sem_conn.close()
        
        logger.info("获取数据概览")
        
        return {
            "total_songs": total,
            "unique_labels": unique_counts,
            "latest_update": latest
        }
        
    except Exception as e:
        logger.error(f"获取数据概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """
    获取整体统计数据（前端专用）
    """
    try:
        sem_conn = connect_sem_db()
        
        # 总歌曲数
        total_songs = sem_conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]
        
        # 已标签歌曲数
        tagged_songs = sem_conn.execute("SELECT COUNT(*) FROM music_semantic WHERE mood IS NOT NULL AND mood != 'None'").fetchone()[0]
        
        # 未标签歌曲数
        untagged_songs = total_songs - tagged_songs
        
        # 标签覆盖率
        tag_coverage = (tagged_songs / total_songs * 100) if total_songs > 0 else 0
        
        # 情绪分布
        mood_dist = sem_conn.execute("""
            SELECT mood, COUNT(*) as count
            FROM music_semantic
            WHERE mood IS NOT NULL AND mood != 'None'
            GROUP BY mood
        """).fetchall()
        mood_distribution = {row[0]: row[1] for row in mood_dist}
        
        # 能量分布
        energy_dist = sem_conn.execute("""
            SELECT energy, COUNT(*) as count
            FROM music_semantic
            WHERE energy IS NOT NULL AND energy != 'None'
            GROUP BY energy
        """).fetchall()
        energy_distribution = {row[0]: row[1] for row in energy_dist}
        
        # 流派分布
        genre_dist = sem_conn.execute("""
            SELECT genre, COUNT(*) as count
            FROM music_semantic
            WHERE genre IS NOT NULL AND genre != 'None'
            GROUP BY genre
        """).fetchall()
        genre_distribution = {row[0]: row[1] for row in genre_dist}
        
        # 地区分布
        region_dist = sem_conn.execute("""
            SELECT region, COUNT(*) as count
            FROM music_semantic
            WHERE region IS NOT NULL AND region != 'None'
            GROUP BY region
        """).fetchall()
        region_distribution = {row[0]: row[1] for row in region_dist}
        
        sem_conn.close()
        
        logger.info("获取整体统计数据")
        
        return {
            "total_songs": total_songs,
            "tagged_songs": tagged_songs,
            "untagged_songs": untagged_songs,
            "tag_coverage": tag_coverage,
            "mood_distribution": mood_distribution,
            "energy_distribution": energy_distribution,
            "genre_distribution": genre_distribution,
            "region_distribution": region_distribution
        }
        
    except Exception as e:
        logger.error(f"获取整体统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_users():
    """
    获取所有用户列表（前端专用）
    """
    try:
        from src.core.database import connect_nav_db
        
        nav_conn = connect_nav_db()
        
        # 获取所有用户
        users = nav_conn.execute("SELECT id, user_name FROM user ORDER BY user_name").fetchall()
        user_list = [row[1] for row in users if row[1]]
        
        nav_conn.close()
        
        logger.info(f"获取用户列表: {len(user_list)} 个用户")
        
        return user_list
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{username}")
async def get_user_stats(username: str):
    """
    获取用户统计数据（前端专用）
    """
    try:
        from src.core.database import connect_nav_db, connect_sem_db
        
        nav_conn = connect_nav_db()
        sem_conn = connect_sem_db()
        
        # 获取用户 ID
        user_id = nav_conn.execute(
            "SELECT id FROM user WHERE user_name = ?",
            (username,)
        ).fetchone()
        
        if not user_id:
            raise HTTPException(status_code=404, detail=f"用户 {username} 不存在")
        
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
        
        nav_conn.close()
        sem_conn.close()
        
        logger.info(f"获取用户统计数据: {username}")
        
        return {
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
        
    except Exception as e:
        logger.error(f"获取用户统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
