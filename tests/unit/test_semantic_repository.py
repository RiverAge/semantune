import pytest
from unittest.mock import Mock, MagicMock, patch
import sqlite3

from src.repositories.semantic_repository import SemanticRepository


class TestSemanticRepository:
    """SemanticRepository 测试"""

    def test_init(self):
        """测试初始化"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        assert repo.sem_conn == mock_conn
        assert repo.query is not None
        assert repo.stats is not None

    def test_get_song_tags(self):
        """测试获取歌曲标签"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_tags = {"mood": "Energetic", "energy": "High"}
        repo.query.get_song_tags = Mock(return_value=mock_tags)
        
        result = repo.get_song_tags("file-123")
        
        assert result == mock_tags
        repo.query.get_song_tags.assert_called_once_with("file-123")

    def test_get_song_tags_none(self):
        """测试获取不存在的歌曲标签"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.get_song_tags = Mock(return_value=None)
        
        result = repo.get_song_tags("nonexistent")
        
        assert result is None

    def test_get_all_songs(self):
        """测试获取所有歌曲"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [
            {"file_id": "1", "title": "Song 1", "mood": "Happy"},
            {"file_id": "2", "title": "Song 2", "mood": "Sad"}
        ]
        repo.query.get_all_songs = Mock(return_value=mock_songs)
        
        result = repo.get_all_songs()
        
        assert result == mock_songs
        repo.query.get_all_songs.assert_called_once()

    def test_get_all_songs_empty(self):
        """测试获取空歌曲列表"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.get_all_songs = Mock(return_value=[])
        
        result = repo.get_all_songs()
        
        assert result == []

    def test_get_song_by_id(self):
        """测试根据 ID 获取歌曲"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_song = {"file_id": "1", "title": "Test Song", "mood": "Energetic"}
        repo.query.get_song_by_id = Mock(return_value=mock_song)
        
        result = repo.get_song_by_id("1")
        
        assert result == mock_song
        repo.query.get_song_by_id.assert_called_once_with("1")

    def test_get_song_by_id_not_found(self):
        """测试获取不存在的歌曲"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.get_song_by_id = Mock(return_value=None)
        
        result = repo.get_song_by_id("nonexistent")
        
        assert result is None

    def test_query_by_mood(self):
        """测试按情绪查询"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [{"file_id": "1", "mood": "Energetic"}]
        repo.query.query_by_mood = Mock(return_value=mock_songs)
        
        result = repo.query_by_mood("Energetic", limit=10)
        
        assert result == mock_songs
        repo.query.query_by_mood.assert_called_once_with("Energetic", 10)

    def test_query_by_mood_default_limit(self):
        """测试按情绪查询使用默认限制"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [{"file_id": "1", "mood": "Energetic"}]
        repo.query.query_by_mood = Mock(return_value=mock_songs)
        
        result = repo.query_by_mood("Energetic")
        
        assert result == mock_songs
        repo.query.query_by_mood.assert_called_once_with("Energetic", 20)

    def test_query_by_mood_no_results(self):
        """测试按情绪查询无结果"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.query_by_mood = Mock(return_value=[])
        
        result = repo.query_by_mood("UnknownMood")
        
        assert result == []

    def test_query_by_tags_multiple(self):
        """测试按多个标签组合查询"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [
            {"file_id": "1", "mood": "Energetic", "energy": "High", "genre": "Rock"}
        ]
        repo.query.query_by_tags = Mock(return_value=mock_songs)
        
        result = repo.query_by_tags(
            mood="Energetic",
            energy="High",
            genre="Rock",
            limit=15
        )
        
        assert result == mock_songs
        repo.query.query_by_tags.assert_called_once_with(
            "Energetic", "High", "Rock", None, 15
        )

    def test_query_by_tags_single(self):
        """测试按单个标签查询"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [{"file_id": "1", "mood": "Happy"}]
        repo.query.query_by_tags = Mock(return_value=mock_songs)
        
        result = repo.query_by_tags(mood="Happy")
        
        assert result == mock_songs
        repo.query.query_by_tags.assert_called_once_with(
            "Happy", None, None, None, 20
        )

    def test_query_by_tags_all_none(self):
        """测试所有参数为 None 的查询"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [{"file_id": "1", "title": "Song"}]
        repo.query.query_by_tags = Mock(return_value=mock_songs)
        
        result = repo.query_by_tags()
        
        assert result == mock_songs

    def test_query_by_tags_no_results(self):
        """测试标签查询无结果"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.query_by_tags = Mock(return_value=[])
        
        result = repo.query_by_tags(mood="Nonexistent")
        
        assert result == []

    def test_get_songs_by_ids(self):
        """测试根据 ID 列表获取歌曲"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [
            {"file_id": "1", "title": "Song 1"},
            {"file_id": "2", "title": "Song 2"}
        ]
        repo.query.get_songs_by_ids = Mock(return_value=mock_songs)
        
        result = repo.get_songs_by_ids(["1", "2"])
        
        assert result == mock_songs
        repo.query.get_songs_by_ids.assert_called_once_with(["1", "2"])

    def test_get_songs_by_ids_empty(self):
        """测试空 ID 列表"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.get_songs_by_ids = Mock(return_value=[])
        
        result = repo.get_songs_by_ids([])
        
        assert result == []

    def test_songs_by_ids_single(self):
        """测试单个 ID 查询"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_songs = [{"file_id": "1", "title": "Song 1"}]
        repo.query.get_songs_by_ids = Mock(return_value=mock_songs)
        
        result = repo.get_songs_by_ids(["1"])
        
        assert result == mock_songs

    def test_get_total_count(self):
        """测试获取歌曲总数"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.get_total_count = Mock(return_value=42)
        
        result = repo.get_total_count()
        
        assert result == 42
        repo.query.get_total_count.assert_called_once()

    def test_get_total_count_zero(self):
        """测试零首歌曲"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.query.get_total_count = Mock(return_value=0)
        
        result = repo.get_total_count()
        
        assert result == 0

    def test_get_distribution(self):
        """测试获取字段分布统计"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_distribution = [
            {"mood": "Energetic", "count": 25},
            {"mood": "Happy", "count": 18}
        ]
        repo.stats.get_distribution = Mock(return_value=mock_distribution)
        
        result = repo.get_distribution("mood")
        
        assert result == mock_distribution
        repo.stats.get_distribution.assert_called_once_with("mood")

    def test_get_distribution_empty(self):
        """测试分布统计为空"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.stats.get_distribution = Mock(return_value=[])
        
        result = repo.get_distribution("nonexistent")
        
        assert result == []

    def test_get_combinations(self):
        """测试获取 Mood + Energy 组合"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_combinations = [
            {"mood": "Energetic", "energy": "High", "count": 15},
            {"mood": "Happy", "energy": "Medium", "count": 10}
        ]
        repo.stats.get_combinations = Mock(return_value=mock_combinations)
        
        result = repo.get_combinations(limit=20)
        
        assert result == mock_combinations
        repo.stats.get_combinations.assert_called_once_with(20)

    def test_get_combinations_default_limit(self):
        """测试组合统计使用默认限制"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_combinations = [{"mood": "Energetic", "energy": "High", "count": 15}]
        repo.stats.get_combinations = Mock(return_value=mock_combinations)
        
        result = repo.get_combinations()
        
        assert result == mock_combinations
        repo.stats.get_combinations.assert_called_once_with(15)

    def test_get_region_genre_distribution(self):
        """测试获取地区流派分布"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_dist = {
            "North America": [
                {"genre": "Rock", "count": 20},
                {"genre": "Pop", "count": 15}
            ],
            "Asia": [
                {"genre": "J-Pop", "count": 18},
                {"genre": "K-Pop", "count": 12}
            ]
        }
        repo.stats.get_region_genre_distribution = Mock(return_value=mock_dist)
        
        result = repo.get_region_genre_distribution()
        
        assert result == mock_dist
        repo.stats.get_region_genre_distribution.assert_called_once()

    def test_get_region_genre_distribution_empty(self):
        """测试地区流派分布为空"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.stats.get_region_genre_distribution = Mock(return_value={})
        
        result = repo.get_region_genre_distribution()
        
        assert result == {}

    def test_get_quality_stats(self):
        """测试获取数据质量统计"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        mock_stats = {
            "total_songs": 100,
            "with_mood": 95,
            "with_energy": 92,
            "with_genre": 88,
            "coverage_pct": 92.0
        }
        repo.stats.get_quality_stats = Mock(return_value=mock_stats)
        
        result = repo.get_quality_stats()
        
        assert result == mock_stats
        repo.stats.get_quality_stats.assert_called_once()

    def test_save_song_tags(self):
        """测试保存歌曲标签"""
        mock_conn = Mock(spec=sqlite3.Connection)
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        repo = SemanticRepository(mock_conn)
        
        tags = {
            "mood": "Energetic",
            "energy": "High",
            "scene": "Workout",
            "region": "North America",
            "subculture": "Mainstream",
            "genre": "Rock"
        }
        
        repo.save_song_tags(
            file_id="file-123",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            tags=tags,
            confidence=0.95,
            model="gpt-4"
        )
        
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT OR REPLACE INTO music_semantic" in sql
        assert params[0] == "file-123"
        assert params[1] == "Test Song"
        assert params[2] == "Test Artist"
        assert params[3] == "Test Album"
        assert params[4] == "Energetic"
        assert params[5] == "High"
        assert params[6] == "Workout"
        assert params[7] == "North America"
        assert params[8] == "Mainstream"
        assert params[9] == "Rock"
        assert params[10] == 0.95
        assert params[11] == "gpt-4"
        
        mock_conn.commit.assert_called_once()

    def test_save_song_tags_partial_tags(self):
        """测试保存部分标签（某些字段为 None）"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        tags = {
            "mood": "Happy",
            "energy": "Medium"
            # 缺少 scene, region, subculture, genre
        }
        
        repo.save_song_tags(
            file_id="file-456",
            title="Another Song",
            artist="Artist",
            album="Album",
            tags=tags,
            confidence=0.88,
            model="gpt-3.5"
        )
        
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        
        assert params[4] == "Happy"
        assert params[5] == "Medium"
        assert params[6] is None
        assert params[7] is None
        assert params[8] is None
        assert params[9] is None

    def test_save_song_tags_all_tags_none(self):
        """测试保存所有标签为 None 的情况"""
        mock_conn = Mock(spec=sqlite3.Connection)
        repo = SemanticRepository(mock_conn)
        
        repo.save_song_tags(
            file_id="file-789",
            title="Empty Tags",
            artist="Artist",
            album="Album",
            tags={},
            confidence=0.0,
            model="none"
        )
        
        call_args = mock_conn.execute.call_args
        params = call_args[0][1]
        
        assert params[4] is None
        assert params[5] is None
        assert params[6] is None
        assert params[7] is None
        assert params[8] is None
        assert params[9] is None
