"""
测试查询和分析 CLI 命令
"""

import pytest
import logging
from unittest.mock import Mock, patch

from src.cli.query_cli import QueryCLI
from src.cli.analyze_cli import AnalyzeCLI


class TestQueryCLI:
    """测试查询 CLI"""

    @pytest.fixture
    def sample_scenes(self):
        """示例场景"""
        return ["Study", "Workout", "Night", "Morning", "Relax"]

    @pytest.fixture
    def sample_songs(self):
        """示例歌曲数据"""
        return [
            {
                "file_id": "song1",
                "title": "Study Song 1",
                "artist": "Study Artist 1",
                "album": "Study Album",
                "mood": "Peaceful",
                "energy": "Low",
                "genre": "Classical"
            },
            {
                "file_id": "song2",
                "title": "Study Song 2",
                "artist": "Study Artist 2",
                "album": "Study Album",
                "mood": "Peaceful",
                "energy": "Low",
                "genre": "Ambient"
            }
        ]

    def test_main_success(self, sample_scenes, sample_songs, caplog):
        """测试成功查询"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.query_cli.ServiceFactory') as mock_factory:
            mock_query_service = Mock()
            mock_query_service.get_available_scenes = Mock(return_value=sample_scenes)
            mock_query_service.query_by_scene_preset = Mock(return_value=sample_songs)
            mock_factory.create_query_service = Mock(return_value=mock_query_service)

            with patch('builtins.input', return_value='1'):
                QueryCLI.main()

            assert "可用场景" in caplog.text
            assert "查询完成" in caplog.text
            assert "Study" in caplog.text
            assert "Song" in caplog.text
            assert "查询完成" in caplog.text
            assert "共 2 首歌曲" in caplog.text
            assert "Study Song 1" in caplog.text

    def test_main_no_scenes(self, caplog):
        """测试没有可用场景"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.query_cli.ServiceFactory') as mock_factory:
            mock_query_service = Mock()
            mock_query_service.get_available_scenes = Mock(return_value=[])
            mock_factory.create_query_service = Mock(return_value=mock_query_service)

            with patch('builtins.input', return_value='1'):
                with pytest.raises(IndexError):
                    QueryCLI.main()

    def test_main_empty_results(self, sample_scenes, caplog):
        """测试空查询结果"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.query_cli.ServiceFactory') as mock_factory:
            mock_query_service = Mock()
            mock_query_service.get_available_scenes = Mock(return_value=sample_scenes)
            mock_query_service.query_by_scene_preset = Mock(return_value=[])
            mock_factory.create_query_service = Mock(return_value=mock_query_service)

            with patch('builtins.input', return_value='1'):
                QueryCLI.main()

            # captured = caplog.readouterr()
            assert "共 0 首歌曲" in caplog.text

    def test_main_long_names(self, caplog):
        """测试长歌曲名称截断"""
        caplog.set_level(logging.INFO)
        long_songs = [
            {
                "file_id": "song1",
                "title": "This is a very long song title that should be truncated",
                "artist": "Artist With Very Long Name",
                "mood": "Peaceful",
                "energy": "Low",
                "genre": "Classical"
            }
        ]

        with patch('src.cli.query_cli.ServiceFactory') as mock_factory:
            mock_query_service = Mock()
            mock_query_service.get_available_scenes = Mock(return_value=["Study"])
            mock_query_service.query_by_scene_preset = Mock(return_value=long_songs)
            mock_factory.create_query_service = Mock(return_value=mock_query_service)

            with patch('builtins.input', return_value='1'):
                QueryCLI.main()

            # captured = caplog.readouterr()
            assert ".." in caplog.text

    def test_main_missing_fields(self, caplog):
        """测试缺少可选字段的歌曲"""
        caplog.set_level(logging.INFO)
        incomplete_songs = [
            {
                "file_id": "song1",
                "title": "Incomplete Song",
                "artist": "Artist"
            }
        ]

        with patch('src.cli.query_cli.ServiceFactory') as mock_factory:
            mock_query_service = Mock()
            mock_query_service.get_available_scenes = Mock(return_value=["Study"])
            mock_query_service.query_by_scene_preset = Mock(return_value=incomplete_songs)
            mock_factory.create_query_service = Mock(return_value=mock_query_service)

            with patch('builtins.input', return_value='1'):
                QueryCLI.main()

            # captured = caplog.readouterr()
            assert "N/A" in caplog.text


class TestAnalyzeCLI:
    """测试分析 CLI"""

    @pytest.fixture
    def sample_overview(self):
        """示例概览数据"""
        return {
            "total_songs": 100,
            "average_confidence": 0.82,
            "low_confidence_count": 5,
            "low_confidence_percentage": 5.0
        }

    @pytest.fixture
    def sample_distribution(self):
        """示例分布数据"""
        return {
            "field_name": "mood",
            "total": 100,
            "distribution": [
                {"label": "happy", "count": 30, "percentage": 30.0},
                {"label": "sad", "count": 20, "percentage": 20.0},
                {"label": "epic", "count": 15, "percentage": 15.0}
            ]
        }

    @pytest.fixture
    def sample_combinations(self):
        """示例组合数据"""
        return {
            "combinations": [
                {"mood": "happy", "energy": "high", "count": 25, "percentage": 25.0},
                {"mood": "sad", "energy": "low", "count": 20, "percentage": 20.0}
            ]
        }

    @pytest.fixture
    def sample_quality(self):
        """示例质量数据"""
        return {
            "none_stats": {
                "mood": {"count": 3, "percentage": 3.0},
                "energy": {"count": 2, "percentage": 2.0},
                "genre": {"count": 5, "percentage": 5.0}
            }
        }

    def test_main_success(self, sample_overview, sample_distribution, sample_combinations, sample_quality, caplog):
        """测试成功分析"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.analyze_cli.ServiceFactory') as mock_factory:
            mock_analyze_service = Mock()
            mock_analyze_service.get_overview = Mock(return_value=sample_overview)
            mock_analyze_service.get_distribution = Mock(return_value=sample_distribution)
            mock_analyze_service.get_combinations = Mock(return_value=sample_combinations)
            mock_analyze_service.get_quality_stats = Mock(return_value=sample_quality)
            mock_factory.create_analyze_service = Mock(return_value=mock_analyze_service)

            AnalyzeCLI.main()

            # captured = caplog.readouterr()
            assert "分析数据" in caplog.text
            assert "数据概览" in caplog.text
            assert "总歌曲数: 100" in caplog.text
            assert "平均置信度: 0.82" in caplog.text
            assert "mood 分布" in caplog.text
            assert "happy" in caplog.text
            assert "Mood + Energy 组合" in caplog.text
            assert "数据质量分析" in caplog.text
            assert "分析完成" in caplog.text

    def test_main_empty_distribution(self, sample_overview, caplog):
        """测试空分布数据"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.analyze_cli.ServiceFactory') as mock_factory:
            mock_analyze_service = Mock()
            mock_analyze_service.get_overview = Mock(return_value=sample_overview)
            mock_analyze_service.get_distribution = Mock(return_value={"field_name": "mood", "total": 0, "distribution": []})
            mock_analyze_service.get_combinations = Mock(return_value={"combinations": []})
            mock_analyze_service.get_quality_stats = Mock(return_value={"none_stats": {}})
            mock_factory.create_analyze_service = Mock(return_value=mock_analyze_service)

            AnalyzeCLI.main()

            # captured = caplog.readouterr()
            assert "分析完成" in caplog.text

    def test_main_no_songs(self, caplog):
        """测试空数据库"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.analyze_cli.ServiceFactory') as mock_factory:
            mock_analyze_service = Mock()
            mock_analyze_service.get_overview = Mock(return_value={
                "total_songs": 0, 
                "average_confidence": 0, 
                "high_confidence_count": 0,
                "low_confidence_count": 0,
                "low_confidence_percentage": 0
            })
            mock_analyze_service.get_distribution = Mock(return_value={
                "field_name": "mood", "total": 0, "distribution": []
            })
            mock_analyze_service.get_combinations = Mock(return_value={"combinations": []})
            mock_analyze_service.get_quality_stats = Mock(return_value={"none_stats": {}})
            mock_factory.create_analyze_service = Mock(return_value=mock_analyze_service)

            AnalyzeCLI.main()

            # captured = caplog.readouterr()
            assert "总歌曲数: 0" in caplog.text
            assert "分析完成" in caplog.text

    def test_main_failure_during_analysis(self, sample_overview, caplog):
        """测试分析过程中出错"""
        caplog.set_level(logging.INFO)
        with patch('src.cli.analyze_cli.ServiceFactory') as mock_factory:
            mock_analyze_service = Mock()
            mock_analyze_service.get_overview = Mock(return_value=sample_overview)
            mock_analyze_service.get_distribution = Mock(side_effect=Exception("Database error"))
            mock_factory.create_analyze_service = Mock(return_value=mock_analyze_service)

            with pytest.raises(Exception):
                AnalyzeCLI.main()

    def test_main_multiple_fields(self, sample_overview, sample_quality, caplog):
        """测试多字段分析"""
        caplog.set_level(logging.INFO)
        distributions = {
            "mood": {"field_name": "mood", "total": 100, "distribution": [{"label": "happy", "count": 30, "percentage": 30.0}]},
            "energy": {"field_name": "energy", "total": 100, "distribution": [{"label": "high", "count": 50, "percentage": 50.0}]},
            "genre": {"field_name": "genre", "total": 100, "distribution": [{"label": "pop", "count": 40, "percentage": 40.0}]},
            "region": {"field_name": "region", "total": 100, "distribution": [{"label": "Western", "count": 60, "percentage": 60.0}]}
        }
        with patch('src.cli.analyze_cli.ServiceFactory') as mock_factory:
            mock_analyze_service = Mock()
            mock_analyze_service.get_overview = Mock(return_value=sample_overview)
            mock_analyze_service.get_distribution = Mock(side_effect=lambda x: distributions.get(x, {}))
            mock_analyze_service.get_combinations = Mock(return_value={"combinations": []})
            mock_analyze_service.get_quality_stats = Mock(return_value=sample_quality)
            mock_factory.create_analyze_service = Mock(return_value=mock_analyze_service)

            AnalyzeCLI.main()

            # captured = caplog.readouterr()
            assert "mood 分布" in caplog.text
            assert "energy 分布" in caplog.text
            assert "genre 分布" in caplog.text
            assert "region 分布" in caplog.text
