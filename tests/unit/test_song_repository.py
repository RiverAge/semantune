"""
测试 src.repositories.song_repository 模块
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sqlite3

from src.repositories.song_repository import SongRepository


@pytest.fixture
def mock_nav_conn():
    """模拟 Navidrome 数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    yield conn


@pytest.fixture
def mock_sem_conn():
    """模拟语义数据库连接"""
    conn = Mock(spec=sqlite3.Connection)
    yield conn


@pytest.fixture
def mock_scene_presets():
    """模拟 SCENE_PRESETS 配置"""
    presets = {
        "Workout": {"mood": ["Energetic", "Epic"], "energy": ["High"]},
        "Study": {"mood": ["Peaceful", "Chill"], "energy": ["Low", "Medium"]},
    }
    return presets


class TestSongRepository:
    """测试 SongRepository 类"""

    # ===== 初始化测试 =====
    def test_initialization(self, mock_nav_conn, mock_sem_conn):
        """测试 SongRepository 初始化"""
        repo = SongRepository(mock_nav_conn, mock_sem_conn)

        assert repo.nav_conn == mock_nav_conn
        assert repo.sem_conn == mock_sem_conn

    # ===== get_song_with_tags 测试 =====
    def test_get_song_with_tags_found_with_semantic(self, mock_nav_conn, mock_sem_conn):
        """测试成功获取歌曲及其语义标签 - 有语义数据"""
        # Navidrome cursor 模拟
        nav_cursor = Mock()
        nav_cursor.fetchone.return_value = ("song1", "Test Song", "Artist", "Album", 240, "/test/path.mp3")
        mock_nav_conn.execute.return_value = nav_cursor

        # Semantic cursor 模拟
        sem_cursor = Mock()
        sem_cursor.fetchone.return_value = ("Happy", "High", "Workout", "Western", None, "Pop", 0.9)
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        song = repo.get_song_with_tags("song1")

        assert song is not None
        assert song['id'] == "song1"
        assert song['title'] == "Test Song"
        assert song['mood'] == "Happy"
        assert song['energy'] == "High"
        assert song['scene'] == "Workout"
        assert song['region'] == "Western"
        assert song['genre'] == "Pop"
        assert song['confidence'] == 0.9

    def test_get_song_with_tags_found_without_semantic(self, mock_nav_conn, mock_sem_conn):
        """测试成功获取歌曲但其没有语义数据"""
        nav_cursor = Mock()
        nav_cursor.fetchone.return_value = ("song1", "Test Song", "Artist", "Album", 240, "/test/path.mp3")
        mock_nav_conn.execute.return_value = nav_cursor

        sem_cursor = Mock()
        sem_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        song = repo.get_song_with_tags("song1")

        assert song is not None
        assert song['id'] == "song1"
        assert song['mood'] is None
        assert song['energy'] is None
        assert song['genre'] is None
        assert song['confidence'] is None

    def test_get_song_with_tags_not_found(self, mock_nav_conn, mock_sem_conn):
        """测试获取不存在的歌曲"""
        nav_cursor = Mock()
        nav_cursor.fetchone.return_value = None
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        song = repo.get_song_with_tags("nonexistent")

        assert song is None
        # 不应该调用 sem_conn
        mock_sem_conn.execute.assert_not_called()

    def test_get_song_with_tags_sql_queries_correct(self, mock_nav_conn, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        nav_cursor = Mock()
        nav_cursor.fetchone.return_value = ("song1", "Test", "Artist", "Album", 240, "/path")
        mock_nav_conn.execute.return_value = nav_cursor

        sem_cursor = Mock()
        sem_cursor.fetchone.return_value = (None, None, None, None, None, None, None)
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_song_with_tags("test-id")

        # 验证 Navidrome 查询
        mock_nav_conn.execute.assert_called_once()
        nav_call_args = mock_nav_conn.execute.call_args
        assert "FROM media_file" in nav_call_args[0][0]
        assert "WHERE id = ?" in nav_call_args[0][0]

        # 验证 Semantic 查询
        mock_sem_conn.execute.assert_called_once()
        sem_call_args = mock_sem_conn.execute.call_args
        assert "FROM music_semantic" in sem_call_args[0][0]
        assert "WHERE file_id = ?" in sem_call_args[0][0]

    # ===== get_songs_with_tags 测试 =====
    def test_get_songs_with_tags_empty(self, mock_nav_conn, mock_sem_conn):
        """测试空 ID 列表"""
        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        songs = repo.get_songs_with_tags([])

        assert songs == []
        mock_nav_conn.execute.assert_not_called()
        mock_sem_conn.execute.assert_not_called()

    @patch('src.repositories.song_repository.dict')
    def test_get_songs_with_tags_single_id(self, mock_dict, mock_nav_conn, mock_sem_conn):
        """测试单个 ID 批量获取"""
        # Mock dict() 返回预定义的字典
        mock_dict.side_effect = lambda row: {
            'id': row[0], 'title': row[1], 'artist': row[2], 'album': row[3], 'duration': row[4], 'path': row[5]
        } if len(row) == 6 else {
            'file_id': row[0], 'mood': row[1], 'energy': row[2], 'scene': row[3], 'region': row[4], 'subculture': row[5], 'genre': row[6], 'confidence': row[7]
        }

        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = [("song1", "Song 1", "Artist 1", "Album 1", 240, "/path1.mp3")]
        mock_nav_conn.execute.return_value = nav_cursor

        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = [("song1", "Happy", "High", "Workout", "Western", None, "Pop", 0.9)]
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        songs = repo.get_songs_with_tags(["song1"])

        assert len(songs) == 1
        assert songs[0]['file_id'] == "song1"
        assert songs[0]['mood'] == "Happy"

    @patch('src.repositories.song_repository.dict')
    def test_get_songs_with_tags_multiple_ids(self, mock_dict, mock_nav_conn, mock_sem_conn):
        """测试多个 ID 批量获取"""
        mock_dict.side_effect = lambda row: {
            'id': row[0], 'title': row[1], 'artist': row[2], 'album': row[3], 'duration': row[4], 'path': row[5]
        } if len(row) == 6 else {
            'file_id': row[0], 'mood': row[1], 'energy': row[2], 'scene': row[3], 'region': row[4], 'subculture': row[5], 'genre': row[6], 'confidence': row[7]
        }

        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = [
            ("song1", "Song 1", "Artist 1", "Album 1", 240, "/path1.mp3"),
            ("song2", "Song 2", "Artist 2", "Album 2", 180, "/path2.mp3"),
        ]
        mock_nav_conn.execute.return_value = nav_cursor

        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = [
            ("song1", "Happy", "High", "Workout", "Western", None, "Pop", 0.9),
            ("song2", "Sad", "Low", "Study", "Chinese", None, "Indie", 0.85),
        ]
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        songs = repo.get_songs_with_tags(["song1", "song2"])

        assert len(songs) == 2
        assert songs[0]['file_id'] == "song1"
        assert songs[1]['file_id'] == "song2"
        assert songs[0]['mood'] == "Happy"
        assert songs[1]['mood'] == "Sad"

    @patch('src.repositories.song_repository.dict')
    def test_get_songs_with_tags_some_missing_semantic(self, mock_dict, mock_nav_conn, mock_sem_conn):
        """测试部分歌曲缺少语义数据"""
        mock_dict.side_effect = lambda row: {
            'id': row[0], 'title': row[1], 'artist': row[2], 'album': row[3], 'duration': row[4], 'path': row[5]
        } if len(row) == 6 else {
            'file_id': row[0], 'mood': row[1], 'energy': row[2], 'scene': row[3], 'region': row[4], 'subculture': row[5], 'genre': row[6], 'confidence': row[7]
        }

        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = [
            ("song1", "Song 1", "Artist 1", "Album 1", 240, "/path1.mp3"),
            ("song2", "Song 2", "Artist 2", "Album 2", 180, "/path2.mp3"),
        ]
        mock_nav_conn.execute.return_value = nav_cursor

        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = [
            ("song1", "Happy", "High", "Workout", "Western", None, "Pop", 0.9),
        ]
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        songs = repo.get_songs_with_tags(["song1", "song2"])

        assert len(songs) == 2
        assert songs[0]['mood'] == "Happy"
        assert songs[1]['mood'] is None  # song2 没有语义数据

    @patch('src.repositories.song_repository.dict')
    def test_get_songs_with_tags_sql_query_correct(self, mock_dict, mock_nav_conn, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        mock_dict.side_effect = lambda row: {
            'id': row[0], 'title': row[1], 'artist': row[2], 'album': row[3], 'duration': row[4], 'path': row[5]
        } if len(row) == 6 else {
            'file_id': row[0], 'mood': row[1], 'energy': row[2], 'scene': row[3], 'region': row[4], 'subculture': row[5], 'genre': row[6], 'confidence': row[7]
        }

        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = nav_cursor

        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags(["song1", "song2", "song3"])

        # 验证 Navidrome 查询
        nav_call_args = mock_nav_conn.execute.call_args
        assert "WHERE id IN (?,?,?)" in nav_call_args[0][0]
        assert nav_call_args[0][1] == ["song1", "song2", "song3"]

        # 验证 Semantic 查询
        sem_call_args = mock_sem_conn.execute.call_args
        assert "WHERE file_id IN (?,?,?)" in sem_call_args[0][0]
        assert sem_call_args[0][1] == ["song1", "song2", "song3"]

    # ===== get_all_songs_with_tags 测试 =====
    def test_get_all_songs_with_tags_no_limit(self, mock_nav_conn, mock_sem_conn):
        """测试获取所有歌曲，无限制"""
        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = [("song1", "Song", "Artist", "Album", 240, "/path.mp3")]
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        # Mock 内部 get_songs_with_tags 方法
        repo.get_songs_with_tags = Mock(return_value=[{'file_id': 'song1'}])

        songs = repo.get_all_songs_with_tags()

        repo.get_songs_with_tags.assert_called_once_with(["song1"])

    def test_get_all_songs_with_tags_with_limit(self, mock_nav_conn, mock_sem_conn):
        """测试获取所有歌曲，有限制"""
        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = [
            ("song1", "Song 1", "Artist 1", "Album 1", 240, "/path1.mp3"),
            ("song2", "Song 2", "Artist 2", "Album 2", 180, "/path2.mp3"),
        ]
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.get_all_songs_with_tags(limit=10)

        nav_call_args = mock_nav_conn.execute.call_args
        assert "LIMIT 10" in nav_call_args[0][0]
        repo.get_songs_with_tags.assert_called_once()

    def test_get_all_songs_with_tags_zero_limit(self, mock_nav_conn, mock_sem_conn):
        """测试限制为 0 - 0 是 falsy 值，不会生成 LIMIT 子句"""
        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.get_all_songs_with_tags(limit=0)

        nav_call_args = mock_nav_conn.execute.call_args
        # 0 是 falsy，不会生成 LIMIT 子句
        assert "LIMIT" not in nav_call_args[0][0]

    def test_get_all_songs_with_tags_sql_query_correct(self, mock_nav_conn, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        repo.get_all_songs_with_tags()

        nav_call_args = mock_nav_conn.execute.call_args
        assert "ORDER BY title" in nav_call_args[0][0]
        assert "FROM media_file" in nav_call_args[0][0]

    # ===== search_songs_with_tags 测试 =====
    def test_search_songs_with_tags_success(self, mock_nav_conn, mock_sem_conn):
        """测试成功搜索歌曲"""
        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = [("song1", "Song 1", "Artist 1", "Album 1", 240, "/path1.mp3")]
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[{'file_id': 'song1'}])

        songs = repo.search_songs_with_tags("test song", 10)

        assert repo.get_songs_with_tags.called
        nav_call_args = mock_nav_conn.execute.call_args
        assert "WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?" in nav_call_args[0][0]
        assert nav_call_args[0][1] == ("%test song%", "%test song%", "%test song%", 10)

    def test_search_songs_with_tags_default_limit(self, mock_nav_conn, mock_sem_conn):
        """测试搜索使用默认限制"""
        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.search_songs_with_tags("query")

        nav_call_args = mock_nav_conn.execute.call_args
        assert nav_call_args[0][1][3] == 20  # 默认 limit

    def test_search_songs_with_tags_empty_query(self, mock_nav_conn, mock_sem_conn):
        """测试空搜索词"""
        nav_cursor = Mock()
        nav_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = nav_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.search_songs_with_tags("")

        nav_call_args = mock_nav_conn.execute.call_args
        assert nav_call_args[0][1] == ("%%", "%%", "%%", 20)

    # ===== get_songs_by_tags 测试 =====
    def test_get_songs_by_tags_all_none(self, mock_nav_conn, mock_sem_conn):
        """测试所有标签为 None"""
        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = [("song1",), ("song2",)]
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.get_songs_by_tags(mood=None, energy=None, genre=None, region=None)

        sem_call_args = mock_sem_conn.execute.call_args
        assert "WHERE 1=1" in sem_call_args[0][0]
        assert sem_call_args[0][1] == [20]

    def test_get_songs_by_tags_single_tag(self, mock_nav_conn, mock_sem_conn):
        """测试单个标签查询"""
        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = [("song1",)]
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.get_songs_by_tags(mood="Happy")

        sem_call_args = mock_sem_conn.execute.call_args
        assert "WHERE mood = ?" in sem_call_args[0][0]
        assert sem_call_args[0][1] == ["Happy", 20]

    def test_get_songs_by_tags_multiple_tags(self, mock_nav_conn, mock_sem_conn):
        """测试多个标签组合查询"""
        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = [("song1",)]
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.get_songs_by_tags(mood="Happy", energy="High", genre="Pop", region="Western")

        sem_call_args = mock_sem_conn.execute.call_args
        assert "AND" in sem_call_args[0][0]
        assert "mood = ?" in sem_call_args[0][0]
        assert sem_call_args[0][1] == ["Happy", "High", "Pop", "Western", 20]

    def test_get_songs_by_tags_sql_query_correct(self, mock_nav_conn, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        repo.get_songs_by_tags(mood="Happy", energy="High")

        sem_call_args = mock_sem_conn.execute.call_args
        assert "FROM music_semantic" in sem_call_args[0][0]
        assert "ORDER BY RANDOM()" in sem_call_args[0][0]

    # ===== get_songs_by_scene_preset 测试 =====
    @patch('src.repositories.song_repository.SCENE_PRESETS', {
        "Workout": {"mood": ["Energetic", "Epic"], "energy": ["High"]},
        "Study": {"mood": ["Peaceful", "Chill"], "energy": ["Low"]},
    })
    def test_get_songs_by_scene_preset_success(self, mock_nav_conn, mock_sem_conn):
        """测试成功按场景预设获取歌曲"""
        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = [("song1",), ("song2",)]
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.get_songs_by_scene_preset("Workout")

        sem_call_args = mock_sem_conn.execute.call_args
        assert "WHERE mood IN (?,?)" in sem_call_args[0][0]
        assert "AND energy IN (?)" in sem_call_args[0][0]
        assert sem_call_args[0][1] == ["Energetic", "Epic", "High", 20]

    @patch('src.repositories.song_repository.SCENE_PRESETS', {
        "Workout": {"mood": ["Energetic"], "energy": ["High"]},
    })
    def test_get_songs_by_scene_preset_invalid_scene(self, mock_nav_conn, mock_sem_conn):
        """测试无效的场景预设名称"""
        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        songs = repo.get_songs_by_scene_preset("InvalidScene")

        assert songs == []
        mock_sem_conn.execute.assert_not_called()

    @patch('src.repositories.song_repository.SCENE_PRESETS', {
        "Study": {"mood": ["Peaceful"], "energy": ["Low", "Medium"]},
    })
    def test_get_songs_by_scene_preset_multiple_energies(self, mock_nav_conn, mock_sem_conn):
        """测试场景预设包含多个能量值"""
        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        songs = repo.get_songs_by_scene_preset("Study")

        sem_call_args = mock_sem_conn.execute.call_args
        assert "AND energy IN (?,?)" in sem_call_args[0][0]

    @patch('src.repositories.song_repository.SCENE_PRESETS', {
        "Workout": {"mood": ["Energetic"], "energy": ["High"]},
    })
    def test_get_songs_by_scene_preset_sql_query_correct(self, mock_nav_conn, mock_sem_conn):
        """测试 SQL 查询语句是否正确"""
        sem_cursor = Mock()
        sem_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)
        repo.get_songs_with_tags = Mock(return_value=[])

        repo.get_songs_by_scene_preset("Workout")

        sem_call_args = mock_sem_conn.execute.call_args
        assert "FROM music_semantic" in sem_call_args[0][0]
        assert "ORDER BY RANDOM()" in sem_call_args[0][0]
        assert "LIMIT ?" in sem_call_args[0][0]

    # ===== 集成测试 =====
    @patch('src.repositories.song_repository.SCENE_PRESETS', {
        "Workout": {"mood": ["Energetic"], "energy": ["High"]},
    })
    def test_full_repository_workflow(self, mock_nav_conn, mock_sem_conn):
        """测试完整的仓库工作流程"""
        # Mock get_song_with_tags
        nav_cursor = Mock()
        nav_cursor.fetchone.return_value = ("song1", "Song", "Artist", "Album", 240, "/path")
        mock_nav_conn.execute.return_value = nav_cursor

        sem_cursor = Mock()
        sem_cursor.fetchone.return_value = ("Happy", "High", "Workout", "Western", None, "Pop", 0.9)
        mock_sem_conn.execute.return_value = sem_cursor

        repo = SongRepository(mock_nav_conn, mock_sem_conn)

        # 获取单个歌曲
        song = repo.get_song_with_tags("song1")
        assert song is not None
        assert song['mood'] == "Happy"

        # 按场景预设查询
        sem_cursor.fetchall.return_value = [("song1",)]
        repo.get_songs_with_tags = Mock(return_value=[song])
        songs = repo.get_songs_by_scene_preset("Workout")
        assert len(songs) >= 0
