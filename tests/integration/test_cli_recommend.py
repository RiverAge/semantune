"""
测试推荐 CLI 命令
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import sys

from src.cli.recommend_cli import RecommendCLI


class TestRecommendCLI:
    """测试推荐 CLI"""

    @pytest.fixture
    def sample_users(self):
        """示例用户数据"""
        return [
            {"id": "user_1", "name": "test_user_1"},
            {"id": "user_2", "name": "test_user_2"}
        ]

    @pytest.fixture
    def sample_recommendations(self):
        """示例推荐数据"""
        return [
            {
                "file_id": "song1",
                "title": "Test Song 1",
                "artist": "Test Artist 1",
                "album": "Test Album 1",
                "mood": "happy",
                "energy": "medium",
                "genre": "pop",
                "region": "Western",
                "confidence": 0.85,
                "similarity": 0.92
            },
            {
                "file_id": "song2",
                "title": "Test Song 2",
                "artist": "Test Artist 2",
                "album": "Test Album 2",
                "mood": "epic",
                "energy": "high",
                "genre": "rock",
                "region": "Western",
                "confidence": 0.90,
                "similarity": 0.88
            }
        ]

    def test_main_single_user(self, sample_users, sample_recommendations, capsys, caplog):
        """测试单个用户场景 - 自动选择"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_users[0]])
            mock_user_repo.get_user_songs = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                with patch('src.cli.recommend_cli.ServiceFactory') as mock_factory:
                    mock_recommend_service = Mock()
                    mock_recommend_service.recommend = Mock(return_value=sample_recommendations)
                    mock_factory.create_recommend_service = Mock(return_value=mock_recommend_service)

                    RecommendCLI.main()

                    assert "test_user_1" in caplog.text
                    assert "推荐完成" in caplog.text
                    assert "Test Song 1" in caplog.text
                    assert "Test Song 2" in caplog.text

    def test_main_multiple_users(self, sample_users, sample_recommendations, caplog):
        """测试多用户场景 - 模拟选择第一个用户"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=sample_users)
            mock_user_repo.get_user_songs = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                with patch('src.cli.recommend_cli.ServiceFactory') as mock_factory:
                    mock_recommend_service = Mock()
                    mock_recommend_service.recommend = Mock(return_value=sample_recommendations)
                    mock_factory.create_recommend_service = Mock(return_value=mock_recommend_service)

                    with patch('builtins.input', return_value='1'):
                        RecommendCLI.main()

                    assert "可用用户" in caplog.text
                    assert "test_user_1" in caplog.text
                    assert "test_user_2" in caplog.text

    def test_main_no_users(self, caplog):
        """测试无用户场景"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                RecommendCLI.main()

                assert "未找到用户" in caplog.text

    def test_main_recommendation_failure(self, sample_users, caplog):
        """测试推荐生成失败"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_users[0]])
            mock_user_repo.get_user_songs = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                with patch('src.cli.recommend_cli.ServiceFactory') as mock_factory:
                    mock_recommend_service = Mock()
                    mock_recommend_service.recommend = Mock(side_effect=Exception("Recommendation error"))
                    mock_factory.create_recommend_service = Mock(return_value=mock_recommend_service)

                    with pytest.raises(Exception):
                        RecommendCLI.main()

    def test_main_empty_recommendations(self, sample_users, caplog):
        """测试空推荐列表"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_users[0]])
            mock_user_repo.get_user_songs = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                with patch('src.cli.recommend_cli.ServiceFactory') as mock_factory:
                    mock_recommend_service = Mock()
                    mock_recommend_service.recommend = Mock(return_value=[])
                    mock_factory.create_recommend_service = Mock(return_value=mock_recommend_service)

                    RecommendCLI.main()

                    assert "推荐完成" in caplog.text
                    assert "共 0 首歌曲" in caplog.text

    def test_main_long_song_names(self, sample_users, caplog):
        """测试长歌曲/歌手名称的截断显示"""
        caplog.set_level(logging.INFO)
        long_recommendations = [
            {
                "file_id": "song1",
                "title": "This is a very long song title that exceeds the display limit and should be truncated",
                "artist": "This Artist Name Is Too Long For The Display",
                "album": "Album",
                "mood": "happy",
                "energy": "medium",
                "genre": "pop",
                "similarity": 0.92
            }
        ]

        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_users[0]])
            mock_user_repo.get_user_songs = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                with patch('src.cli.recommend_cli.ServiceFactory') as mock_factory:
                    mock_recommend_service = Mock()
                    mock_recommend_service.recommend = Mock(return_value=long_recommendations)
                    mock_factory.create_recommend_service = Mock(return_value=mock_recommend_service)

                    RecommendCLI.main()

                    assert ".." in caplog.text
                    assert "推荐完成" in caplog.text

    def test_main_missing_optional_fields(self, sample_users, caplog):
        """测试缺少可选字段的歌曲"""
        caplog.set_level(logging.INFO)
        recommendations_without_fields = [
            {
                "file_id": "song1",
                "title": "Song 1",
                "artist": "Artist 1",
                "similarity": 0.92
            }
        ]

        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_users[0]])
            mock_user_repo.get_user_songs = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                with patch('src.cli.recommend_cli.ServiceFactory') as mock_factory:
                    mock_recommend_service = Mock()
                    mock_recommend_service.recommend = Mock(return_value=recommendations_without_fields)
                    mock_factory.create_recommend_service = Mock(return_value=mock_recommend_service)

                    RecommendCLI.main()

                    assert "推荐完成" in caplog.text
                    assert "N/A" in caplog.text

    def test_main_user_prompt_number(self, sample_users, sample_recommendations, caplog):
        """测试用户输入数字选择"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.recommend_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=sample_users)
            mock_user_repo.get_user_songs = Mock(return_value=[])

            with patch('src.cli.recommend_cli.UserRepository', return_value=mock_user_repo):
                with patch('src.cli.recommend_cli.ServiceFactory') as mock_factory:
                    mock_recommend_service = Mock()
                    mock_recommend_service.recommend = Mock(return_value=sample_recommendations)
                    mock_factory.create_recommend_service = Mock(return_value=mock_recommend_service)

                    user_inputs = ['2', '1']
                    with patch('builtins.input', side_effect=user_inputs):
                        RecommendCLI.main()

                    assert "test_user_2" in caplog.text
