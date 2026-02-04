"""
查询服务 - 封装歌曲查询的业务逻辑
"""

from typing import List, Dict, Any, Optional

from config.constants import get_allowed_labels, get_scene_presets, SCENE_PRESETS
from src.repositories.song_repository import SongRepository


class QueryService:
    """查询服务类"""

    def __init__(self, song_repo: SongRepository):
        """
        初始化查询服务

        Args:
            song_repo: 歌曲数据仓库
        """
        self.song_repo = song_repo

    def query_by_mood(self, mood: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        按情绪查询歌曲

        Args:
            mood: 情绪标签
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
        return self.song_repo.get_songs_by_tags(mood=mood, limit=limit)

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
        return self.song_repo.get_songs_by_tags(
            mood=mood,
            energy=energy,
            genre=genre,
            region=region,
            limit=limit
        )

    def query_by_scene_preset(self, scene_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        根据场景预设查询歌曲

        Args:
            scene_name: 场景名称
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
        return self.song_repo.get_songs_by_scene_preset(scene_name, limit)

    def search_songs(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索歌曲

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
        return self.song_repo.search_songs_with_tags(query, limit)

    def get_available_scenes(self) -> List[str]:
        """
        获取可用的场景预设列表

        Returns:
            场景名称列表
        """
        return list(get_scene_presets().keys())

    def get_available_moods(self) -> List[str]:
        """
        获取可用的情绪标签列表

        Returns:
            情绪标签列表
        """
        allowed_labels = get_allowed_labels()
        return list(allowed_labels.get('mood', set()))

    def get_available_energies(self) -> List[str]:
        """
        获取可用的能量标签列表

        Returns:
            能量标签列表
        """
        allowed_labels = get_allowed_labels()
        return list(allowed_labels.get('energy', set()))

    def get_available_genres(self) -> List[str]:
        """
        获取可用的流派标签列表

        Returns:
            流派标签列表
        """
        allowed_labels = get_allowed_labels()
        return list(allowed_labels.get('genre', set()))

    def get_available_regions(self) -> List[str]:
        """
        获取可用的地区标签列表

        Returns:
            地区标签列表
        """
        allowed_labels = get_allowed_labels()
        return list(allowed_labels.get('region', set()))
