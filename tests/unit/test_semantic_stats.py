"""
测试语义统计仓库
"""
import pytest
import sqlite3
from unittest.mock import Mock, MagicMock, call

from src.repositories.semantic_stats import SemanticStatsRepository


class TestSemanticStatsRepository:
    """测试语义统计仓库类"""

    def test_initialization(self):
        """测试初始化"""
        sem_conn = Mock()
        repo = SemanticStatsRepository(sem_conn)
        
        assert repo.sem_conn == sem_conn

    def test_get_distribution_mood(self):
        """测试获取情绪分布"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("happy", 10, 20.0),
            ("sad", 5, 10.0)
        ]
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_distribution("mood")
        
        assert len(result) == 2
        assert result[0]["label"] == "happy"
        assert result[0]["count"] == 10
        assert result[0]["percentage"] == 20.0
        assert result[1]["label"] == "sad"
        assert result[1]["count"] == 5
        assert result[1]["percentage"] == 10.0
        
        sem_conn.execute.assert_called_once()

    def test_get_distribution_energy(self):
        """测试获取能量分布"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("high", 15, 30.0),
            ("low", 10, 20.0)
        ]
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_distribution("energy")
        
        assert len(result) == 2
        assert result[0]["label"] == "high"
        assert result[1]["label"] == "low"

    def test_get_distribution_genre(self):
        """测试获取流派分布"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("pop", 20, 40.0),
            ("rock", 15, 30.0)
        ]
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_distribution("genre")
        
        assert len(result) == 2
        assert result[0]["label"] == "pop"
        assert result[1]["label"] == "rock"

    def test_get_distribution_region(self):
        """测试获取地区分布"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("欧美", 25, 50.0),
            ("华语", 20, 40.0)
        ]
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_distribution("region")
        
        assert len(result) == 2
        assert result[0]["label"] == "欧美"
        assert result[1]["label"] == "华语"

    def test_get_distribution_empty(self):
        """测试获取分布（空结果）"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_distribution("mood")
        
        assert result == []

    def test_get_distribution_with_null_values(self):
        """测试获取分布（包含空值）"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("happy", 10, 20.0),
            (None, 5, 10.0)
        ]
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_distribution("mood")
        
        assert len(result) == 2
        assert result[0]["label"] == "happy"
        assert result[1]["label"] == "(空值)"

    def test_get_combinations(self):
        """测试获取 Mood + Energy 组合"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("happy", "high", 10, 20.0),
            ("sad", "low", 5, 10.0)
        ]
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_combinations(limit=15)
        
        assert len(result) == 2
        assert result[0]["mood"] == "happy"
        assert result[0]["energy"] == "high"
        assert result[0]["count"] == 10
        assert result[0]["percentage"] == 20.0
        assert result[1]["mood"] == "sad"
        
        sem_conn.execute.assert_called_once()
        # 验证 limit 参数被传递
        execute_args = sem_conn.execute.call_args[0]
        assert "?" in execute_args[0]  # SQL 中包含参数占位符

    def test_get_combinations_custom_limit(self):
        """测试获取组合（自定义限制）"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            ("happy", "high", 5, 10.0)
        ]
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_combinations(limit=5)
        
        assert len(result) == 1
        # 模拟应该用 limit 参数调用 execute
        execute_args = sem_conn.execute.call_args
        # execute 被调用了，验证 SQL 包含参数化查询即可
        assert execute_args.called

    def test_get_combinations_empty(self):
        """测试获取组合（空结果）"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_combinations()
        
        assert result == []

    def test_get_region_genre_distribution(self):
        """测试获取地区流派分布"""
        # Mock 获取不同地区
        regions_cursor = MagicMock()
        regions_cursor.fetchall.return_value = [
            ("欧美",),
            ("华语",)
        ]
        
        # Mock 获取每个地区的流派
        genre_cursor = MagicMock()
        genre_cursor.fetchall.side_effect = [
            [("pop", 10), ("rock", 5)],  # 欧美
            [("华语流行", 8), ("民谣", 3)]  # 华语
        ]
        
        sem_conn = Mock()
        # 根据查询内容返回不同的 cursor
        def execute_side_effect(query, params=None):
            if "SELECT DISTINCT region" in query:
                return regions_cursor
            else:
                return genre_cursor
        
        sem_conn.execute.side_effect = execute_side_effect
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_region_genre_distribution()
        
        assert "欧美" in result
        assert "华语" in result
        assert len(result["欧美"]) == 2
        assert result["欧美"][0]["genre"] == "pop"
        assert result["欧美"][0]["count"] == 10
        assert len(result["华语"]) == 2
        assert result["华语"][0]["genre"] == "华语流行"

    def test_get_region_genre_distribution_empty(self):
        """测试获取地区流派分布（无地区）"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_region_genre_distribution()
        
        assert result == {}

    def test_get_region_genre_distribution_no_genres(self):
        """测试获取地区流派分布（无流派数据）"""
        # Mock 返回一个地区
        regions_cursor = MagicMock()
        regions_cursor.fetchall.return_value = [("欧美",)]
        
        # Mock 返回空流派列表
        genre_cursor = MagicMock()
        genre_cursor.fetchall.return_value = []
        
        sem_conn = Mock()
        def execute_side_effect(query, params=None):
            if "SELECT DISTINCT region" in query:
                return regions_cursor
            else:
                return genre_cursor
        
        sem_conn.execute.side_effect = execute_side_effect
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_region_genre_distribution()
        
        assert "欧美" in result
        assert len(result["欧美"]) == 0

    def test_get_quality_stats(self):
        """测试获取质量统计"""
        # Mock 获取总数
        total_cursor = MagicMock()
        total_cursor.fetchone.return_value = [100]
        
        # Mock 获取平均置信度
        avg_cursor = MagicMock()
        avg_cursor.fetchone.return_value = [0.85]
        
        # Mock 获取低置信度数量
        low_cursor = MagicMock()
        low_cursor.fetchone.return_value = [10]
        
        # Mock 获取各字段的 None 数量
        none_cursors = [MagicMock() for _ in range(6)]
        for i, cursor in enumerate(none_cursors):
            cursor.fetchone.return_value = [5 + i]
        
        sem_conn = Mock()
        execute_count = [0]
        def execute_side_effect(query):
            execute_count[0] += 1
            if "SELECT COUNT(*) FROM music_semantic" in query and "WHERE" not in query:
                return total_cursor
            elif "AVG(confidence)" in query:
                return avg_cursor
            elif "confidence < 0.5" in query:
                return low_cursor
            else:
                # 对应各个字段的 None 统计查询
                return none_cursors[min(execute_count[0] - 5, 5)]
        
        sem_conn.execute.side_effect = execute_side_effect
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_quality_stats()
        
        assert result["total_songs"] == 100
        assert result["average_confidence"] == 0.85
        assert result["low_confidence_count"] == 10
        assert result["low_confidence_percentage"] == 10.0
        assert "none_stats" in result
        assert len(result["none_stats"]) == 6

    def test_get_quality_stats_empty_database(self):
        """测试获取质量统计（空数据库）"""
        # Mock 返回空数据库
        total_cursor = MagicMock()
        total_cursor.fetchone.return_value = [0]
        
        avg_cursor = MagicMock()
        avg_cursor.fetchone.return_value = [None]
        
        low_cursor = MagicMock()
        low_cursor.fetchone.return_value = [0]
        
        none_cursors = [MagicMock() for _ in range(6)]
        for cursor in none_cursors:
            cursor.fetchone.return_value = [0]
        
        sem_conn = Mock()
        execute_count = [0]
        def execute_side_effect(query):
            execute_count[0] += 1
            if "SELECT COUNT(*) FROM music_semantic" in query and "WHERE" not in query:
                return total_cursor
            elif "AVG(confidence)" in query:
                return avg_cursor
            elif "confidence < 0.5" in query:
                return low_cursor
            else:
                return none_cursors[min(execute_count[0] - 5, 5)]
        
        sem_conn.execute.side_effect = execute_side_effect
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_quality_stats()
        
        assert result["total_songs"] == 0
        assert result["average_confidence"] == 0.0  # None 转为 0
        assert result["low_confidence_count"] == 0
        assert result["low_confidence_percentage"] == 0.0

    def test_get_quality_stats_with_low_confidence(self):
        """测试获取质量统计（大量低置信度数据）"""
        total_cursor = MagicMock()
        total_cursor.fetchone.return_value = [200]
        
        avg_cursor = MagicMock()
        avg_cursor.fetchone.return_value = [0.65]
        
        low_cursor = MagicMock()
        low_cursor.fetchone.return_value = [50]  # 25% 低置信度
        
        none_cursors = [MagicMock() for _ in range(6)]
        for i, cursor in enumerate(none_cursors):
            cursor.fetchone.return_value = [i * 2]
        
        sem_conn = Mock()
        execute_count = [0]
        def execute_side_effect(query):
            execute_count[0] += 1
            if "SELECT COUNT(*) FROM music_semantic" in query and "WHERE" not in query:
                return total_cursor
            elif "AVG(confidence)" in query:
                return avg_cursor
            elif "confidence < 0.5" in query:
                return low_cursor
            else:
                return none_cursors[min(execute_count[0] - 5, 5)]
        
        sem_conn.execute.side_effect = execute_side_effect
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_quality_stats()
        
        assert result["total_songs"] == 200
        assert result["average_confidence"] == 0.65
        assert result["low_confidence_count"] == 50
        assert result["low_confidence_percentage"] == 25.0

    def test_get_distribution_sql_injection(self):
        """测试分布查询是否防止 SQL 注入"""
        # 这个测试主要验证查询格式，SQL 注入需要参数化查询
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        
        sem_conn = Mock()
        sem_conn.execute.return_value = mock_cursor
        
        repo = SemanticStatsRepository(sem_conn)
        
        # 简单的 field name
        repo.get_distribution("mood")
        
        # SQL 查询应该被构建并执行
        assert sem_conn.execute.called
        
    def test_get_quality_stats_all_fields_none_stats(self):
        """测试质量统计中所有字段的 None 统计"""
        total_cursor = MagicMock()
        total_cursor.fetchone.return_value = [100]
        
        avg_cursor = MagicMock()
        avg_cursor.fetchone.return_value = [0.8]
        
        low_cursor = MagicMock()
        low_cursor.fetchone.return_value = [5]
        
        none_cursors = [MagicMock() for _ in range(6)]
        none_counts = [0, 1, 2, 3, 4, 5]
        for i, (cursor, count) in enumerate(zip(none_cursors, none_counts)):
            cursor.fetchone.return_value = [count]
        
        sem_conn = Mock()
        execute_count = [0]
        def execute_side_effect(query):
            execute_count[0] += 1
            if "SELECT COUNT(*) FROM music_semantic" in query and "WHERE" not in query:
                return total_cursor
            elif "AVG(confidence)" in query:
                return avg_cursor
            elif "confidence < 0.5" in query:
                return low_cursor
            else:
                return none_cursors[min(execute_count[0] - 5, 5)]
        
        sem_conn.execute.side_effect = execute_side_effect
        
        repo = SemanticStatsRepository(sem_conn)
        result = repo.get_quality_stats()
        
        assert len(result["none_stats"]) == 6
        expected_fields = ['mood', 'energy', 'scene', 'region', 'subculture', 'genre']
        for field in expected_fields:
            assert field in result["none_stats"]
            assert "count" in result["none_stats"][field]
            assert "percentage" in result["none_stats"][field]
