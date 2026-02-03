"""
用户相关工具模块 - 提取自 recommend/engine.py 和 profile/builder.py 的重复函数
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from config.settings import WEIGHT_CONFIG
from src.core.database import connect_nav_db, connect_sem_db

logger = logging.getLogger(__name__)


def get_user_id(nav_conn, auto_select: bool = True) -> str:
    """
    获取用户ID（如果只有一个用户，自动选择）
    
    Args:
        nav_conn: Navidrome 数据库连接对象
        auto_select: 是否自动选择第一个用户（用于 API 环境）
        
    Returns:
        用户ID字符串
        
    Raises:
        ValueError: 用户输入无效时抛出
    """
    cursor = nav_conn.execute("SELECT id, user_name FROM user")
    users = cursor.fetchall()

    if len(users) == 1:
        return users[0][0]

    # API 环境下自动选择第一个用户
    if auto_select:
        return users[0][0]

    # CLI 环境下让用户选择
    print("\n可用用户:")
    for idx, (uid, name) in enumerate(users, 1):
        print(f"  {idx}. {name} ({uid})")

    choice = int(input("\n请选择用户 (输入序号): ")) - 1
    logger.info(f"选择用户: {users[choice][1]} ({users[choice][0]})")
    return users[choice][0]


def get_play_history(nav_conn, user_id: str) -> Dict[str, Dict[str, Any]]:
    """
    获取用户的播放历史和收藏信息
    
    Args:
        nav_conn: Navidrome 数据库连接对象
        user_id: 用户ID
        
    Returns:
        字典，键为歌曲ID，值为包含播放次数、收藏状态、播放时间的字典
        {
            'song_id': {
                'play_count': int,
                'starred': bool,
                'play_date': float (Unix 时间戳)
            }
        }
    """
    cursor = nav_conn.execute("""
        SELECT
            item_id,
            play_count,
            starred,
            play_date
        FROM annotation
        WHERE user_id = ? AND item_type = 'media_file'
    """, (user_id,))

    history = {}
    for row in cursor.fetchall():
        item_id = row[0]
        play_date_str = row[3]

        # 解析时间戳（Navidrome 使用 ISO 8601 格式）
        play_date_ts = 0
        if play_date_str:
            try:
                dt = datetime.fromisoformat(play_date_str.replace('Z', '+00:00'))
                play_date_ts = dt.timestamp()
            except (ValueError, TypeError):
                try:
                    play_date_ts = float(play_date_str)
                except (ValueError, TypeError):
                    play_date_ts = 0

        history[item_id] = {
            'play_count': row[1] or 0,
            'starred': bool(row[2]),
            'play_date': play_date_ts
        }

    return history


def get_playlist_songs(nav_conn, user_id: str) -> Dict[str, int]:
    """
    获取用户歌单中的歌曲
    
    Args:
        nav_conn: Navidrome 数据库连接对象
        user_id: 用户ID
        
    Returns:
        字典，键为歌曲ID，值为该歌曲在歌单中出现的次数
    """
    cursor = nav_conn.execute("""
        SELECT pt.media_file_id, COUNT(*) as playlist_count
        FROM playlist_tracks pt
        JOIN playlist p ON pt.playlist_id = p.id
        WHERE p.owner_id = ?
        GROUP BY pt.media_file_id
    """, (user_id,))

    playlist_songs = {}
    for row in cursor.fetchall():
        playlist_songs[row[0]] = row[1]

    return playlist_songs


def get_song_tags(sem_conn, file_id: str) -> Optional[Dict[str, str]]:
    """
    获取歌曲的语义标签
    
    Args:
        sem_conn: 语义数据库连接对象
        file_id: 歌曲ID
        
    Returns:
        包含 mood, energy, genre, region 的字典，如果歌曲不存在则返回 None
    """
    cursor = sem_conn.execute("""
        SELECT mood, energy, genre, region
        FROM music_semantic
        WHERE file_id = ?
    """, (file_id,))

    row = cursor.fetchone()
    if row:
        return {
            'mood': row[0],
            'energy': row[1],
            'genre': row[2],
            'region': row[3]
        }
    return None


def calculate_time_decay(play_date: float) -> float:
    """
    计算时间衰减系数，用于降低旧播放记录的权重
    
    Args:
        play_date: 播放时间的 Unix 时间戳
        
    Returns:
        衰减系数，范围 [min_decay, 1.0]
        
    计算公式:
        decay = max(min_decay, 1.0 - days_ago / time_decay_days)
    """
    if not play_date:
        return WEIGHT_CONFIG['min_decay']

    now = time.time()
    days_ago = (now - play_date) / 86400

    decay = max(
        WEIGHT_CONFIG['min_decay'],
        1.0 - days_ago / WEIGHT_CONFIG['time_decay_days']
    )

    return decay


def calculate_song_weight(play_data: Dict[str, Any], playlist_count: int) -> float:
    """
    计算单首歌的综合权重
    
    Args:
        play_data: 播放数据字典，包含 play_count, starred, play_date
        playlist_count: 该歌曲在歌单中出现的次数
        
    Returns:
        综合权重值
        
    权重计算:
        - 播放次数 × play_count 权重
        - 收藏加分（固定值）
        - 歌单加分（每个歌单 × in_playlist 权重）
        - 应用时间衰减
    """
    weight = 0.0

    # 1. 播放次数基础权重
    weight += play_data['play_count'] * WEIGHT_CONFIG['play_count']

    # 2. 收藏加分
    if play_data['starred']:
        weight += WEIGHT_CONFIG['starred']

    # 3. 歌单加分
    if playlist_count > 0:
        weight += WEIGHT_CONFIG['in_playlist'] * playlist_count

    # 4. 时间衰减
    decay = calculate_time_decay(play_data['play_date'])
    weight *= decay

    return weight
