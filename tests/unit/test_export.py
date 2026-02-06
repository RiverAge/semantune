"""
单元测试 - 数据导出工具
测试覆盖率目标: 100%
"""

import pytest
import csv
import json
import os
from unittest.mock import Mock, patch, call, MagicMock
from io import StringIO
from datetime import datetime

from src.utils.export import (
    get_user_id,
    export_play_history,
    export_playlists,
    export_statistics,
    main
)


class TestGetUserId:
    """测试获取用户ID功能"""

    def test_get_user_id_single_user(self):
        """测试当只有一个用户时直接返回"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [('user_001', 'Alice')]
        mock_conn.execute.return_value = mock_cursor

        user_id, user_name = get_user_id(mock_conn)

        mock_conn.execute.assert_called_once_with("SELECT id, user_name FROM user")
        assert user_id == 'user_001'
        assert user_name == 'Alice'

    @patch('builtins.input')
    def test_get_user_id_multiple_users(self, mock_input):
        """测试当有多个用户时提示选择"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('user_001', 'Alice'),
            ('user_002', 'Bob'),
            ('user_003', 'Charlie')
        ]
        mock_conn.execute.return_value = mock_cursor

        mock_input.return_value = '2'

        user_id, user_name = get_user_id(mock_conn)

        mock_conn.execute.assert_called_once_with("SELECT id, user_name FROM user")
        mock_input.assert_called_once_with("\n请选择用户 (输入序号): ")
        assert user_id == 'user_002'
        assert user_name == 'Bob'

    @patch('builtins.input')
    def test_get_user_id_first_user(self, mock_input):
        """测试选择第一个用户（索引0）"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('user_001', 'Alice'),
            ('user_002', 'Bob')
        ]
        mock_conn.execute.return_value = mock_cursor

        mock_input.return_value = '1'

        user_id, user_name = get_user_id(mock_conn)

        assert user_id == 'user_001'
        assert user_name == 'Alice'

    @patch('builtins.input')
    def test_get_user_id_last_user(self, mock_input):
        """测试选择最后一个用户"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ('user_001', 'Alice'),
            ('user_002', 'Bob'),
            ('user_003', 'Charlie')
        ]
        mock_conn.execute.return_value = mock_cursor

        mock_input.return_value = '3'

        user_id, user_name = get_user_id(mock_conn)

        assert user_id == 'user_003'
        assert user_name == 'Charlie'


class TestExportPlayHistory:
    """测试导出播放历史功能"""

    def test_export_play_history_empty(self, tmp_path):
        """测试导出空的播放历史"""
        mock_nav_conn = Mock()
        mock_nav_cursor = Mock()
        mock_nav_cursor.fetchall.return_value = []
        mock_nav_conn.execute.return_value = mock_nav_cursor

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "play_history.csv"
        count = export_play_history(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert count == 0

        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == [
                'song_id', 'title', 'artist', 'album', 'year', 'original_genre',
                'play_count', 'starred', 'play_date',
                'mood', 'energy', 'genre', 'style', 'scene', 'region', 'culture', 'language'
            ]
            assert sum(1 for _ in reader) == 0

    def test_export_play_history_with_data(self, tmp_path):
        """测试导出有数据的播放历史"""
        mock_nav_conn = Mock()
        mock_nav_cursor = Mock()
        mock_nav_cursor.fetchall.return_value = [
            ('song_001', 10, True, '2024-01-15', 'Song 1', 'Artist 1', 'Album 1', 2020, 'Rock'),
            ('song_002', 5, False, '2024-01-20', 'Song 2', 'Artist 2', 'Album 2', 2021, 'Pop')
        ]
        mock_nav_conn.execute.return_value = mock_nav_cursor

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.side_effect = [
            ('Energetic', 'High', 'Rock', 'Alternative', 'Driving', 'US', 'Western', 'English'),
            ('Relaxed', 'Low', 'Pop', 'Ballad', 'Work', 'UK', 'English', 'English')
        ]
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "play_history.csv"
        count = export_play_history(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert count == 2

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)

            assert len(rows) == 2
            assert rows[0] == [
                'song_001', 'Song 1', 'Artist 1', 'Album 1', '2020', 'Rock',
                '10', 'Yes', '2024-01-15',
                'Energetic', 'High', 'Rock', 'Alternative', 'Driving', 'US', 'Western', 'English'
            ]
            assert rows[1] == [
                'song_002', 'Song 2', 'Artist 2', 'Album 2', '2021', 'Pop',
                '5', 'No', '2024-01-20',
                'Relaxed', 'Low', 'Pop', 'Ballad', 'Work', 'UK', 'English', 'English'
            ]

    def test_export_play_history_no_semantic_data(self, tmp_path):
        """测试歌曲没有语义标签数据时使用N/A"""
        mock_nav_conn = Mock()
        mock_nav_cursor = Mock()
        mock_nav_cursor.fetchall.return_value = [
            ('song_001', 1, False, '2024-01-01', 'Song', 'Artist', 'Album', 2020, 'Pop')
        ]
        mock_nav_conn.execute.return_value = mock_nav_cursor

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "play_history.csv"
        count = export_play_history(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert count == 1

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            row = next(reader)
            assert row[-8:] == ['N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A']

    def test_export_play_history_starred_true(self, tmp_path):
        """测试starred列的显示"""
        mock_nav_conn = Mock()
        mock_nav_cursor = Mock()
        mock_nav_cursor.fetchall.return_value = [
            ('song_001', 5, True, '2024-01-15', 'Song', 'Artist', 'Album', 2020, 'Rock')
        ]
        mock_nav_conn.execute.return_value = mock_nav_cursor

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.return_value = ('Mood', 'Energy', 'Genre', 'Style', 'Scene', 'Region', 'Culture', 'Language')
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "play_history.csv"
        export_play_history(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            row = next(reader)
            assert row[7] == 'Yes'

    def test_export_play_history_starred_false(self, tmp_path):
        """测试starred为False时的显示"""
        mock_nav_conn = Mock()
        mock_nav_cursor = Mock()
        mock_nav_cursor.fetchall.return_value = [
            ('song_001', 5, False, '2024-01-15', 'Song', 'Artist', 'Album', 2020, 'Rock')
        ]
        mock_nav_conn.execute.return_value = mock_nav_cursor

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.return_value = ('Mood', 'Energy', 'Genre', 'Style', 'Scene', 'Region', 'Culture', 'Language')
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "play_history.csv"
        export_play_history(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            row = next(reader)
            assert row[7] == 'No'

    def test_export_play_history_null_year_and_genre(self, tmp_path):
        """测试年份和原始genre为None的情况"""
        mock_nav_conn = Mock()
        mock_nav_cursor = Mock()
        mock_nav_cursor.fetchall.return_value = [
            ('song_001', 1, False, None, 'NoYear', 'Artist', 'Album', None, None)
        ]
        mock_nav_conn.execute.return_value = mock_nav_cursor

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "play_history.csv"
        count = export_play_history(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert count == 1
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            row = next(reader)
            assert row[4] == ''
            assert row[5] == ''
            assert row[8] == ''


class TestExportPlaylists:
    """测试导出歌单功能"""

    def test_export_playlists_empty(self, tmp_path):
        """测试导出空的歌单"""
        mock_nav_conn = Mock()

        def nav_execute(query, params):
            cursor = Mock()
            if 'playlist' in query:
                cursor.fetchall.return_value = []
            return cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "playlists.csv"
        count = export_playlists(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert count == 0

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == [
                'playlist_id', 'playlist_name', 'updated_at',
                'song_id', 'title', 'artist', 'album',
                'mood', 'energy', 'genre', 'style', 'scene', 'region', 'culture', 'language'
            ]

    def test_export_playlists_with_data(self, tmp_path):
        """测试导出有数据的歌单"""
        mock_nav_conn = Mock()

        playlists_data = [
            ('playlist_001', 'My Playlist', '2024-01-20'),
            ('playlist_002', 'Favorites', '2024-01-25')
        ]

        songs_data_1 = [
            ('song_001', 'Song A', 'Artist A', 'Album A'),
            ('song_002', 'Song B', 'Artist B', 'Album B')
        ]
        songs_data_2 = [
            ('song_003', 'Song C', 'Artist C', 'Album C')
        ]

        semantic_data_1 = ('Energetic', 'High', 'Rock', 'Alternative', 'Driving', 'US', 'Western', 'English')
        semantic_data_2 = (None, None, None, None, None, None, None, None)
        semantic_data_3 = ('Relaxed', 'Low', 'Pop', 'Ballad', 'Work', 'UK', 'English', 'English')

        def nav_execute(query, params):
            cursor = Mock()
            if 'playlist' in query and 'playlist_tracks' not in query:
                cursor.fetchall.return_value = playlists_data
            else:
                if params[0] == 'playlist_001':
                    cursor.fetchall.return_value = songs_data_1
                else:
                    cursor.fetchall.return_value = songs_data_2
            return cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.side_effect = [
            semantic_data_1, semantic_data_2, semantic_data_3
        ]
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "playlists.csv"
        count = export_playlists(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert count == 2

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            rows = list(reader)
            assert len(rows) == 3
            assert rows[0][:4] == ['playlist_001', 'My Playlist', '2024-01-20', 'song_001']
            assert rows[0][4:8] == ['Song A', 'Artist A', 'Album A', 'Energetic']
            assert rows[1][:4] == ['playlist_001', 'My Playlist', '2024-01-20', 'song_002']
            assert rows[1][7:11] == ['', '', '', '']
            assert rows[2][:4] == ['playlist_002', 'Favorites', '2024-01-25', 'song_003']

    def test_export_playlists_no_semantic_data(self, tmp_path):
        """测试歌曲没有语义标签"""
        mock_nav_conn = Mock()

        playlists_data = [('playlist_001', 'My Playlist', '2024-01-20')]
        songs_data = [('song_001', 'Song', 'Artist', 'Album')]

        def nav_execute(query, params):
            cursor = Mock()
            if 'playlist_tracks' not in query:
                cursor.fetchall.return_value = playlists_data
            else:
                cursor.fetchall.return_value = songs_data
            return cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchone.return_value = None
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "playlists.csv"
        export_playlists(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            row = next(reader)
            assert row[-4:] == ['N/A', 'N/A', 'N/A', 'N/A']

    def test_export_playlists_empty_playlist(self, tmp_path):
        """测试空歌单（没有歌曲）"""
        mock_nav_conn = Mock()

        playlists_data = [('playlist_001', 'Empty Playlist', '2024-01-20')]

        def nav_execute(query, params):
            cursor = Mock()
            if 'playlist_tracks' not in query:
                cursor.fetchall.return_value = playlists_data
            else:
                cursor.fetchall.return_value = []
            return cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "playlists.csv"
        count = export_playlists(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert count == 1

        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader)
            assert list(reader) == []


class TestExportStatistics:
    """测试导出统计数据功能"""

    def test_export_statistics_basic(self, tmp_path):
        """测试导出基本统计数据"""
        mock_nav_conn = Mock()

        playlist_cursor = Mock()
        playlist_cursor.fetchone.return_value = (5,)

        play_stats_cursor = Mock()
        play_stats_cursor.fetchone.return_value = (100, 500, 25)

        def nav_execute(query, params):
            if 'playlist' in query.lower():
                return playlist_cursor
            return play_stats_cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchall.return_value = [
            ('Energetic', 30),
            ('Relaxed', 20),
            ('Happy', 50)
        ]
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "statistics.json"
        stats = export_statistics(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert stats['user_id'] == 'user_001'
        assert 'export_time' in stats
        assert stats['total_songs'] == 100
        assert stats['total_plays'] == 500
        assert stats['starred_count'] == 25
        assert stats['playlist_count'] == 5
        assert stats['mood_distribution'] == {
            'Energetic': 30,
            'Relaxed': 20,
            'Happy': 50
        }

        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_stats = json.load(f)
            assert loaded_stats == stats

    def test_export_statistics_zero_values(self, tmp_path):
        """测试统计数据为零的情况"""
        mock_nav_conn = Mock()

        playlist_cursor = Mock()
        playlist_cursor.fetchone.return_value = (0,)

        play_stats_cursor = Mock()
        play_stats_cursor.fetchone.return_value = (0, 0, 0)

        def nav_execute(query, params):
            if 'playlist' in query.lower():
                return playlist_cursor
            return play_stats_cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "statistics.json"
        stats = export_statistics(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert stats['total_songs'] == 0
        assert stats['total_plays'] == 0
        assert stats['starred_count'] == 0
        assert stats['playlist_count'] == 0
        assert stats['mood_distribution'] == {}

    def test_export_statistics_none_mood_values(self, tmp_path):
        """测试mood为None的情况"""
        mock_nav_conn = Mock()

        playlist_cursor = Mock()
        playlist_cursor.fetchone.return_value = (2,)

        play_stats_cursor = Mock()
        play_stats_cursor.fetchone.return_value = (10, 50, 5)

        def nav_execute(query, params):
            if 'playlist' in query.lower():
                return playlist_cursor
            return play_stats_cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchall.return_value = [
            ('Energetic', 5),
            (None, 5)
        ]
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "statistics.json"
        stats = export_statistics(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert stats['mood_distribution'] == {
            'Energetic': 5,
            None: 5
        }

    def test_export_statistics_export_time_format(self, tmp_path):
        """测试导出时间格式"""
        mock_nav_conn = Mock()

        playlist_cursor = Mock()
        playlist_cursor.fetchone.return_value = (1,)

        play_stats_cursor = Mock()
        play_stats_cursor.fetchone.return_value = (1, 1, 0)

        def nav_execute(query, params):
            if 'playlist' in query.lower():
                return playlist_cursor
            return play_stats_cursor

        mock_nav_conn.execute.side_effect = nav_execute

        mock_sem_conn = Mock()
        mock_sem_cursor = Mock()
        mock_sem_cursor.fetchall.return_value = []
        mock_sem_conn.execute.return_value = mock_sem_cursor

        output_file = tmp_path / "statistics.json"
        stats = export_statistics(mock_nav_conn, mock_sem_conn, 'user_001', str(output_file))

        assert datetime.fromisoformat(stats['export_time'])


class TestMain:
    """测试主函数"""

    @patch('src.utils.export.dbs_context')
    @patch('src.utils.export.get_user_id')
    @patch('src.utils.export.export_play_history')
    @patch('src.utils.export.export_playlists')
    @patch('src.utils.export.export_statistics')
    @patch('os.makedirs')
    def test_main_success(self, mock_makedirs, mock_export_stats, mock_export_playlists,
                        mock_export_history, mock_get_user_id, mock_dbs_context, tmp_path):
        """测试主函数正常执行流程"""
        mock_nav_conn = Mock()
        mock_sem_conn = Mock()
        mock_dbs_context.return_value.__enter__.return_value = (mock_nav_conn, mock_sem_conn)

        mock_get_user_id.return_value = ('user_001', 'Alice')

        mock_export_history.return_value = 100
        mock_export_playlists.return_value = 5
        mock_export_stats.return_value = {
            'total_songs': 100,
            'total_plays': 500,
            'starred_count': 25,
            'playlist_count': 5,
            'mood_distribution': {}
        }

        with patch('src.utils.export.EXPORT_DIR', str(tmp_path)):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                main()

        mock_get_user_id.assert_called_once_with(mock_nav_conn)
        mock_makedirs.assert_called_once()
        mock_export_history.assert_called_once()
        mock_export_playlists.assert_called_once()
        mock_export_stats.assert_called_once()

    @patch('src.utils.export.dbs_context')
    @patch('sys.exit')
    def test_main_keyboard_interrupt(self, mock_exit, mock_dbs_context, tmp_path):
        """测试主函数被KeyboardInterrupt中断"""
        mock_nav_conn = Mock()
        mock_sem_conn = Mock()
        mock_dbs_context.return_value.__enter__.side_effect = KeyboardInterrupt()

        with patch('src.utils.export.EXPORT_DIR', str(tmp_path)):
            main()

        mock_exit.assert_called_once_with(0)

    @patch('src.utils.export.dbs_context')
    @patch('sys.exit')
    def test_main_exception(self, mock_exit, mock_dbs_context, tmp_path):
        """测试主函数遇到异常"""
        mock_dbs_context.return_value.__enter__.side_effect = RuntimeError("Database error")

        with patch('src.utils.export.EXPORT_DIR', str(tmp_path)):
            main()

        mock_exit.assert_called_once_with(1)

    @patch('src.utils.export.dbs_context')
    @patch('src.utils.export.get_user_id')
    @patch('src.utils.export.export_play_history')
    @patch('src.utils.export.export_playlists')
    @patch('src.utils.export.export_statistics')
    @patch('os.makedirs')
    def test_main_creates_readme(self, mock_makedirs, mock_export_stats, mock_export_playlists,
                                mock_export_history, mock_get_user_id, mock_dbs_context, tmp_path):
        """测试主函数创建README文件"""
        mock_nav_conn = Mock()
        mock_sem_conn = Mock()
        mock_dbs_context.return_value.__enter__.return_value = (mock_nav_conn, mock_sem_conn)

        mock_get_user_id.return_value = ('user_001', 'Alice')
        mock_export_history.return_value = 10
        mock_export_playlists.return_value = 2
        mock_export_stats.return_value = {
            'total_songs': 10,
            'total_plays': 100,
            'starred_count': 3,
            'playlist_count': 2,
            'mood_distribution': {}
        }

        written_content = []

        def open_side_effect(filename, mode, **kwargs):
            mock_file = MagicMock()
            mock_file.write.side_effect = written_content.append
            mock_file.__enter__.return_value = mock_file
            return mock_file

        with patch('src.utils.export.EXPORT_DIR', str(tmp_path)):
            with patch('builtins.open', side_effect=open_side_effect):
                main()

        assert any('用户数据导出' in content for content in written_content)
        assert any('Alice' in content for content in written_content)

    @patch('src.utils.export.dbs_context')
    @patch('src.utils.export.get_user_id')
    @patch('src.utils.export.export_play_history')
    @patch('src.utils.export.export_playlists')
    @patch('src.utils.export.export_statistics')
    @patch('os.makedirs')
    def test_main_export_directory_format(self, mock_makedirs, mock_export_stats, mock_export_playlists,
                                         mock_export_history, mock_get_user_id, mock_dbs_context, tmp_path):
        """测试导出目录命名格式"""
        mock_nav_conn = Mock()
        mock_sem_conn = Mock()
        mock_dbs_context.return_value.__enter__.return_value = (mock_nav_conn, mock_sem_conn)

        mock_get_user_id.return_value = ('user_001', 'TestUser')
        mock_export_history.return_value = 1
        mock_export_playlists.return_value = 1
        mock_export_stats.return_value = {
            'total_songs': 1,
            'total_plays': 1,
            'starred_count': 0,
            'playlist_count': 1,
            'mood_distribution': {}
        }

        with patch('src.utils.export.EXPORT_DIR', str(tmp_path)):
            with patch('builtins.open', create=True):
                main()

        assert mock_makedirs.called
        call_args = mock_makedirs.call_args
        dir_name = call_args[0][0]
        assert 'TestUser' in dir_name
        assert 'export_' in dir_name
