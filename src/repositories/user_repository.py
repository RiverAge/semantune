"""
用户数据访问层 - 封装所有用户相关的数据库操作
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime


class UserRepository:
    """用户数据访问类"""

    def __init__(self, nav_conn: sqlite3.Connection):
        """
        初始化用户仓库

        Args:
            nav_conn: Navidrome 数据库连接对象
        """
        self.nav_conn = nav_conn

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        获取所有用户列表

        Returns:
            用户列表，每个用户包含 id 和 user_name
        """
        cursor = self.nav_conn.execute("SELECT id, user_name FROM user")
        return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，如果不存在则返回 None
        """
        cursor = self.nav_conn.execute(
            "SELECT id, user_name FROM user WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1]}
        return None

    def get_first_user(self) -> Optional[Dict[str, Any]]:
        """
        获取第一个用户

        Returns:
            第一个用户信息，如果没有用户则返回 None
        """
        cursor = self.nav_conn.execute("SELECT id, user_name FROM user LIMIT 1")
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "name": row[1]}
        return None

    def get_play_history(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """
        获取用户的播放历史和收藏信息

        Args:
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
        cursor = self.nav_conn.execute("""
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

    def get_playlist_songs(self, user_id: str) -> Dict[str, int]:
        """
        获取用户歌单中的歌曲

        Args:
            user_id: 用户ID

        Returns:
            字典，键为歌曲ID，值为该歌曲在歌单中出现的次数
        """
        cursor = self.nav_conn.execute("""
            SELECT pt.media_file_id, COUNT(*) as playlist_count
            FROM playlist_tracks pt
            JOIN playlist p ON pt.playlist_id = p.id
            WHERE p.owner_id = ?
            GROUP BY pt.media_file_id
        """, (user_id,))

        return {str(row[0]): int(row[1]) for row in cursor.fetchall()}

    def get_user_songs(self, user_id: str) -> List[str]:
        """
        获取用户相关的所有歌曲ID（播放历史 + 歌单）

        Args:
            user_id: 用户ID

        Returns:
            歌曲ID列表
        """
        play_history = self.get_play_history(user_id)
        playlist_songs = self.get_playlist_songs(user_id)
        return list(set(play_history.keys()) | set(playlist_songs.keys()))
