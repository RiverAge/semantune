"""
语义数据库统计模块 - 封装所有统计相关的数据库操作
"""

import sqlite3
from typing import List, Dict, Any


class SemanticStatsRepository:
    """语义数据统计类"""

    def __init__(self, sem_conn: sqlite3.Connection):
        """
        初始化语义统计仓库

        Args:
            sem_conn: 语义数据库连接对象
        """
        self.sem_conn = sem_conn

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
