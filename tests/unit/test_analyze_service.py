"""
测试分析服务
"""
import pytest
from unittest.mock import Mock, MagicMock

from src.services.analyze_service import AnalyzeService


class TestAnalyzeService:
    """测试分析服务类"""

    def test_analyze_service_initialization(self):
        """测试服务初始化"""
        sem_repo = Mock()
        service = AnalyzeService(sem_repo)
        
        assert service.sem_repo == sem_repo

    def test_get_distribution_valid_field(self):
        """测试获取有效字段的分布"""
        sem_repo = Mock()
        sem_repo.get_distribution.return_value = {"happy": 10, "sad": 5}
        
        service = AnalyzeService(sem_repo)
        result = service.get_distribution("mood")
        
        assert result["field"] == "mood"
        assert result["field_name"] == "Mood"
        assert result["distribution"] == {"happy": 10, "sad": 5}
        sem_repo.get_distribution.assert_called_once_with("mood")

    def test_get_distribution_all_valid_fields(self):
        """测试所有有效字段"""
        valid_fields = ['mood', 'energy', 'genre', 'region', 'scene', 'subculture']
        sem_repo = Mock()
        sem_repo.get_distribution.return_value = {}
        
        service = AnalyzeService(sem_repo)
        
        for field in valid_fields:
            result = service.get_distribution(field)
            assert result["field"] == field
            assert result["field_name"] == field.capitalize()

    def test_get_distribution_invalid_field(self):
        """测试获取无效字段的分布"""
        sem_repo = Mock()
        service = AnalyzeService(sem_repo)
        
        with pytest.raises(ValueError) as exc_info:
            service.get_distribution("invalid_field")
        
        assert "无效的字段" in str(exc_info.value)
        sem_repo.get_distribution.assert_not_called()

    def test_get_distribution_empty_field(self):
        """测试空字段"""
        sem_repo = Mock()
        service = AnalyzeService(sem_repo)
        
        with pytest.raises(ValueError) as exc_info:
            service.get_distribution("")
        
        assert "无效的字段" in str(exc_info.value)

    def test_get_combinations(self):
        """测试获取 Mood + Energy 组合"""
        sem_repo = Mock()
        expected_combinations = [
            {"mood": "happy", "energy": "high", "count": 10},
            {"mood": "sad", "energy": "low", "count": 5}
        ]
        sem_repo.get_combinations.return_value = expected_combinations
        
        service = AnalyzeService(sem_repo)
        result = service.get_combinations()
        
        assert result["combinations"] == expected_combinations
        sem_repo.get_combinations.assert_called_once()

    def test_get_combinations_empty(self):
        """测试获取空组合"""
        sem_repo = Mock()
        sem_repo.get_combinations.return_value = []
        
        service = AnalyzeService(sem_repo)
        result = service.get_combinations()
        
        assert result["combinations"] == []

    def test_get_region_genre_distribution(self):
        """测试获取地区流派分布"""
        sem_repo = Mock()
        expected_regions = {
            "流行": {"华语": 10, "欧美": 5},
            "摇滚": {"华语": 3}
        }
        sem_repo.get_region_genre_distribution.return_value = expected_regions
        
        service = AnalyzeService(sem_repo)
        result = service.get_region_genre_distribution()
        
        assert result["regions"] == expected_regions
        sem_repo.get_region_genre_distribution.assert_called_once()

    def test_get_region_genre_distribution_empty(self):
        """测试获取空地区流派分布"""
        sem_repo = Mock()
        sem_repo.get_region_genre_distribution.return_value = {}
        
        service = AnalyzeService(sem_repo)
        result = service.get_region_genre_distribution()
        
        assert result["regions"] == {}

    def test_get_quality_stats(self):
        """测试获取数据质量统计"""
        sem_repo = Mock()
        expected_quality = {
            "average_confidence": 0.85,
            "low_confidence_count": 5,
            "low_confidence_percentage": 10.0
        }
        sem_repo.get_quality_stats.return_value = expected_quality
        
        service = AnalyzeService(sem_repo)
        result = service.get_quality_stats()
        
        assert result == expected_quality
        sem_repo.get_quality_stats.assert_called_once()

    def test_get_quality_stats_with_low_confidence(self):
        """测试获取低质量数据统计"""
        sem_repo = Mock()
        expected_quality = {
            "average_confidence": 0.65,
            "low_confidence_count": 20,
            "low_confidence_percentage": 40.0
        }
        sem_repo.get_quality_stats.return_value = expected_quality
        
        service = AnalyzeService(sem_repo)
        result = service.get_quality_stats()
        
        assert result["average_confidence"] == 0.65
        assert result["low_confidence_count"] == 20
        assert result["low_confidence_percentage"] == 40.0

    def test_get_overview(self):
        """测试获取数据概览"""
        sem_repo = Mock()
        sem_repo.get_total_count.return_value = 100
        sem_repo.get_quality_stats.return_value = {
            "average_confidence": 0.85,
            "low_confidence_count": 5,
            "low_confidence_percentage": 10.0
        }
        
        service = AnalyzeService(sem_repo)
        result = service.get_overview()
        
        assert result["total_songs"] == 100
        assert result["average_confidence"] == 0.85
        assert result["low_confidence_count"] == 5
        assert result["low_confidence_percentage"] == 10.0
        sem_repo.get_total_count.assert_called_once()
        sem_repo.get_quality_stats.assert_called_once()

    def test_get_overview_empty_database(self):
        """测试空数据库的概览"""
        sem_repo = Mock()
        sem_repo.get_total_count.return_value = 0
        sem_repo.get_quality_stats.return_value = {
            "average_confidence": 0.0,
            "low_confidence_count": 0,
            "low_confidence_percentage": 0.0
        }
        
        service = AnalyzeService(sem_repo)
        result = service.get_overview()
        
        assert result["total_songs"] == 0
        assert result["average_confidence"] == 0.0

    def test_get_overview_with_low_quality(self):
        """测试低质量数据的概览"""
        sem_repo = Mock()
        sem_repo.get_total_count.return_value = 1000
        sem_repo.get_quality_stats.return_value = {
            "average_confidence": 0.72,
            "low_confidence_count": 150,
            "low_confidence_percentage": 15.0
        }
        
        service = AnalyzeService(sem_repo)
        result = service.get_overview()
        
        assert result["total_songs"] == 1000
        assert result["average_confidence"] == 0.72
        assert result["low_confidence_count"] == 150
        assert result["low_confidence_percentage"] == 15.0

    def test_get_distribution_repository_error(self):
        """测试仓库返回错误时的处理"""
        sem_repo = Mock()
        sem_repo.get_distribution.side_effect = Exception("Database error")
        
        service = AnalyzeService(sem_repo)
        
        with pytest.raises(Exception) as exc_info:
            service.get_distribution("mood")
        
        assert "Database error" in str(exc_info.value)

    def test_get_combinations_repository_error(self):
        """测试获取组合时仓库错误"""
        sem_repo = Mock()
        sem_repo.get_combinations.side_effect = Exception("Connection failed")
        
        service = AnalyzeService(sem_repo)
        
        with pytest.raises(Exception) as exc_info:
            service.get_combinations()
        
        assert "Connection failed" in str(exc_info.value)

    def test_get_overview_repository_error_on_total(self):
        """测试获取概览时总数仓库错误"""
        sem_repo = Mock()
        sem_repo.get_total_count.side_effect = Exception("Count error")
        
        service = AnalyzeService(sem_repo)
        
        with pytest.raises(Exception) as exc_info:
            service.get_overview()
        
        assert "Count error" in str(exc_info.value)
        sem_repo.get_quality_stats.assert_not_called()
