"""
语义数据库查询模块 - 封装所有查询相关的数据库操作
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Union


class SemanticQueryRepository:
    """语义数据查询类"""

    array_fields = ['mood', 'genre', 'scene', 'style']

    def __init__(self, sem_conn: sqlite3.Connection):
        """
        初始化语义查询仓库

        Args:
            sem_conn: 语义数据库连接对象
        """
        self.sem_conn = sem_conn

    def _parse_tag_value(self, value: Optional[str], field: str) -> Union[str, List[str], None]:
        """
        解析标签值（如果是数组字段则从 JSON 转为数组）

        Args:
            value: 数据库中存储的字符串值
            field: 字段名

        Returns:
            解析后的值（数组字段返回 list，其他返回 str 或 None）
        """
        if value is None or not value.strip():
            return None
        if field in self.array_fields:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    def _parse_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析一行数据，处理数组字段

        Args:
            row: 原始行数据

        Returns:
            解析后的数据
        """
        parsed = {}
        for key, value in row.items():
            parsed[key] = self._parse_tag_value(value, key)
        return parsed

    def get_song_tags(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取歌曲的语义标签

        Args:
            file_id: 歌曲ID

        Returns:
            包含所有维度标签的字典，如果歌曲不存在则返回 None
        """
        cursor = self.sem_conn.execute("""
            SELECT mood, energy, genre, style, scene, region, culture, language
            FROM music_semantic
            WHERE file_id = ?
        """, (file_id,))

        row = cursor.fetchone()
        if row:
            return {
                'mood': self._parse_tag_value(row[0], 'mood'),
                'energy': row[1],
                'genre': self._parse_tag_value(row[2], 'genre'),
                'style': self._parse_tag_value(row[3], 'style'),
                'scene': self._parse_tag_value(row[4], 'scene'),
                'region': row[5],
                'culture': row[6],
                'language': row[7]
            }
        return None

    def get_all_songs(self) -> List[Dict[str, Any]]:
        """
        获取所有歌曲的语义标签

        Returns:
            歌曲列表，每首歌包含所有语义标签字段
        """
        cursor = self.sem_conn.execute("""
            SELECT file_id, title, artist, album, mood, energy, genre,
                   style, scene, region, culture, language, confidence
            FROM music_semantic
        """)
        return [self._parse_row(dict(row)) for row in cursor.fetchall()]

    def get_song_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取歌曲信息

        Args:
            file_id: 歌曲ID

        Returns:
            歌曲信息字典，如果不存在则返回 None
        """
        cursor = self.sem_conn.execute("""
            SELECT file_id, title, artist, album, mood, energy, genre,
                   style, scene, region, culture, language, confidence
            FROM music_semantic
            WHERE file_id = ?
        """, (file_id,))
        row = cursor.fetchone()
        return self._parse_row(dict(row)) if row else None

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
            SELECT file_id, title, artist, album, mood, energy, genre,
                   style, scene, region, culture, language, confidence
            FROM music_semantic
            WHERE mood LIKE ?
            ORDER BY confidence DESC
            LIMIT ?
        """, (f'%"{mood}"%', limit))
        return [self._parse_row(dict(row)) for row in cursor.fetchall()]

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
            conditions.append("mood LIKE ?")
            params.append(f'%"{mood}"%')
        if energy:
            conditions.append("energy = ?")
            params.append(energy)
        if genre:
            conditions.append("genre LIKE ?")
            params.append(f'%"{genre}"%')
        if region:
            conditions.append("region = ?")
            params.append(region)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor = self.sem_conn.execute(f"""
            SELECT file_id, title, artist, album, mood, energy, genre,
                   style, scene, region, culture, language, confidence
            FROM music_semantic
            WHERE {where_clause}
            ORDER BY RANDOM()
            LIMIT ?
        """, params + [limit])

        return [self._parse_row(dict(row)) for row in cursor.fetchall()]

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
            SELECT file_id, title, artist, album, mood, energy, genre,
                   style, scene, region, culture, language, confidence
            FROM music_semantic
            WHERE file_id IN ({placeholders})
        """, file_ids)

        return [self._parse_row(dict(row)) for row in cursor.fetchall()]

    def get_total_count(self) -> int:
        """
        获取歌曲总数

        Returns:
            歌曲总数
        """
        return self.sem_conn.execute(
            "SELECT COUNT(*) FROM music_semantic"
        ).fetchone()[0]
