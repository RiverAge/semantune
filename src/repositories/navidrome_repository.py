"""
Navidrome 数据库访问层 - 封装所有 Navidrome 相关的数据库操作
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional


class NavidromeRepository:
    """Navidrome 数据访问类"""

    def __init__(self, nav_conn: sqlite3.Connection):
        """
        初始化 Navidrome 仓库

        Args:
            nav_conn: Navidrome 数据库连接对象
        """
        self.nav_conn = nav_conn

    def get_all_songs(self) -> List[Dict[str, Any]]:
        """
        获取所有歌曲信息

        Returns:
            歌曲列表，每首歌包含 id, title, artist, album 等信息
        """
        cursor = self.nav_conn.execute("""
            SELECT id, title, artist, album, duration, path, lyrics
            FROM media_file
            ORDER BY title
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_song_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取歌曲信息

        Args:
            file_id: 歌曲ID

        Returns:
            歌曲信息字典，如果不存在则返回 None
        """
        cursor = self.nav_conn.execute("""
            SELECT id, title, artist, album, duration, path, lyrics
            FROM media_file
            WHERE id = ?
        """, (file_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_songs_by_ids(self, file_ids: List[str]) -> List[Dict[str, Any]]:
        """
        根据ID列表获取歌曲信息

        Args:
            file_ids: 歌曲ID列表

        Returns:
            歌曲列表
        """
        if not file_ids:
            return []

        placeholders = ','.join('?' * len(file_ids))
        cursor = self.nav_conn.execute(f"""
            SELECT id, title, artist, album, duration, path, lyrics
            FROM media_file
            WHERE id IN ({placeholders})
        """, file_ids)

        return [dict(row) for row in cursor.fetchall()]

    def search_songs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索歌曲

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
        cursor = self.nav_conn.execute("""
            SELECT id, title, artist, album, duration, path, lyrics
            FROM media_file
            WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
            ORDER BY title
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))

        return [dict(row) for row in cursor.fetchall()]

    def get_total_count(self) -> int:
        """
        获取歌曲总数

        Returns:
            歌曲总数
        """
        return self.nav_conn.execute(
            "SELECT COUNT(*) FROM media_file"
        ).fetchone()[0]

    def get_artists(self) -> List[Dict[str, Any]]:
        """
        获取所有艺术家

        Returns:
            艺术家列表
        """
        cursor = self.nav_conn.execute("""
            SELECT DISTINCT artist
            FROM media_file
            WHERE artist IS NOT NULL AND artist != ''
            ORDER BY artist
        """)
        return [{"name": row[0]} for row in cursor.fetchall()]

    def get_albums(self) -> List[Dict[str, Any]]:
        """
        获取所有专辑

        Returns:
            专辑列表
        """
        cursor = self.nav_conn.execute("""
            SELECT DISTINCT album, artist
            FROM media_file
            WHERE album IS NOT NULL AND album != ''
            ORDER BY album
        """)
        return [{"name": row[0], "artist": row[1]} for row in cursor.fetchall()]

    def extract_lyrics_text(self, lyrics: Optional[str]) -> Optional[str]:
        """
        从 lyrics 字段提取纯文本歌词

        Args:
            lyrics: 歌词字段，可能是 JSON 格式或纯文本

        Returns:
            提取的歌词文本，如果歌词为空则返回 None
        """
        if not lyrics or not lyrics.strip():
            return None

        lyrics = lyrics.strip()

        try:
            parsed = json.loads(lyrics)
            if isinstance(parsed, dict):
                return parsed.get('text')
            elif isinstance(parsed, str):
                return parsed
            return str(parsed)
        except (json.JSONDecodeError, TypeError):
            return lyrics
