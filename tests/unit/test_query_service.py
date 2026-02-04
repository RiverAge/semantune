"""
测试查询服务
"""
import pytest
from unittest.mock import Mock, MagicMock

from src.services.query_service import QueryService


class TestQueryService:
    """测试查询服务类"""

    def test_query_service_initialization(self):
        """测试服务初始化"""
        song_repo = Mock()
        service = QueryService(song_repo)
        
        assert service.song_repo == song_repo

    def test_query_by_mood(self):
        """测试按情绪查询歌曲"""
        song_repo = Mock()
        expected_songs = [
            {"id": 1, "title": "Song 1", "mood": "happy"},
            {"id": 2, "title": "Song 2", "mood": "happy"}
        ]
        song_repo.get_songs_by_tags.return_value = expected_songs
        
        service = QueryService(song_repo)
        result = service.query_by_mood("happy", limit=10)
        
        assert result == expected_songs
        song_repo.get_songs_by_tags.assert_called_once_with(mood="happy", limit=10)

    def test_query_by_mood_default_limit(self):
        """测试按情绪查询歌曲（使用默认限制）"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.return_value = []
        
        service = QueryService(song_repo)
        service.query_by_mood("happy")
        
        song_repo.get_songs_by_tags.assert_called_once_with(mood="happy", limit=20)

    def test_query_by_mood_empty_result(self):
        """测试按情绪查询歌曲（空结果）"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.return_value = []
        
        service = QueryService(song_repo)
        result = service.query_by_mood("nonexistent")
        
        assert result == []

    def test_query_by_tags_single_tag(self):
        """测试按单个标签查询"""
        song_repo = Mock()
        expected_songs = [
            {"id": 1, "title": "Song 1", "energy": "high"}
        ]
        song_repo.get_songs_by_tags.return_value = expected_songs
        
        service = QueryService(song_repo)
        result = service.query_by_tags(energy="high", limit=5)
        
        assert result == expected_songs
        song_repo.get_songs_by_tags.assert_called_once_with(
            mood=None, energy="high", genre=None, region=None, limit=5
        )

    def test_query_by_tags_multiple_tags(self):
        """测试按多个标签查询"""
        song_repo = Mock()
        expected_songs = [
            {"id": 1, "title": "Song 1", "mood": "happy", "genre": "pop", "region": "欧美"}
        ]
        song_repo.get_songs_by_tags.return_value = expected_songs
        
        service = QueryService(song_repo)
        result = service.query_by_tags(
            mood="happy",
            genre="pop",
            region="欧美",
            limit=15
        )
        
        assert result == expected_songs
        song_repo.get_songs_by_tags.assert_called_once_with(
            mood="happy", energy=None, genre="pop", region="欧美", limit=15
        )

    def test_query_by_tags_all_none(self):
        """测试所有标签都为 None"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.return_value = []
        
        service = QueryService(song_repo)
        result = service.query_by_tags()
        
        assert result == []
        song_repo.get_songs_by_tags.assert_called_once_with(
            mood=None, energy=None, genre=None, region=None, limit=20
        )

    def test_query_by_tags_empty_result(self):
        """测试按标签查询（空结果）"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.return_value = []
        
        service = QueryService(song_repo)
        result = service.query_by_tags(mood="nonexistent")
        
        assert result == []

    def test_query_by_scene_preset(self):
        """测试按场景预设查询"""
        song_repo = Mock()
        expected_songs = [
            {"id": 1, "title": "Study Song", "scene": "学习"},
            {"id": 2, "title": "Focus Song", "scene": "专注"}
        ]
        song_repo.get_songs_by_scene_preset.return_value = expected_songs
        
        service = QueryService(song_repo)
        result = service.query_by_scene_preset("学习", limit=10)
        
        assert result == expected_songs
        song_repo.get_songs_by_scene_preset.assert_called_once_with("学习", 10)

    def test_query_by_scene_preset_default_limit(self):
        """测试按场景预设查询（使用默认限制）"""
        song_repo = Mock()
        song_repo.get_songs_by_scene_preset.return_value = []
        
        service = QueryService(song_repo)
        service.query_by_scene_preset("专注")
        
        song_repo.get_songs_by_scene_preset.assert_called_once_with("专注", 20)

    def test_query_by_scene_preset_empty_result(self):
        """测试按场景预设查询（空结果）"""
        song_repo = Mock()
        song_repo.get_songs_by_scene_preset.return_value = []
        
        service = QueryService(song_repo)
        result = service.query_by_scene_preset("nonexistent")
        
        assert result == []

    def test_search_songs(self):
        """测试搜索歌曲"""
        song_repo = Mock()
        expected_songs = [
            {"id": 1, "title": "Hello World", "artist": "Artist"},
            {"id": 2, "title": "Hello Goodbye", "artist": "Artist 2"}
        ]
        song_repo.search_songs_with_tags.return_value = expected_songs
        
        service = QueryService(song_repo)
        result = service.search_songs("Hello", limit=5)
        
        assert result == expected_songs
        song_repo.search_songs_with_tags.assert_called_once_with("Hello", 5)

    def test_search_songs_default_limit(self):
        """测试搜索歌曲（使用默认限制）"""
        song_repo = Mock()
        song_repo.search_songs_with_tags.return_value = []
        
        service = QueryService(song_repo)
        service.search_songs("test")
        
        song_repo.search_songs_with_tags.assert_called_once_with("test", 20)

    def test_search_songs_empty_result(self):
        """测试搜索歌曲（空结果）"""
        song_repo = Mock()
        song_repo.search_songs_with_tags.return_value = []
        
        service = QueryService(song_repo)
        result = service.search_songs("nonexistent song")
        
        assert result == []

    def test_search_songs_empty_query(self):
        """测试搜索歌曲（空查询）"""
        song_repo = Mock()
        song_repo.search_songs_with_tags.return_value = []
        
        service = QueryService(song_repo)
        result = service.search_songs("")
        
        assert result == []
        song_repo.search_songs_with_tags.assert_called_once_with("", 20)

    def test_get_available_scenes(self):
        """测试获取可用场景"""
        song_repo = Mock()
        service = QueryService(song_repo)
        
        scenes = service.get_available_scenes()
        
        assert isinstance(scenes, list)

    def test_get_available_moods(self):
        """测试获取可用情绪标签"""
        song_repo = Mock()
        service = QueryService(song_repo)
        
        moods = service.get_available_moods()
        
        assert isinstance(moods, list)

    def test_get_available_energies(self):
        """测试获取可用能量标签"""
        song_repo = Mock()
        service = QueryService(song_repo)
        
        energies = service.get_available_energies()
        
        assert isinstance(energies, list)

    def test_get_available_genres(self):
        """测试获取可用流派标签"""
        song_repo = Mock()
        service = QueryService(song_repo)
        
        genres = service.get_available_genres()
        
        assert isinstance(genres, list)

    def test_get_available_regions(self):
        """测试获取可用地区标签"""
        song_repo = Mock()
        service = QueryService(song_repo)
        
        regions = service.get_available_regions()
        
        assert isinstance(regions, list)

    def test_query_by_mood_repository_error(self):
        """测试仓库返回错误时的处理"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.side_effect = Exception("Database error")
        
        service = QueryService(song_repo)
        
        with pytest.raises(Exception) as exc_info:
            service.query_by_mood("happy")
        
        assert "Database error" in str(exc_info.value)

    def test_query_by_tags_repository_error(self):
        """测试按标签查询时仓库错误"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.side_effect = Exception("Connection failed")
        
        service = QueryService(song_repo)
        
        with pytest.raises(Exception) as exc_info:
            service.query_by_tags(mood="happy")
        
        assert "Connection failed" in str(exc_info.value)

    def test_search_songs_repository_error(self):
        """测试搜索时仓库错误"""
        song_repo = Mock()
        song_repo.search_songs_with_tags.side_effect = Exception("Search failed")
        
        service = QueryService(song_repo)
        
        with pytest.raises(Exception) as exc_info:
            service.search_songs("test")
        
        assert "Search failed" in str(exc_info.value)

    def test_query_by_scene_preset_repository_error(self):
        """测试按场景查询时仓库错误"""
        song_repo = Mock()
        song_repo.get_songs_by_scene_preset.side_effect = Exception("Preset error")
        
        service = QueryService(song_repo)
        
        with pytest.raises(Exception) as exc_info:
            service.query_by_scene_preset("学习")
        
        assert "Preset error" in str(exc_info.value)

    def test_query_by_mood_large_limit(self):
        """测试大限制值"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.return_value = []
        
        service = QueryService(song_repo)
        service.query_by_mood("happy", limit=100)
        
        song_repo.get_songs_by_tags.assert_called_once_with(mood="happy", limit=100)

    def test_query_by_mood_small_limit(self):
        """测试小限制值"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.return_value = []
        
        service = QueryService(song_repo)
        service.query_by_mood("happy", limit=1)
        
        song_repo.get_songs_by_tags.assert_called_once_with(mood="happy", limit=1)

    def test_query_by_mood_zero_limit(self):
        """测试零限制值"""
        song_repo = Mock()
        song_repo.get_songs_by_tags.return_value = []
        
        service = QueryService(song_repo)
        service.query_by_mood("happy", limit=0)
        
        song_repo.get_songs_by_tags.assert_called_once_with(mood="happy", limit=0)
