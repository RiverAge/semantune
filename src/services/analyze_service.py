"""
分析服务 - 封装数据分析的业务逻辑
"""

from typing import Dict, Any, List

from src.repositories.semantic_repository import SemanticRepository


class AnalyzeService:
    """分析服务类"""

    def __init__(self, sem_repo: SemanticRepository):
        """
        初始化分析服务

        Args:
            sem_repo: 语义数据仓库
        """
        self.sem_repo = sem_repo

    def get_distribution(self, field: str) -> Dict[str, Any]:
        """
        获取指定字段的分布分析

        Args:
            field: 字段名称 (mood, energy, genre, region, scene, subculture)

        Returns:
            分布分析结果
        """
        valid_fields = ['mood', 'energy', 'genre', 'region', 'scene', 'subculture']
        if field not in valid_fields:
            raise ValueError(f"无效的字段，可用字段: {', '.join(valid_fields)}")

        distribution = self.sem_repo.get_distribution(field)

        return {
            "field": field,
            "field_name": field.capitalize(),
            "distribution": distribution
        }

    def get_combinations(self) -> Dict[str, Any]:
        """
        获取最常见的 Mood + Energy 组合

        Returns:
            组合分析结果
        """
        combinations = self.sem_repo.get_combinations()

        return {
            "combinations": combinations
        }

    def get_region_genre_distribution(self) -> Dict[str, Any]:
        """
        获取各地区流派分布

        Returns:
            地区流派分布结果
        """
        regions = self.sem_repo.get_region_genre_distribution()

        return {
            "regions": regions
        }

    def get_quality_stats(self) -> Dict[str, Any]:
        """
        获取数据质量统计

        Returns:
            质量统计结果
        """
        return self.sem_repo.get_quality_stats()

    def get_overview(self) -> Dict[str, Any]:
        """
        获取数据概览

        Returns:
            数据概览结果
        """
        total = self.sem_repo.get_total_count()
        quality = self.sem_repo.get_quality_stats()

        return {
            "total_songs": total,
            "average_confidence": quality["average_confidence"],
            "low_confidence_count": quality["low_confidence_count"],
            "low_confidence_percentage": quality["low_confidence_percentage"]
        }
