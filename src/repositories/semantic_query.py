"""
语义数据库查询模块 - 封装所有查询相关的数据库操作
"""

import sqlite3
from typing import List, Dict, Any, Optional


class SemanticQueryRepository:
    """语义数据查询类"""

    def __init__(self, sem_conn: sqlite3.Connection):
        """
        初始化语义查询仓库

        Args:
            sem_conn: 语义数据库连接对象
        """
        self.sem_conn = sem_conn

    def get_song_tags(self, file_id: str) -> Optional[Dict[str, str]]:
        """
        获取歌曲的语义标签

        Args:
            file_id: 歌曲ID

        Returns:
            包含 mood, energy, genre, region, scene, subculture 的字典，如果歌曲不存在则返回 None
        """
        cursor = self.sem_conn.execute("""
            SELECT mood, energy, genre, region, scene, subculture
            FROM music_semantic
            WHERE file_id = ?
        """, (file_id,))

        row = cursor.fetchone()
        if row:
            return {
                'mood': row[0],
                'energy': row[1],
                'genre': row[2],
                'region': row[3],
                'scene': row[4],
                'subculture': row[5]
            }
        return None

    def get_all_songs(self) -> List[Dict[str, Any]]:
        """
        获取所有歌曲的语义标签

        Returns:
            歌曲列表，每首歌包含所有语义标签字段
        """
        cursor = self.sem_conn.execute("""
            SELECT file_id, title, artist, album, mood, energy, scene,
                   region, subculture, genre, confidence
            FROM music_semantic
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
        cursor = self.sem_conn.execute("""
            SELECT file_id, title, artist, album, mood, energy, scene,
                   region, subculture, genre, confidence
            FROM music_semantic
            WHERE file_id = ?
        """, (file_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def query_by_mood(self, mood: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        按情绪查询歌曲

        Args:
            mood: 情绪标签
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
        cursor = self.sem_conn.execute("""
            SELECT title, artist, album, mood, energy, genre, region, confidence
            FROM music_semantic
            WHERE mood = ?
            ORDER BY confidence DESC
            LIMIT ?
        """, (mood, limit))
        return [dict(row) for row in cursor.fetchall()]

    def query_by_tags(
        self,
        mood: Optional[str] = None,
        energy: Optional[str] = None,
        genre: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        按多个标签组合查询

        Args:
            mood: 情绪标签
            energy: 能量标签
            genre: 流派标签
            region: 地区标签
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
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

        cursor = self.sem_conn.execute(f"""
            SELECT title, artist, album, mood, energy, genre, region, confidence
            FROM music_semantic
            WHERE {where_clause}
            ORDER BY RANDOM()
            LIMIT ?
        """, params + [limit])

        return [dict(row) for row in cursor.fetchall()]

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
        cursor = self.sem_conn.execute(f"""
            SELECT file_id, title, artist, album, mood, energy, scene,
                   region, subculture, genre, confidence
            FROM music_semantic
            WHERE file_id IN ({placeholders})
        """, file_ids)

        return [dict(row) for row in cursor.fetchall()]

    def get_total_count(self) -> int:
        """
        获取歌曲总数

        Returns:
            歌曲总数
        """
        return self.sem_conn.execute(
            "SELECT COUNT(*) FROM music_semantic"
        ).fetchone()[0]
