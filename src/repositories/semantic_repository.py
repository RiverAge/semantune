"""
语义数据库访问层 - 封装所有语义标签相关的数据库操作
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Union, Tuple

from .semantic_query import SemanticQueryRepository
from .semantic_stats import SemanticStatsRepository
from config.constants import validate_tags_against_whitelist


class SemanticRepository:
    """语义数据访问类 - 组合查询和统计功能"""

    array_fields = ['mood', 'genre', 'scene', 'style']

    def __init__(self, sem_conn: sqlite3.Connection):
        """
        初始化语义仓库

        Args:
            sem_conn: 语义数据库连接对象
        """
        self.sem_conn = sem_conn
        self.query = SemanticQueryRepository(sem_conn)
        self.stats = SemanticStatsRepository(sem_conn)

    def _normalize_tag_value(self, value: Union[str, List[str], None]) -> Optional[str]:
        """
        将标签值归一化为字符串格式（数组字段转为 JSON 字符串）

        Args:
            value: 标签值（字符串或列表）

        Returns:
            归一化后的字符串，如果是数组则转为 JSON，单值或空则不变
        """
        if value is None:
            return None
        if isinstance(value, list):
            return json.dumps(value)
        return value

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

    def delete_songs_by_ids(self, file_ids: List[str]) -> int:
        """
        根据 ID 列表删除语义标签（用于清理孤儿项）

        Args:
            file_ids: 要删除的歌曲 ID 列表

        Returns:
            删除的记录数量
        """
        if not file_ids:
            return 0
        
        placeholders = ','.join('?' * len(file_ids))
        cursor = self.sem_conn.execute(f"""
            DELETE FROM music_semantic
            WHERE file_id IN ({placeholders})
        """, file_ids)
        self.sem_conn.commit()
        return cursor.rowcount

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
        保存歌曲语义标签（旧方法，保持兼容）

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
            (file_id, title, artist, album, mood, energy, genre, style, scene, region, culture, language, confidence, model, validation_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_id, title, artist, album,
            self._normalize_tag_value(tags.get('mood')),
            self._normalize_tag_value(tags.get('energy')),
            self._normalize_tag_value(tags.get('genre')),
            self._normalize_tag_value(tags.get('style')),
            self._normalize_tag_value(tags.get('scene')),
            self._normalize_tag_value(tags.get('region')),
            self._normalize_tag_value(tags.get('culture')),
            self._normalize_tag_value(tags.get('language')),
            confidence, model, 'valid'
        ))
        self.sem_conn.commit()

    def save_song_tags_with_validation(
        self,
        file_id: str,
        title: str,
        artist: str,
        album: str,
        tags: Dict[str, Any],
        confidence: float,
        model: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        保存歌曲语义标签（带白名单验证）

        Args:
            file_id: 歌曲ID
            title: 歌曲标题
            artist: 歌手名称
            album: 专辑名称
            tags: 标签字典
            confidence: 置信度
            model: 使用的模型名称

        Returns:
            (是否保存成功, 验证结果)
            如果有违规标签：
                - 返回 False，记录validation_status='invalid'和invalid_tags
            如果全部合规：
                - 返回 True，记录validation_status='valid'，invalid_tags=NULL
        """
        # 验证标签
        validation_result = validate_tags_against_whitelist(tags)

        if validation_result['is_valid']:
            # 合规：正常保存
            self.sem_conn.execute("""
                INSERT OR REPLACE INTO music_semantic
                (file_id, title, artist, album, mood, energy, genre, style, scene, region, culture, language, confidence, model, validation_status, invalid_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id, title, artist, album,
                self._normalize_tag_value(tags.get('mood')),
                self._normalize_tag_value(tags.get('energy')),
                self._normalize_tag_value(tags.get('genre')),
                self._normalize_tag_value(tags.get('style')),
                self._normalize_tag_value(tags.get('scene')),
                self._normalize_tag_value(tags.get('region')),
                self._normalize_tag_value(tags.get('culture')),
                self._normalize_tag_value(tags.get('language')),
                confidence, model, 'valid', None
            ))
            self.sem_conn.commit()
            return True, validation_result
        else:
            # 不合规：记录但标记为invalid
            invalid_tags_json = json.dumps(validation_result['invalid_tags'], ensure_ascii=False)
            self.sem_conn.execute("""
                INSERT OR REPLACE INTO music_semantic
                (file_id, title, artist, album, mood, energy, genre, style, scene, region, culture, language, confidence, model, validation_status, invalid_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id, title, artist, album,
                self._normalize_tag_value(tags.get('mood')),
                self._normalize_tag_value(tags.get('energy')),
                self._normalize_tag_value(tags.get('genre')),
                self._normalize_tag_value(tags.get('style')),
                self._normalize_tag_value(tags.get('scene')),
                self._normalize_tag_value(tags.get('region')),
                self._normalize_tag_value(tags.get('culture')),
                self._normalize_tag_value(tags.get('language')),
                confidence, model, 'invalid', invalid_tags_json
            ))
            self.sem_conn.commit()
            return False, validation_result
