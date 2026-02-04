"""
测试 src.repositories.user_repository 模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sqlite3

from src.repositories.user_repository import UserRepository


@pytest.fixture
def mock_nav_conn():
    """模拟 Navidrome 数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    yield conn


class TestUserRepository:
    """测试 UserRepository 类"""

    # ===== 初始化测试 =====
    def test_initialization(self, mock_nav_conn):
        """测试 UserRepository 初始化"""
        repo = UserRepository(mock_nav_conn)

        assert repo.nav_conn == mock_nav_conn

    # ===== get_all_users 测试 =====
    def test_get_all_users_success(self, mock_nav_conn):
        """测试成功获取所有用户"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("user1", "Alice"),
            ("user2", "Bob"),
            ("user3", "Charlie")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        users = repo.get_all_users()

        assert len(users) == 3
        assert users[0] == {"id": "user1", "name": "Alice"}
        assert users[1] == {"id": "user2", "name": "Bob"}
        assert users[2] == {"id": "user3", "name": "Charlie"}
        mock_nav_conn.execute.assert_called_once_with("SELECT id, user_name FROM user")

    def test_get_all_users_empty(self, mock_nav_conn):
        """测试获取所有用户，但不存在的用户"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        users = repo.get_all_users()

        assert users == []
        mock_nav_conn.execute.assert_called_once_with("SELECT id, user_name FROM user")

    # ===== get_user_by_id 测试 =====
    def test_get_user_by_id_found(self, mock_nav_conn):
        """测试根据 ID 成功获取用户"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("user1", "Alice")
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        user = repo.get_user_by_id("user1")

        assert user == {"id": "user1", "name": "Alice"}
        mock_nav_conn.execute.assert_called_once_with(
            "SELECT id, user_name FROM user WHERE id = ?",
            ("user1",)
        )

    def test_get_user_by_id_not_found(self, mock_nav_conn):
        """测试根据 ID 获取不存在的用户"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        user = repo.get_user_by_id("nonexistent")

        assert user is None
        mock_nav_conn.execute.assert_called_once_with(
            "SELECT id, user_name FROM user WHERE id = ?",
            ("nonexistent",)
        )

    def test_get_user_by_id_multiple_results(self, mock_nav_conn):
        """测试根据 ID 获取用户（多个结果时的行为）"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("user1", "Alice")
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        user = repo.get_user_by_id("user1")

        # 即使有多个结果，fetchone 也只返回第一个
        assert user == {"id": "user1", "name": "Alice"}

    # ===== get_first_user 测试 =====
    def test_get_first_user_found(self, mock_nav_conn):
        """测试成功获取第一个用户"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("user1", "Alice")
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        user = repo.get_first_user()

        assert user == {"id": "user1", "name": "Alice"}
        mock_nav_conn.execute.assert_called_once_with("SELECT id, user_name FROM user LIMIT 1")

    def test_get_first_user_no_users(self, mock_nav_conn):
        """测试数据库中没有用户时获取第一个用户"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        user = repo.get_first_user()

        assert user is None
        mock_nav_conn.execute.assert_called_once_with("SELECT id, user_name FROM user LIMIT 1")

    def test_get_first_user_returns_dict_structure(self, mock_nav_conn):
        """测试第一个用户返回的字典结构"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("test-id", "Test User")
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        user = repo.get_first_user()

        assert isinstance(user, dict)
        assert "id" in user
        assert "name" in user
        assert user["id"] == "test-id"
        assert user["name"] == "Test User"

    # ===== get_play_history 测试 =====
    def test_get_play_history_success(self, mock_nav_conn):
        """测试成功获取播放历史"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, "2024-01-01T12:00:00Z"),
            ("song2", 5, False, "2024-01-02T15:30:00Z"),
            ("song3", 20, True, "2024-01-03T10:00:00Z")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert len(history) == 3
        assert history["song1"]["play_count"] == 10
        assert history["song1"]["starred"] is True
        assert history["song1"]["play_date"] > 0

        assert history["song2"]["play_count"] == 5
        assert history["song2"]["starred"] is False

        assert history["song3"]["play_count"] == 20
        assert history["song3"]["starred"] is True

    def test_get_play_history_empty(self, mock_nav_conn):
        """测试获取空的播放历史"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history == {}

    def test_get_play_history_none_play_count(self, mock_nav_conn):
        """测试播放次数为 None 的情况"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", None, True, "2024-01-01T12:00:00Z")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["play_count"] == 0

    def test_get_play_history_none_play_date(self, mock_nav_conn):
        """测试播放日期为 None 的情况"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, None)
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["play_date"] == 0

    def test_get_play_history_invalid_iso_format(self, mock_nav_conn):
        """测试无效的 ISO 8601 格式，尝试解析为 float"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, "invalid-date-string")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        # 当 datetime.fromisoformat 失败时，尝试 float 解析，也会失败
        assert history["song1"]["play_date"] == 0

    def test_get_play_history_float_timestamp_string(self, mock_nav_conn):
        """测试播放日期为 float 时间戳字符串"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, "1704108000.0")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["play_date"] == 1704108000.0

    def test_get_play_history_value_error_on_float_parse(self, mock_nav_conn):
        """测试 float 解析时 ValueError"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, "not-a-number")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["play_date"] == 0

    def test_get_play_history_type_error_on_float_parse(self, mock_nav_conn):
        """测试 float 解析时 TypeError (line 104-106)"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, {})  # 传入字典对象，float() 会抛出 TypeError
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["play_date"] == 0

    def test_get_play_history_none_string_object(self, mock_nav_conn):
        """测试 ISO 解析时 TypeError (对 None 调用 replace 会引发 TypeError)"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, None)  # 已有专门测试 None 的情况
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["play_date"] == 0

    def test_get_play_history_with_iso_without_z(self, mock_nav_conn):
        """测试不带 Z 的 ISO 8601 格式"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, True, "2024-01-01T12:00:00+00:00")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["play_date"] > 0

    def test_get_play_history_zero_starred(self, mock_nav_conn):
        """测试 starred 为 0 的情况"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 10, 0, "2024-01-01T12:00:00Z")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        history = repo.get_play_history("user1")

        assert history["song1"]["starred"] is False

    def test_get_play_history_sql_query_correct(self, mock_nav_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        repo.get_play_history("user123")

        expected_query = """
            SELECT
                item_id,
                play_count,
                starred,
                play_date
            FROM annotation
            WHERE user_id = ? AND item_type = 'media_file'
        """
        mock_nav_conn.execute.assert_called_once()
        call_args = mock_nav_conn.execute.call_args
        assert "item_type = 'media_file'" in call_args[0][0]
        assert "user_id = ?" in call_args[0][0]
        assert call_args[0][1] == ("user123",)

    # ===== get_playlist_songs 测试 =====
    def test_get_playlist_songs_success(self, mock_nav_conn):
        """测试成功获取歌单歌曲"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("song1", 2),
            ("song2", 1),
            ("song3", 3)
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        playlist_songs = repo.get_playlist_songs("user1")

        assert len(playlist_songs) == 3
        assert playlist_songs["song1"] == 2
        assert playlist_songs["song2"] == 1
        assert playlist_songs["song3"] == 3

    def test_get_playlist_songs_empty(self, mock_nav_conn):
        """测试获取空歌单"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        playlist_songs = repo.get_playlist_songs("user1")

        assert playlist_songs == {}

    def test_get_playlist_songs_sql_query_correct(self, mock_nav_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        repo.get_playlist_songs("user123")

        mock_nav_conn.execute.assert_called_once()
        call_args = mock_nav_conn.execute.call_args
        assert "GROUP BY" in call_args[0][0]
        assert "COUNT(*) as playlist_count" in call_args[0][0]
        assert "owner_id = ?" in call_args[0][0]
        assert call_args[0][1] == ("user123",)

    def test_get_playlist_songs_keys_are_strings(self, mock_nav_conn):
        """测试返回的键是字符串类型"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (123, 1),
            (456, 2)
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = UserRepository(mock_nav_conn)
        playlist_songs = repo.get_playlist_songs("user1")

        assert isinstance(list(playlist_songs.keys())[0], str)
        assert "123" in playlist_songs
        assert "456" in playlist_songs

    # ===== get_user_songs 测试 =====
    def test_get_user_songs_from_both_sources(self, mock_nav_conn):
        """测试从播放历史和歌单获取歌曲"""
        repo = UserRepository(mock_nav_conn)
        repo.get_play_history = Mock(return_value={"song1": {}, "song2": {}})
        repo.get_playlist_songs = Mock(return_value={"song2": 1, "song3": 1})

        songs = repo.get_user_songs("user1")

        assert set(songs) == {"song1", "song2", "song3"}

    def test_get_user_songs_only_history(self, mock_nav_conn):
        """测试仅从播放历史获取歌曲"""
        repo = UserRepository(mock_nav_conn)
        repo.get_play_history = Mock(return_value={"song1": {}, "song2": {}})
        repo.get_playlist_songs = Mock(return_value={})

        songs = repo.get_user_songs("user1")

        assert set(songs) == {"song1", "song2"}

    def test_get_user_songs_only_playlist(self, mock_nav_conn):
        """测试仅从歌单获取歌曲"""
        repo = UserRepository(mock_nav_conn)
        repo.get_play_history = Mock(return_value={})
        repo.get_playlist_songs = Mock(return_value={"song1": 1, "song2": 2})

        songs = repo.get_user_songs("user1")

        assert set(songs) == {"song1", "song2"}

    def test_get_user_songs_empty(self, mock_nav_conn):
        """测试获取用户歌曲为空"""
        repo = UserRepository(mock_nav_conn)
        repo.get_play_history = Mock(return_value={})
        repo.get_playlist_songs = Mock(return_value={})

        songs = repo.get_user_songs("user1")

        assert songs == []

    def test_get_user_songs_duplicates_removed(self, mock_nav_conn):
        """测试重复歌曲被去重"""
        repo = UserRepository(mock_nav_conn)
        repo.get_play_history = Mock(return_value={"song1": {}, "song2": {}, "song3": {}})
        repo.get_playlist_songs = Mock(return_value={"song2": 1, "song3": 1, "song4": 1})

        songs = repo.get_user_songs("user1")

        assert set(songs) == {"song1", "song2", "song3", "song4"}
        assert len(songs) == len(set(songs))  # 无重复

    def test_get_user_songs_returns_list(self, mock_nav_conn):
        """测试返回类型是列表"""
        repo = UserRepository(mock_nav_conn)
        repo.get_play_history = Mock(return_value={"song1": {}})
        repo.get_playlist_songs = Mock(return_value={"song2": 1})

        songs = repo.get_user_songs("user1")

        assert isinstance(songs, list)

    # ===== 集成测试 =====
    def test_full_user_workflow(self, mock_nav_conn):
        """测试完整的用户数据获取流程"""
        # 设置模拟数据
        mock_cursor_users = Mock()
        mock_cursor_users.fetchone.return_value = ("user1", "Alice")
        mock_cursor_users.fetchall.return_value = [("user1", "Alice")]

        mock_cursor_history = Mock()
        mock_cursor_history.fetchall.return_value = [
            ("song1", 5, True, "2024-01-01T12:00:00Z"),
            ("song2", 3, False, None)
        ]

        mock_cursor_playlist = Mock()
        mock_cursor_playlist.fetchall.return_value = [
            ("song2", 1),
            ("song3", 2)
        ]

        def execute_side_effect(query, params=None):
            if "user_name FROM user" in query and "WHERE id" in query:
                return mock_cursor_users
            elif "item_type = 'media_file'" in query:
                return mock_cursor_history
            elif "playlist_tracks" in query:
                return mock_cursor_playlist
            return Mock()

        mock_nav_conn.execute.side_effect = execute_side_effect

        repo = UserRepository(mock_nav_conn)

        # 获取用户信息
        user = repo.get_user_by_id("user1")
        assert user == {"id": "user1", "name": "Alice"}

        # 获取播放历史
        history = repo.get_play_history("user1")
        assert len(history) == 2

        # 获取歌单歌曲
        playlist = repo.get_playlist_songs("user1")
        assert set(playlist.keys()) == {"song2", "song3"}

        # 获取所有用户歌曲
        all_songs = repo.get_user_songs("user1")
        assert set(all_songs) == {"song1", "song2", "song3"}
