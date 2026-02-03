"""
语义数据库访问层 - 封装所有语义标签相关的数据库操作
"""

import sqlite3
from typing import List, Dict, Any, Optional

from .semantic_query import SemanticQueryRepository
from .semantic_stats import SemanticStatsRepository


class SemanticRepository:
    """语义数据访问类 - 组合查询和统计功能"""

    def __init__(self, sem_conn: sqlite3.Connection):
        """
        初始化语义仓库

        Args:
            sem_conn: 语义数据库连接对象
        """
        self.sem_conn = sem_conn
        self.query = SemanticQueryRepository(sem_conn)
        self.stats = SemanticStatsRepository(sem_conn)

    # 查询方法 - 委托给 SemanticQueryRepository
    def get_song_tags(self, file_id: str) -> Optional[Dict[str, str]]:
        """获取歌曲的语义标签"""
        return self.query.get_song_tags(file_id)

    def get_all_songs(self) -> List[Dict[str, Any]]:
        """获取所有歌曲的语义标签"""
        return self.query.get_all_songs()

    def get_song_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取歌曲信息"""
        return self.query.get_song_by_id(file_id)

    def query_by_mood(self, mood: str, limit: int = 20) -> List[Dict[str, Any]]:
        """按情绪查询歌曲"""
        return self.query.query_by_mood(mood, limit)

    def query_by_tags(
        self,
        mood: Optional[str] = None,
        energy: Optional[str] = None,
        genre: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """按多个标签组合查询"""
        return self.query.query_by_tags(mood, energy, genre, region, limit)

    def get_songs_by_ids(self, file_ids: List[str]) -> List[Dict[str, Any]]:
        """根据ID列表获取歌曲信息"""
        return self.query.get_songs_by_ids(file_ids)

    def get_total_count(self) -> int:
        """获取歌曲总数"""
        return self.query.get_total_count()

    # 统计方法 - 委托给 SemanticStatsRepository
    def get_distribution(self, field: str) -> List[Dict[str, Any]]:
        """获取指定字段的分布统计"""
        return self.stats.get_distribution(field)

    def get_combinations(self, limit: int = 15) -> List[Dict[str, Any]]:
        """获取最常见的 Mood + Energy 组合"""
        return self.stats.get_combinations(limit)

    def get_region_genre_distribution(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取各地区流派分布"""
        return self.stats.get_region_genre_distribution()

    def get_quality_stats(self) -> Dict[str, Any]:
        """获取数据质量统计"""
        return self.stats.get_quality_stats()

    # 保存方法 - 保留在主类中
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
