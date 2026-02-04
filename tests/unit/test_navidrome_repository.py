"""
测试 src.repositories.navidrome_repository 模块
"""

import pytest
from unittest.mock import Mock, MagicMock
import sqlite3

from src.repositories.navidrome_repository import NavidromeRepository


@pytest.fixture
def mock_nav_conn():
    """模拟 Navidrome 数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    yield conn


class TestNavidromeRepository:
    """测试 NavidromeRepository 类"""

    # ===== 初始化测试 =====
    def test_initialization(self, mock_nav_conn):
        """测试 NavidromeRepository 初始化"""
        repo = NavidromeRepository(mock_nav_conn)

        assert repo.nav_conn == mock_nav_conn

    # ===== get_all_songs 测试 =====
    def test_get_all_songs_success(self, mock_nav_conn):
        """测试成功获取所有歌曲，覆盖 lines 28-33"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            MagicMock(
                keys=lambda: ['id', 'title', 'artist', 'album', 'duration', 'path'],
                __getitem__=lambda self, key: {
                    'id': 'song1', 'title': 'Song 1', 'artist': 'Artist 1',
                    'album': 'Album 1', 'duration': 180, 'path': '/path/to/song1.mp3'
                }.get(key)
            )
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.get_all_songs()

        assert len(songs) == 1
        mock_nav_conn.execute.assert_called_once_with("""
            SELECT id, title, artist, album, duration, path
            FROM media_file
            ORDER BY title
        """)

    def test_get_all_songs_empty(self, mock_nav_conn):
        """测试获取所有歌曲为空"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.get_all_songs()

        assert songs == []

    # ===== get_song_by_id 测试 =====
    def test_get_song_by_id_found(self, mock_nav_conn):
        """测试根据 ID 成功获取歌曲 - 覆盖 lines 45-51"""
        mock_cursor = Mock()
        mock_row = MagicMock(
            keys=lambda: ['id', 'title', 'artist', 'album', 'duration', 'path'],
            __getitem__=lambda self, key: {
                'id': 'song1', 'title': 'Test Song', 'artist': 'Test Artist',
                'album': 'Test Album', 'duration': 240, 'path': '/test/path.mp3'
            }.get(key)
        )
        mock_cursor.fetchone.return_value = mock_row
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        song = repo.get_song_by_id("song1")

        assert song is not None
        assert song['id'] == "song1"
        mock_nav_conn.execute.assert_called_once()

    def test_get_song_by_id_not_found(self, mock_nav_conn):
        """测试根据 ID 获取不存在的歌曲"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        song = repo.get_song_by_id("nonexistent")

        assert song is None

    def test_get_song_by_id_sql_query_correct(self, mock_nav_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        repo.get_song_by_id("test-song-id")

        call_args = mock_nav_conn.execute.call_args
        assert "WHERE id = ?" in call_args[0][0]
        assert call_args[0][1] == ("test-song-id",)

    # ===== get_songs_by_ids 测试 =====
    def test_get_songs_by_ids_empty(self, mock_nav_conn):
        """测试空 ID 列表返回空 - 覆盖 line 63-64"""
        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.get_songs_by_ids([])

        assert songs == []
        mock_nav_conn.execute.assert_not_called()

    def test_get_songs_by_ids_single_id(self, mock_nav_conn):
        """测试单个 ID 查询 - 覆盖 lines 66-73"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.get_songs_by_ids(["song1"])

        assert songs == []
        call_args = mock_nav_conn.execute.call_args
        assert "WHERE id IN (?)" in call_args[0][0]
        assert call_args[0][1] == ["song1"]

    def test_get_songs_by_ids_multiple_ids(self, mock_nav_conn):
        """测试多个 ID 查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.get_songs_by_ids(["song1", "song2", "song3"])

        assert songs == []
        call_args = mock_nav_conn.execute.call_args
        assert "WHERE id IN (?,?,?)" in call_args[0][0]
        assert call_args[0][1] == ["song1", "song2", "song3"]

    def test_get_songs_by_ids_many(self, mock_nav_conn):
        """测试大量 ID 查询"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        ids = [f"song{i}" for i in range(50)]
        expected_placeholders = ','.join(['?'] * 50)

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.get_songs_by_ids(ids)

        assert songs == []
        call_args = mock_nav_conn.execute.call_args
        assert f"WHERE id IN ({expected_placeholders})" in call_args[0][0]
        assert call_args[0][1] == ids

    def test_get_songs_by_ids_sql_query_correct(self, mock_nav_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        repo.get_songs_by_ids(["song1"])

        call_args = mock_nav_conn.execute.call_args
        assert "SELECT id, title, artist, album, duration, path" in call_args[0][0]
        assert "FROM media_file" in call_args[0][0]

    # ===== search_songs 测试 =====
    def test_search_songs_success(self, mock_nav_conn):
        """测试成功搜索歌曲 - 覆盖 lines 86-94"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.search_songs("test song")

        assert songs == []
        call_args = mock_nav_conn.execute.call_args
        assert "WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?" in call_args[0][0]
        assert call_args[0][1] == ("%test song%", "%test song%", "%test song%", 20)

    def test_search_songs_default_limit(self, mock_nav_conn):
        """测试搜索使用默认限制"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.search_songs("query")

        assert songs == []
        call_args = mock_nav_conn.execute.call_args
        assert call_args[0][1][3] == 20  # 默认 limit 是 20

    def test_search_songs_custom_limit(self, mock_nav_conn):
        """测试搜索使用自定义限制"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.search_songs("query", limit=50)

        assert songs == []
        call_args = mock_nav_conn.execute.call_args
        assert call_args[0][1][3] == 50

    def test_search_songs_empty_query(self, mock_nav_conn):
        """测试空搜索词"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        songs = repo.search_songs("")

        assert songs == []
        call_args = mock_nav_conn.execute.call_args
        # 空搜索词会匹配所有歌曲（LIKE %%）
        assert call_args[0][1] == ("%%", "%%", "%%", 20)

    def test_search_songs_sql_query_correct(self, mock_nav_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        repo.search_songs("Bohemian", limit=10)

        call_args = mock_nav_conn.execute.call_args
        assert "ORDER BY title" in call_args[0][0]
        assert "LIMIT ?" in call_args[0][0]

    # ===== get_total_count 测试 =====
    def test_get_total_count(self, mock_nav_conn):
        """测试获取歌曲总数"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [100]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        count = repo.get_total_count()

        assert count == 100
        mock_nav_conn.execute.assert_called_once_with("SELECT COUNT(*) FROM media_file")

    def test_get_total_count_zero(self, mock_nav_conn):
        """测试歌曲总数为零"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [0]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        count = repo.get_total_count()

        assert count == 0

    # ===== get_artists 测试 =====
    def test_get_artists_success(self, mock_nav_conn):
        """测试成功获取所有艺术家 - 覆盖 lines 114-120"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("Artist 1",),
            ("Artist 2",),
            ("Artist 3",)
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        artists = repo.get_artists()

        assert len(artists) == 3
        assert artists[0] == {"name": "Artist 1"}
        assert artists[1] == {"name": "Artist 2"}
        assert artists[2] == {"name": "Artist 3"}
        mock_nav_conn.execute.assert_called_once_with("""
            SELECT DISTINCT artist
            FROM media_file
            WHERE artist IS NOT NULL AND artist != ''
            ORDER BY artist
        """)

    def test_get_artists_empty(self, mock_nav_conn):
        """测试获取艺术家为空"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        artists = repo.get_artists()

        assert artists == []

    def test_get_artists_sql_query_correct(self, mock_nav_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        repo.get_artists()

        call_args = mock_nav_conn.execute.call_args
        assert "SELECT DISTINCT artist" in call_args[0][0]
        assert "WHERE artist IS NOT NULL AND artist != ''" in call_args[0][0]
        assert "ORDER BY artist" in call_args[0][0]

    # ===== get_albums 测试 =====
    def test_get_albums_success(self, mock_nav_conn):
        """测试成功获取所有专辑 - 覆盖 lines 129-135"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("Album 1", "Artist 1"),
            ("Album 2", "Artist 2"),
            ("Album 3", "Artist 3")
        ]
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        albums = repo.get_albums()

        assert len(albums) == 3
        assert albums[0] == {"name": "Album 1", "artist": "Artist 1"}
        assert albums[1] == {"name": "Album 2", "artist": "Artist 2"}
        assert albums[2] == {"name": "Album 3", "artist": "Artist 3"}
        mock_nav_conn.execute.assert_called_once_with("""
            SELECT DISTINCT album, artist
            FROM media_file
            WHERE album IS NOT NULL AND album != ''
            ORDER BY album
        """)

    def test_get_albums_empty(self, mock_nav_conn):
        """测试获取专辑为空"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        albums = repo.get_albums()

        assert albums == []

    def test_get_albums_sql_query_correct(self, mock_nav_conn):
        """测试 SQL 查询语句是否正确"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_cursor

        repo = NavidromeRepository(mock_nav_conn)
        repo.get_albums()

        call_args = mock_nav_conn.execute.call_args
        assert "SELECT DISTINCT album, artist" in call_args[0][0]
        assert "WHERE album IS NOT NULL AND album != ''" in call_args[0][0]
        assert "ORDER BY album" in call_args[0][0]

    # ===== 集成测试 =====
    def test_full_repository_workflow(self, mock_nav_conn):
        """测试完整的仓库工作流程"""
        # 设置 mock 数据
        def execute_side_effect(query, params=None):
            mock_cursor = Mock()
            if "SELECT COUNT" in query:
                mock_cursor.fetchone.return_value = [50]
            elif "SELECT DISTINCT artist" in query:
                mock_cursor.fetchall.return_value = [("Artist 1",), ("Artist 2",)]
            elif "SELECT DISTINCT album" in query:
                mock_cursor.fetchall.return_value = [("Album 1", "Artist 1")]
            else:
                mock_cursor.fetchall.return_value = []
            return mock_cursor

        mock_nav_conn.execute.side_effect = execute_side_effect

        repo = NavidromeRepository(mock_nav_conn)

        # 获取总数
        count = repo.get_total_count()
        assert count == 50

        # 获取所有歌曲
        songs = repo.get_all_songs()
        assert isinstance(songs, list)

        # 搜索歌曲
        results = repo.search_songs("test")
        assert isinstance(results, list)

        # 获取艺术家
        artists = repo.get_artists()
        assert len(artists) == 2

        # 获取专辑
        albums = repo.get_albums()
        assert len(albums) == 1
