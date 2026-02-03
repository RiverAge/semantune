"""
推荐相似度计算模块 - 封装相似度计算逻辑
"""

import random
from typing import Dict, Any

from config.settings import get_recommend_config, get_algorithm_config
from config.constants import get_allowed_labels


class SimilarityCalculator:
    """相似度计算器"""

    def __init__(self):
        """初始化相似度计算器，缓存配置"""
        self._allowed_labels = get_allowed_labels()
        self._tag_weights = get_recommend_config().get('tag_weights', {})
        self._algorithm_config = get_algorithm_config()

    def calculate_similarity(
        self,
        song_tags: Dict[str, str],
        user_profile: Dict[str, Dict[str, float]]
    ) -> float:
        """
        计算加权相似度（拉开分布）

        Args:
            song_tags: 歌曲标签
            user_profile: 用户画像（权重已归一化到 0-1 范围）

        Returns:
            归一化后的相似度分数，范围 [0, 1]
        """
        tag_weights = self._tag_weights
        allowed_labels = self._allowed_labels

        # 分别计算各维度的匹配度
        mood_match = 0.0
        energy_match = 0.0
        genre_match = 0.0
        region_match = 0.0

        # Mood 维度
        for tag in allowed_labels.get('mood', set()):
            if tag in user_profile.get('mood', {}) and song_tags.get('mood') == tag:
                mood_match += user_profile['mood'][tag]

        # Energy 维度
        for tag in allowed_labels.get('energy', set()):
            if tag in user_profile.get('energy', {}) and song_tags.get('energy') == tag:
                energy_match += user_profile['energy'][tag]

        # Genre 维度
        for tag in allowed_labels.get('genre', set()):
            if tag in user_profile.get('genre', {}) and song_tags.get('genre') == tag:
                genre_match += user_profile['genre'][tag]

        # Region 维度
        for tag in allowed_labels.get('region', set()):
            if tag in user_profile.get('region', {}) and song_tags.get('region') == tag:
                region_match += user_profile['region'][tag]

        # 加权求和
        weighted_score = (
            mood_match * tag_weights.get('mood', 2.0) +
            energy_match * tag_weights.get('energy', 1.5) +
            genre_match * tag_weights.get('genre', 1.2) +
            region_match * tag_weights.get('region', 0.8)
        )

        # 归一化到 0-1 范围
        max_possible = (
            tag_weights.get('mood', 2.0) +
            tag_weights.get('energy', 1.5) +
            tag_weights.get('genre', 1.2) +
            tag_weights.get('region', 0.8)
        )

        return weighted_score / max_possible if max_possible > 0 else 0.0

    def apply_randomness(self, score: float) -> float:
        """
        应用随机扰动

        Args:
            score: 原始相似度分数

        Returns:
            应用随机扰动后的分数
        """
        randomness = self._algorithm_config.get('randomness', 0.1)
        if randomness > 0:
            score *= (1 + random.uniform(-randomness, randomness))
        return score
