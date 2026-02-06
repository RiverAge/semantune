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
        song_tags: Dict[str, Any],
        user_profile: Dict[str, Dict[str, float]]
    ) -> float:
        """
        计算加权相似度（动态维度）

        Args:
            song_tags: 歌曲标签（支持数组和单值）
            user_profile: 用户画像（权重已归一化到 0-1 范围）

        Returns:
            归一化后的相似度分数，范围 [0, 1]
        """
        tag_weights = self._tag_weights
        allowed_labels = self._allowed_labels

        # 数组字段配置
        array_fields = {'mood', 'genre', 'style', 'scene'}

        # 分别计算各维度的匹配度（动态维度）
        dimension_matches = {}

        for dimension in allowed_labels.keys():
            dimension_match = 0.0
            song_value = song_tags.get(dimension)

            if song_value is None or (isinstance(song_value, str) and song_value == 'None'):
                dimension_matches[dimension] = 0.0
                continue

            # 处理数组字段
            if dimension in array_fields:
                if isinstance(song_value, list):
                    for tag in song_value:
                        if tag in user_profile.get(dimension, {}):
                            dimension_match += user_profile[dimension][tag]
                else:
                    if song_value in user_profile.get(dimension, {}):
                        dimension_match += user_profile[dimension][song_value]
            # 处理单值字段
            else:
                if song_value in user_profile.get(dimension, {}):
                    dimension_match += user_profile[dimension][song_value]

            dimension_matches[dimension] = dimension_match

        # 加权求和
        weighted_score = 0.0
        max_possible = 0.0

        for dimension, match in dimension_matches.items():
            weight = tag_weights.get(dimension, 1.0)
            weighted_score += match * weight
            max_possible += weight

        # 归一化到 0-1 范围
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
