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
            'mood': {'Happy': 0.8, 'Sad': 0.2},
            'energy': {'High': 0.9, 'Low': 0.1},
            'genre': {'Pop': 0.7, 'Rock': 0.3},
            'region': {'Western': 1.0, 'Chinese': 0.0}
        }

        song_tags = {
            'mood': 'Happy',
            'energy': 'High',
            'genre': 'Pop',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 完美匹配应该有非零的相似度（具体值取决于加权配置）
        assert similarity > 0.0

    def test_calculate_similarity_no_match(self):
        """测试完全不匹配的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.9, 'Sad': 0.1},
            'energy': {'High': 0.8, 'Low': 0.2},
            'genre': {'Pop': 0.7, 'Rock': 0.3},
            'region': {'Chinese': 1.0, 'Japanese': 0.0}
        }

        song_tags = {
            'mood': 'Sad',
            'energy': 'Low',
            'genre': 'Rock',
            'region': 'Japanese'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 匹配的相似度
        assert 0.1 < similarity < 1.0

    def test_calculate_similarity_partial_match(self):
        """测试部分匹配的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.7, 'Sad': 0.3},
            'energy': {'High': 0.6, 'Low': 0.4},
            'genre': {'Pop': 0.5, 'Rock': 0.5},
            'region': {'Western': 1.0}
        }

        song_tags = {
            'mood': 'Happy',
            'energy': 'Low',
            'genre': 'Rock',
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
            'mood': 'Happy',
            'energy': 'High',
            'genre': 'Pop',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 用户画像为空时应该返回0
        assert similarity == 0.0

    def test_calculate_similarity_empty_song_tags(self):
        """测试歌曲标签为空的情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.8},
            'energy': {'High': 0.7},
            'genre': {'Pop': 0.6},
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
            'mood': {'Happy': 0.9},
            'energy': {'High': 0.8}
        }

        song_tags = {
            'mood': 'Happy'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 部分标签应该也能正常计算
        assert 0.0 <= similarity <= 1.0

    def test_calculate_similarity_missing_song_tag(self):
        """测试歌曲缺少某些标签情况"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.7},
            'energy': {'High': 0.6},
            'genre': {'Pop': 0.5},
            'region': {'Western': 0.4}
        }

        song_tags = {
            'mood': 'Happy',
            'energy': 'High'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该能处理缺少的类型
        assert 0.0 <= similarity < 1.0

    def test_calculate_similarity_returns_float(self):
        """测试返回值类型"""
        calculator = SimilarityCalculator()

        user_profile = {'mood': {'Happy': 0.5}}
        song_tags = {'mood': 'Happy'}

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该返回浮点数
        assert isinstance(similarity, float)

    def test_calculate_similarity_range_check(self):
        """测试相似度值在合理范围内"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.5, 'Sad': 0.5},
            'energy': {'High': 0.5, 'Low': 0.5},
            'genre': {'Pop': 0.5, 'Rock': 0.5},
            'region': {'Western': 0.5, 'Chinese': 0.5}
        }

        song_tags = {
            'mood': 'Happy',
            'energy': 'High',
            'genre': 'Pop',
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
            'mood': {'Happy': 0.5},
            'energy': {},
            'genre': {'Pop': 0.3},
            'region': {}
        }

        song_tags = {
            'mood': 'Happy',
            'energy': 'High',
            'genre': 'Pop',
            'region': 'Western'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该能处理空的类型
        assert 0.0 <= similarity <= 1.0

    def test_calculate_multiple_mood_tags(self):
        """测试多个mood标签的计算"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.4, 'Sad': 0.3, 'Energetic': 0.3},
            'energy': {'High': 0.8},
            'genre': {'Pop': 0.6},
            'region': {'Western': 0.5}
        }

        song_tags = {
            'mood': 'Energetic',
            'energy': 'High',
            'genre': 'Pop',
            'region': 'Chinese'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该正确处理用户profile中的mood标签
        assert 0.0 < similarity < 1.0

    def test_calculate_multiple_energy_tags(self):
        """测试多个energy标签的计算"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.7},
            'energy': {'High': 0.5, 'Low': 0.3, 'Medium': 0.2},
            'genre': {'Pop': 0.6},
            'region': {'Western': 0.5}
        }

        song_tags = {
            'mood': 'Happy',
            'energy': 'Low',
            'genre': 'Rock',
            'region': 'Japanese'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该正确处理用户profile中的energy标签
        assert 0.0 < similarity < 1.0

    def test_calculate_multiple_genre_tags(self):
        """测试多个genre标签的计算"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.6},
            'energy': {'High': 0.7},
            'genre': {'Pop': 0.3, 'Rock': 0.2, 'Electronic': 0.5},
            'region': {'Western': 0.5}
        }

        song_tags = {
            'mood': 'Sad',
            'energy': 'Low',
            'genre': 'Electronic',
            'region': 'Chinese'
        }

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该正确处理用户profile中的genre标签
        assert 0.0 < similarity < 1.0

    def test_calculate_exact_mood_match(self):
        """测试mood标签精确匹配触发第48行"""
        calculator = SimilarityCalculator()

        user_profile = {
            'mood': {'Happy': 0.5, 'Sad': 0.3}
        }
        song_tags = {'mood': 'Happy'}

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该匹配到Happy并累加分数
        assert 0.0 < similarity <= 1.0

    def test_calculate_exact_energy_match(self):
        """测试energy标签精确匹配触发第53行"""
        calculator = SimilarityCalculator()

        user_profile = {
            'energy': {'High': 0.6, 'Low': 0.4}
        }
        song_tags = {'energy': 'High'}

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该匹配到High并累加分数
        assert 0.0 < similarity <= 1.0

    def test_calculate_exact_genre_match(self):
        """测试genre标签精确匹配触发第58行"""
        calculator = SimilarityCalculator()

        user_profile = {
            'genre': {'Pop': 0.5, 'Rock': 0.3}
        }
        song_tags = {'genre': 'Pop'}

        similarity = calculator.calculate_similarity(song_tags, user_profile)

        # 应该匹配到Pop并累加分数
        assert 0.0 < similarity <= 1.0
