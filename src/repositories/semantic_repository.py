"""
语义数据库访问层 - 封装所有语义标签相关的数据库操作
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple


class SemanticRepository:
    """语义数据访问类"""

    def __init__(self, sem_conn: sqlite3.Connection):
        """
        初始化语义仓库

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

    def get_distribution(self, field: str) -> List[Dict[str, Any]]:
        """
        获取指定字段的分布统计

        Args:
            field: 字段名称 (mood, energy, genre, region, scene, subculture)

        Returns:
            分布列表，每项包含 label, count, percentage
        """
        cursor = self.sem_conn.execute(f"""
            SELECT {field}, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as percentage
            FROM music_semantic
            GROUP BY {field}
            ORDER BY count DESC
        """)

        return [
            {
                "label": row[0] if row[0] else "(空值)",
                "count": row[1],
                "percentage": row[2]
            }
            for row in cursor.fetchall()
        ]

    def get_combinations(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        获取最常见的 Mood + Energy 组合

        Args:
            limit: 返回数量限制

        Returns:
            组合列表
        """
        cursor = self.sem_conn.execute(f"""
            SELECT mood, energy, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as pct
            FROM music_semantic
            GROUP BY mood, energy
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))

        return [
            {
                "mood": row[0],
                "energy": row[1],
                "count": row[2],
                "percentage": row[3]
            }
            for row in cursor.fetchall()
        ]

    def get_region_genre_distribution(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取各地区流派分布

        Returns:
            字典，键为地区，值为该地区的流派分布列表
        """
        regions = self.sem_conn.execute(
            "SELECT DISTINCT region FROM music_semantic WHERE region != 'None'"
        ).fetchall()

        result = {}
        for (region,) in regions:
            cursor = self.sem_conn.execute("""
                SELECT genre, COUNT(*) as count
                FROM music_semantic
                WHERE region = ? AND genre != 'None'
                GROUP BY genre
                ORDER BY count DESC
                LIMIT 5
            """, (region,))

            result[region] = [
                {"genre": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]

        return result

    def get_quality_stats(self) -> Dict[str, Any]:
        """
        获取数据质量统计

        Returns:
            质量统计字典
        """
        total = self.sem_conn.execute(
            "SELECT COUNT(*) FROM music_semantic"
        ).fetchone()[0]

        avg_confidence = self.sem_conn.execute("""
            SELECT AVG(confidence) FROM music_semantic WHERE confidence IS NOT NULL
        """).fetchone()[0] or 0

        low_confidence = self.sem_conn.execute("""
            SELECT COUNT(*) FROM music_semantic
            WHERE confidence < 0.5 OR confidence IS NULL
        """).fetchone()[0]

        none_stats = {}
        for field in ['mood', 'energy', 'scene', 'region', 'subculture', 'genre']:
            none_count = self.sem_conn.execute(
                f"SELECT COUNT(*) FROM music_semantic WHERE {field} = 'None'"
            ).fetchone()[0]
            none_pct = round(none_count * 100.0 / total, 2) if total > 0 else 0
            none_stats[field] = {
                "count": none_count,
                "percentage": none_pct
            }

        return {
            "total_songs": total,
            "average_confidence": round(avg_confidence, 2),
            "low_confidence_count": low_confidence,
            "low_confidence_percentage": round(low_confidence * 100.0 / total, 2) if total > 0 else 0,
            "none_stats": none_stats
        }

    def save_song_tags(
        self,
        file_id: str,
        title: str,
        artist: str,
        album: str,
        tags: Dict[str, Any],
        confidence: float,
        model: str
    ) -> None:
        """
        保存歌曲语义标签

        Args:
            file_id: 歌曲ID
            title: 歌曲标题
            artist: 歌手名称
            album: 专辑名称
            tags: 标签字典
            confidence: 置信度
            model: 使用的模型名称
        """
        self.sem_conn.execute("""
            INSERT OR REPLACE INTO music_semantic
            (file_id, title, artist, album, mood, energy, scene, region, subculture, genre, confidence, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id, title, artist, album,
            tags.get('mood'), tags.get('energy'),
            tags.get('scene'), tags.get('region'),
            tags.get('subculture'), tags.get('genre'),
            confidence, model
        ))
        self.sem_conn.commit()

    def get_total_count(self) -> int:
        """
        获取歌曲总数

        Returns:
            歌曲总数
        """
        return self.sem_conn.execute(
            "SELECT COUNT(*) FROM music_semantic"
        ).fetchone()[0]

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
