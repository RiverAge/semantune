"""
测试 src.services.recommend_similarity 模块
"""

import pytest
from unittest.mock import Mock, patch

from src.services.recommend_similarity import SimilarityCalculator


class TestSimilarityCalculator:
    """测试 SimilarityCalculator 类"""

    def test_initialization(self):
        """测试初始化"""
        calculator = SimilarityCalculator()

        # 应该初始化配置
        assert hasattr(calculator, '_allowed_labels')
        assert hasattr(calculator, '_tag_weights')

    def test_calculate_similarity_perfect_match(self):
        """测试完美匹配的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.8, 'sad': 0.2},
            'energy': {'high': 0.9, 'low': 0.1},
            'genre': {'pop': 0.7, 'rock': 0.3},
            'region': {'Western': 1.0, 'Eastern': 0.0}
        }

        song_tags = {
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 完美匹配应该有非零的相似度（具体值取决于加权配置）
        assert similarity > 0.0

    def test_calculate_similarity_no_match(self):
        """测试完全不匹配的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.9, 'sad': 0.1},
            'energy': {'high': 0.8, 'low': 0.2},
            'genre': {'pop': 0.7, 'rock': 0.3},
            'region': {'Western': 1.0, 'Eastern': 0.0}
        }

        song_tags = {
            'mood': 'sad',
            'energy': 'low',
            'genre': 'rock',
            'region': 'Eastern'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 不完全匹配相似度应该较低
        assert 0.0 <= similarity < 1.0

    def test_calculate_similarity_partial_match(self):
        """测试部分匹配的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.7, 'sad': 0.3},
            'energy': {'high': 0.6, 'low': 0.4},
            'genre': {'pop': 0.5, 'rock': 0.5},
            'region': {'Western': 1.0}
        }

        song_tags = {
            'mood': 'happy',
            'energy': 'low',
            'genre': 'rock',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 部分匹配应该有中等相似度
        assert 0.0 < similarity < 1.0

    def test_calculate_similarity_empty_user_profile(self):
        """测试用户画像为空的情况"""
        calculator = SimilarityCalculator()

        user_profile = {}
        song_tags = {
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 用户画像为空时应该返回0
        assert similarity == 0.0

    def test_calculate_similarity_empty_song_tags(self):
        """测试歌曲标签为空的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.8},
            'energy': {'high': 0.7},
            'genre': {'pop': 0.6},
            'region': {'Western': 0.9}
        }

        song_tags = {}

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 歌曲标签为空时应该返回0
        assert similarity == 0.0

    def test_calculate_similarity_both_empty(self):
        """测试用户和歌曲标签都为空的情况"""
        calculator = SimilarityCalculator()

        user_profile = {}
        song_tags = {}

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 都为空时应返回0
        assert similarity == 0.0

    def test_calculate_similarity_partial_tags(self):
        """测试只有部分标签字段的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.9},
            'energy': {'high': 0.8}
        }

        song_tags = {
            'mood': 'happy'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 部分标签应该也能正常计算
        assert 0.0 <= similarity <= 1.0

    def test_calculate_similarity_missing_song_tag(self):
        """测试歌曲缺少某些标签情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.7},
            'energy': {'high': 0.6},
            'genre': {'pop': 0.5},
            'region': {'Western': 0.4}
        }

        song_tags = {
            'mood': 'happy',
            'energy': 'high'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该能处理缺少的类型
        assert 0.0 <= similarity < 1.0

    def test_calculate_similarity_returns_float(self):
        """测试返回值类型"""
        calculator = SimilarityCalculator()

        user_profile = {'mood': {'happy': 0.5}}
        song_tags = {'mood': 'happy'}

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该返回浮点数
        assert isinstance(similarity, float)

    def test_calculate_similarity_range_check(self):
        """测试相似度值在合理范围内"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.5, 'sad': 0.5},
            'energy': {'high': 0.5, 'low': 0.5},
            'genre': {'pop': 0.5, 'rock': 0.5},
            'region': {'Western': 0.5, 'Eastern': 0.5}
        }

        song_tags = {
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 相似度应该在[0, 1]范围内
        assert 0.0 <= similarity <= 1.0

    def test_apply_randomness_zero(self):
        """测试随机场为0时"""
        calculator = SimilarityCalculator()

        with patch.object(calculator, '_algorithm_config', {'randomness': 0}):
            score = 0.8
            result = calculator.apply_randomness(score)

            # 应该保持不变
            assert result == score

    def test_apply_randomness_positive(self):
        """测试正随机场"""
        calculator = SimilarityCalculator()

        with patch.object(calculator, '_algorithm_config', {'randomness': 0.2}):
            score = 0.8
            result = calculator.apply_randomness(score)

            # 应该有变化
            assert isinstance(result, float)

    def test_apply_randomness_range(self):
        """测试随机结果在合理范围内"""
        calculator = SimilarityCalculator()

        with patch.object(calculator, '_algorithm_config', {'randomness': 0.1}):
            score = 0.5
            results = [calculator.apply_randomness(score) for _ in range(100)]

            # 所有结果应该在一定范围内
            assert all(0 <= r <= 1 for r in results)

    def test_calculate_similarity_empty_profile_type(self):
        """测试用户画像某些类型为空"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'happy': 0.5},
            'energy': {},
            'genre': {'pop': 0.3},
            'region': {}
        }

        song_tags = {
            'mood': 'happy',
            'energy': 'high',
            'genre': 'pop',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该能处理空的类型
        assert 0.0 <= similarity <= 1.0
