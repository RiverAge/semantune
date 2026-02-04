"""
测试 src.repositories.semantic_query 模块
"""

import pytest
from unittest.mock import Mock, MagicMock
import sqlite3

from src.repositories.semantic_query import SemanticQueryRepository


@pytest.fixture
def mock_sem_conn():
    """模拟语义数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    yield conn


class TestSemanticQueryRepository:
    """测试 SemanticQueryRepository 类"""

    # ===== 初始化测试 =====
    def test_initialization(self, mock_sem_conn):
        """测试 SemanticQueryRepository 初始化"""
        repo = SemanticQueryRepository(mock_sem_conn)

        assert repo.sem_conn == mock_sem_conn

    # ===== get_song_tags 测试 =====
    def test_get_song_tags_found(self, mock_sem_conn):
        """测试成功获取歌曲标签"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("Happy", "High", "Pop", "Western", "Workout", None)
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        tags = repo.get_song_tags("song1")

        assert tags == {
            'mood': "Happy",
            'energy': "High",
            'genre': "Pop",
            'region': "Western",
            'scene': "Workout",
            'subculture': None
        }

    def test_get_song_tags_not_found(self, mock_sem_conn):
        """测试获取不存在的歌曲标签"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        tags = repo.get_song_tags("nonexistent")

        assert tags is None  # 此测试触发 line 47

    def test_get_song_tags_sql_query_correct(self, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        repo.get_song_tags("song123")

        mock_sem_conn.execute.assert_called_once()
        call_args = mock_sem_conn.execute.call_args
        assert "WHERE file_id = ?" in call_args[0][0]
        assert call_args[0][1] == ("song123",)

    # ===== get_all_songs 测试 =====
    def test_get_all_songs_success(self, mock_sem_conn):
        """测试成功获取所有歌曲"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            MagicMock(keys=lambda: ['file_id', 'title', 'artist', 'album'], __getitem__=lambda self, key: {
                'file_id': "song1", 'title': "Song 1", 'artist': "Artist 1", 'album': "Album 1"
            }.get(key)),
            MagicMock(keys=lambda: ['file_id', 'title', 'artist', 'album'], __getitem__=lambda self, key: {
                'file_id': "song2", 'title': "Song 2", 'artist': "Artist 2", 'album': "Album 2"
            }.get(key))
        ]
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.get_all_songs()

        assert len(songs) == 2

    def test_get_all_songs_empty(self, mock_sem_conn):
        """测试获取所有歌曲为空"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.get_all_songs()

        assert songs == []

    # ===== get_song_by_id 测试 =====
    def test_get_song_by_id_found(self, mock_sem_conn):
        """测试根据 ID 成功获取歌曲 - 触发 lines 73-80"""
        mock_cursor = Mock()
        # 使用 Mock 对象模拟 sqlite3.Row 的行为
        mock_row = Mock()
        # dict() 会遍历 row 的 keys() 和 __getitem__
        mock_row.keys.return_value = ['file_id', 'title', 'artist', 'album', 'mood', 'energy', 'scene', 'region', 'subculture', 'genre', 'confidence']
        mock_row.__getitem__ = lambda self, key: {
            'file_id': "song1",
            'title': "Test Song",
            'artist': "Artist",
            'album': "Album",
            'mood': "Happy",
            'energy': "High",
            'scene': None,
            'region': "Western",
            'subculture': None,
            'genre': "Pop",
            'confidence': 0.9
        }.get(key)
        mock_cursor.fetchone.return_value = mock_row
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        song = repo.get_song_by_id("song1")

        assert song is not None
        assert song['file_id'] == "song1"
        mock_sem_conn.execute.assert_called_once()

    def test_get_song_by_id_not_found(self, mock_sem_conn):
        """测试根据 ID 获取不存在的歌曲"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        song = repo.get_song_by_id("nonexistent")

        assert song is None

    def test_get_song_by_id_sql_query_correct(self, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        repo.get_song_by_id("song123")

        mock_sem_conn.execute.assert_called_once()
        call_args = mock_sem_conn.execute.call_args
        assert "WHERE file_id = ?" in call_args[0][0]
        assert call_args[0][1] == ("song123",)

    # ===== query_by_mood 测试 =====
    def test_query_by_mood_success(self, mock_sem_conn):
        """测试按情绪查询成功"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            MagicMock(keys=lambda: ['title'], __getitem__=lambda self, key: {'title': "Song 1"}.get(key))
        ]
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_mood("Happy", 10)

        assert len(songs) >= 0
        mock_sem_conn.execute.assert_called_once()

    def test_query_by_mood_default_limit(self, mock_sem_conn):
        """测试按情绪查询使用默认限制"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_mood("Happy")

        assert songs == []
        mock_sem_conn.execute.assert_called_once()
        call_args = mock_sem_conn.execute.call_args
        # limit 参数应该是 20
        assert call_args[0][1] == ("Happy", 20)

    def test_query_by_mood_custom_limit(self, mock_sem_conn):
        """测试按情绪查询使用自定义限制"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_mood("Happy", 50)

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert call_args[0][1] == ("Happy", 50)

    def test_query_by_mood_sql_query_correct(self, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        repo.query_by_mood("Epic", 15)

        call_args = mock_sem_conn.execute.call_args
        assert "WHERE mood = ?" in call_args[0][0]
        assert "ORDER BY confidence DESC" in call_args[0][0]
        assert "LIMIT ?" in call_args[0][0]
        assert call_args[0][1] == ("Epic", 15)

    # ===== query_by_tags 测试 =====
    def test_query_by_tags_all_none(self, mock_sem_conn):
        """测试所有标签为 None 时查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_tags(mood=None, energy=None, genre=None, region=None)

        assert songs == []
        mock_sem_conn.execute.assert_called_once()
        call_args = mock_sem_conn.execute.call_args
        # where_clause 应该是 "1=1"
        assert "WHERE 1=1" in call_args[0][0]
        assert call_args[0][1] == [20]  # 只有 limit 参数

    def test_query_by_tags_single_tag(self, mock_sem_conn):
        """测试单个标签查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_tags(mood="Happy")

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert "WHERE mood = ?" in call_args[0][0]
        assert call_args[0][1] == ["Happy", 20]

    def test_query_by_tags_multiple_tags(self, mock_sem_conn):
        """测试多个标签组合查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_tags(mood="Happy", energy="High", genre="Pop", region="Western")

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert "AND" in call_args[0][0]
        assert "mood = ?" in call_args[0][0]
        assert "energy = ?" in call_args[0][0]
        assert "genre = ?" in call_args[0][0]
        assert "region = ?" in call_args[0][0]  # 触发 line 136-137
        assert call_args[0][1] == ["Happy", "High", "Pop", "Western", 20]

    def test_query_by_tags_with_region_only(self, mock_sem_conn):
        """测试只有 region 标签的查询 - 触发 lines 136-137"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_tags(region="Western")

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert "WHERE region = ?" in call_args[0][0]
        assert call_args[0][1] == ["Western", 20]

    def test_query_by_tags_partial_tags(self, mock_sem_conn):
        """测试部分标签查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_tags(mood="Happy", genre="Rock")

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert "mood = ?" in call_args[0][0]
        assert "genre = ?" in call_args[0][0]
        assert call_args[0][1] == ["Happy", "Rock", 20]

    def test_query_by_tags_custom_limit(self, mock_sem_conn):
        """测试自定义限制"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.query_by_tags(mood="Happy", limit=50)

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert call_args[0][1] == ["Happy", 50]

    def test_query_by_tags_sql_query_correct(self, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        repo.query_by_tags(mood="Happy", energy="High")

        call_args = mock_sem_conn.execute.call_args
        assert "FROM music_semantic" in call_args[0][0]
        assert "ORDER BY RANDOM()" in call_args[0][0]
        assert "LIMIT ?" in call_args[0][0]

    # ===== get_songs_by_ids 测试 =====
    def test_get_songs_by_ids_empty(self, mock_sem_conn):
        """测试空 ID 列表返回空 - 触发 line 162"""
        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.get_songs_by_ids([])

        assert songs == []
        # 空列表不应该调用 execute
        mock_sem_conn.execute.assert_not_called()

    def test_get_songs_by_ids_single_id(self, mock_sem_conn):
        """测试单个 ID 查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.get_songs_by_ids(["song1"])

        assert songs == []
        mock_sem_conn.execute.assert_called_once()
        call_args = mock_sem_conn.execute.call_args
        assert "WHERE file_id IN (?)" in call_args[0][0]
        assert call_args[0][1] == ["song1"]

    def test_get_songs_by_ids_multiple_ids(self, mock_sem_conn):
        """测试多个 ID 查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.get_songs_by_ids(["song1", "song2", "song3"])

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert "WHERE file_id IN (?,?,?)" in call_args[0][0]
        assert call_args[0][1] == ["song1", "song2", "song3"]

    def test_get_songs_by_ids_many_ids(self, mock_sem_conn):
        """测试大量 ID 查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        ids = [f"song{i}" for i in range(100)]
        expected_placeholders = ','.join(['?'] * 100)

        repo = SemanticQueryRepository(mock_sem_conn)
        songs = repo.get_songs_by_ids(ids)

        assert songs == []
        call_args = mock_sem_conn.execute.call_args
        assert f"WHERE file_id IN ({expected_placeholders})" in call_args[0][0]
        assert call_args[0][1] == ids

    def test_get_songs_by_ids_sql_query_correct(self, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        repo.get_songs_by_ids(["song1", "song2"])

        call_args = mock_sem_conn.execute.call_args
        assert "SELECT file_id, title, artist" in call_args[0][0]
        assert "FROM music_semantic" in call_args[0][0]

    # ===== get_total_count 测试 =====
    def test_get_total_count(self, mock_sem_conn):
        """测试获取歌曲总数"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [100]
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        count = repo.get_total_count()

        assert count == 100
        mock_sem_conn.execute.assert_called_once_with("SELECT COUNT(*) FROM music_semantic")

    def test_get_total_count_zero(self, mock_sem_conn):
        """测试歌曲总数为零"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [0]
        mock_sem_conn.execute.return_value = mock_cursor

        repo = SemanticQueryRepository(mock_sem_conn)
        count = repo.get_total_count()

        assert count == 0

    # ===== 集成测试 =====
    def test_full_query_workflow(self, mock_sem_conn):
        """测试完整查询流程"""
        # 设置 mock 数据
        def execute_side_effect(query, params=None):
            mock_cursor = Mock()
            if "file_id = ?" in query and "SELECT COUNT" not in query and "WHERE file_id IN" not in query:
                # get_song_tags or get_song_by_id
                mock_cursor.fetchone.return_value = ("Happy", "High", "Pop", "Western", "Workout", None)
            elif "SELECT COUNT" in query:
                mock_cursor.fetchone.return_value = [50]
            else:
                mock_cursor.fetchall.return_value = []
            return mock_cursor

        mock_sem_conn.execute.side_effect = execute_side_effect

        repo = SemanticQueryRepository(mock_sem_conn)

        # 获取歌曲标签
        tags = repo.get_song_tags("song1")
        assert tags is not None

        # 获取总数
        count = repo.get_total_count()
        assert count == 50

        # 按情绪查询
        songs = repo.query_by_mood("Happy")
        assert isinstance(songs, list)
