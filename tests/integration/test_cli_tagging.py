"""
测试标签生成 CLI 命令
"""

import pytest
from unittest.mock import Mock, patch

from src.cli.tagging_cli import TaggingCLI


class TestTaggingCLI:
    """测试标签生成 CLI"""

    @pytest.fixture
    def sample_songs(self):
        """示例歌曲数据"""
        return [
            {
                "id": "song1",
                "title": "Test Song 1",
                "artist": "Test Artist 1",
                "album": "Test Album 1"
            },
            {
                "id": "song2",
                "title": "Test Song 2",
                "artist": "Test Artist 2",
                "album": "Test Album 2"
            }
        ]

    @pytest.fixture
    def sample_tags(self):
        """示例标签数据"""
        return {
            "mood": "happy",
            "energy": "medium",
            "genre": "pop",
            "region": "Western",
            "subculture": "None",
            "scene": "None",
            "confidence": 0.85
        }

    @pytest.fixture
    def sample_result(self):
        """示例处理结果"""
        return {
            "total": 10,
            "tagged": 5,
            "processed": 3,
            "failed": 1,
            "remaining": 1
        }

    def test_main_success(self, sample_result, capsys):
        """测试成功生成标签"""
        with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
            mock_tagging_service = Mock()
            mock_tagging_service.process_all_songs = Mock(return_value=sample_result)
            mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

            TaggingCLI.main()

            captured = capsys.readouterr()
            assert "标签生成完成" in captured.out
            assert "总歌曲数: 10" in captured.out
            assert "已标记: 5" in captured.out
            assert "本次处理: 3" in captured.out
            assert "失败: 1" in captured.out
            assert "剩余: 1" in captured.out

    def test_main_failure(self, capsys):
        """测试标签生成失败"""
        with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
            mock_tagging_service = Mock()
            mock_tagging_service.process_all_songs = Mock(side_effect=Exception("API Error"))
            mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

            with pytest.raises(Exception):
                TaggingCLI.main()

    def test_main_no_songs_to_process(self, capsys):
        """测试没有歌曲需要处理"""
        result_no_processing = {
            "total": 5,
            "tagged": 5,
            "processed": 0,
            "failed": 0,
            "remaining": 0
        }

        with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
            mock_tagging_service = Mock()
            mock_tagging_service.process_all_songs = Mock(return_value=result_no_processing)
            mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

            TaggingCLI.main()

            captured = capsys.readouterr()
            assert "标签生成完成" in captured.out
            assert "本次处理: 0" in captured.out

    def test_main_all_failures(self, capsys):
        """测试所有歌曲都失败"""
        result_all_failures = {
            "total": 3,
            "tagged": 0,
            "processed": 0,
            "failed": 3,
            "remaining": 0
        }

        with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
            mock_tagging_service = Mock()
            mock_tagging_service.process_all_songs = Mock(return_value=result_all_failures)
            mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

            TaggingCLI.main()

            captured = capsys.readouterr()
            assert "标签生成完成" in captured.out
            assert "失败: 3" in captured.out

    def test_preview_success(self, sample_songs, sample_tags, capsys):
        """测试成功预览标签生成"""
        with patch('src.cli.tagging_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_nav_repo = Mock()
            mock_nav_repo.get_all_songs = Mock(return_value=sample_songs[:3])

            with patch('src.cli.tagging_cli.NavidromeRepository', return_value=mock_nav_repo):
                with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
                    mock_tagging_service = Mock()
                    mock_tagging_service.generate_tag = Mock(return_value={
                        "title": "Test Song",
                        "artist": "Test Artist",
                        "tags": sample_tags
                    })
                    mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

                    TaggingCLI.preview()

                    captured = capsys.readouterr()
                    assert "预览标签生成" in captured.out
                    assert "Test Song 1" in captured.out
                    assert "happy" in captured.out
                    assert "0.85" in captured.out

    def test_preview_partial_failure(self, sample_songs, sample_tags, capsys):
        """测试预览时部分失败"""
        with patch('src.cli.tagging_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_nav_repo = Mock()
            mock_nav_repo.get_all_songs = Mock(return_value=sample_songs[:2])

            with patch('src.cli.tagging_cli.NavidromeRepository', return_value=mock_nav_repo):
                with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
                    mock_tagging_service = Mock()

                    def side_effect(title, artist, album):
                        if title == "Test Song 1":
                            return {
                                "title": title,
                                "artist": artist,
                                "tags": sample_tags
                            }
                        else:
                            raise Exception("API Error")

                    mock_tagging_service.generate_tag = Mock(side_effect=side_effect)
                    mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

                    TaggingCLI.preview()

                    captured = capsys.readouterr()
                    assert "预览标签生成" in captured.out
                    assert "生成失败" in captured.out

    def test_preview_empty_songs(self, capsys):
        """测试空歌曲列表预览"""
        with patch('src.cli.tagging_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_nav_repo = Mock()
            mock_nav_repo.get_all_songs = Mock(return_value=[])

            with patch('src.cli.tagging_cli.NavidromeRepository', return_value=mock_nav_repo):
                with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
                    mock_tagging_service = Mock()
                    mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

                    TaggingCLI.preview()

                    captured = capsys.readouterr()
                    assert "预览标签生成" in captured.out

    def test_preview_all_fields_displayed(self, sample_songs, capsys):
        """测试预览显示所有标签字段"""
        tags_all_fields = {
            "mood": "epic",
            "energy": "high",
            "genre": "rock",
            "region": "Western",
            "subculture": "None",
            "scene": "None",
            "confidence": 0.92
        }

        with patch('src.cli.tagging_cli.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_nav_repo = Mock()
            mock_nav_repo.get_all_songs = Mock(return_value=sample_songs[:1])

            with patch('src.cli.tagging_cli.NavidromeRepository', return_value=mock_nav_repo):
                with patch('src.cli.tagging_cli.ServiceFactory') as mock_factory:
                    mock_tagging_service = Mock()
                    mock_tagging_service.generate_tag = Mock(return_value={
                        "title": "Test Song",
                        "artist": "Test Artist",
                        "tags": tags_all_fields
                    })
                    mock_factory.create_tagging_service = Mock(return_value=mock_tagging_service)

                    Tagging.cli.preview()

                    captured = capsys.readouterr()
                    assert "Mood:" in captured.out
                    assert "Energy:" in captured.out
                    assert "Genre:" in captured.out
                    assert "Region:" in captured.out
                    assert "Confidence:" in captured.out
