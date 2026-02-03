"""
推荐服务 - 封装音乐推荐的业务逻辑
"""

import random
import math
from typing import Dict, Any, List, Optional

from config.settings import RECOMMEND_CONFIG, WEIGHT_CONFIG, ALGORITHM_CONFIG
from config.constants import ALLOWED_LABELS
from src.repositories.user_repository import UserRepository
from src.repositories.semantic_repository import SemanticRepository
from src.repositories.song_repository import SongRepository
from .profile_service import ProfileService


class RecommendService:
    """推荐服务类"""

    def __init__(
        self,
        user_repo: UserRepository,
        sem_repo: SemanticRepository,
        song_repo: SongRepository,
        profile_service: ProfileService
    ):
        """
        初始化推荐服务

        Args:
            user_repo: 用户数据仓库
            sem_repo: 语义数据仓库
            song_repo: 歌曲数据仓库
            profile_service: 用户画像服务
        """
        self.user_repo = user_repo
        self.sem_repo = sem_repo
        self.song_repo = song_repo
        self.profile_service = profile_service

    def _calculate_similarity(
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
        tag_weights = RECOMMEND_CONFIG.get('tag_weights', {})

        # 分别计算各维度的匹配度
        mood_match = 0.0
        energy_match = 0.0
        genre_match = 0.0
        region_match = 0.0

        # Mood 维度
        for tag in ALLOWED_LABELS['mood']:
            if tag in user_profile.get('mood', {}) and song_tags.get('mood') == tag:
                mood_match += user_profile['mood'][tag]

        # Energy 维度
        for tag in ALLOWED_LABELS['energy']:
            if tag in user_profile.get('energy', {}) and song_tags.get('energy') == tag:
                energy_match += user_profile['energy'][tag]

        # Genre 维度
        for tag in ALLOWED_LABELS['genre']:
            if tag in user_profile.get('genre', {}) and song_tags.get('genre') == tag:
                genre_match += user_profile['genre'][tag]

        # Region 维度
        for tag in ALLOWED_LABELS['region']:
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

    def _apply_diversity(
        self,
        candidates: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        应用多样性控制

        Args:
            candidates: 候选歌曲列表
            limit: 返回数量限制

        Returns:
            多样化后的歌曲列表
        """
        if not candidates:
            return []

        # 按相似度排序
        sorted_candidates = sorted(candidates, key=lambda x: x.get('similarity', 0), reverse=True)

        # 使用贪心算法选择多样化的歌曲
        selected = []
        used_artists = set()
        used_genres = set()

        for song in sorted_candidates:
            if len(selected) >= limit:
                break

            artist = song.get('artist')
            genre = song.get('genre')

            # 检查多样性约束
            artist_count = sum(1 for s in selected if s.get('artist') == artist)
            genre_count = sum(1 for s in selected if s.get('genre') == genre)

            if artist_count < RECOMMEND_CONFIG.get('max_same_artist', 3) and \
               genre_count < RECOMMEND_CONFIG.get('max_same_genre', 5):
                selected.append(song)
                used_artists.add(artist)
                used_genres.add(genre)

        # 如果数量不足，从剩余候选中补充
        if len(selected) < limit:
            remaining = [s for s in sorted_candidates if s not in selected]
            selected.extend(remaining[:limit - len(selected)])

        return selected

    def recommend(
        self,
        user_id: str,
        limit: int = 30,
        filter_recent: bool = True,
        diversity: bool = True
    ) -> List[Dict[str, Any]]:
        """
        生成个性化推荐

        Args:
            user_id: 用户ID
            limit: 推荐数量
            filter_recent: 是否过滤最近听过的歌曲
            diversity: 是否启用多样性控制

        Returns:
            推荐歌曲列表
        """
        # 1. 构建用户画像
        user_profile = self.profile_service.build_user_profile(user_id)

        # 2. 获取用户歌曲（用于过滤）
        user_songs = self.user_repo.get_user_songs(user_id)

        # 3. 获取所有候选歌曲
        all_songs = self.sem_repo.get_all_songs()

        # 4. 计算每首歌的相似度
        candidates = []
        for song in all_songs:
            # 过滤用户已听过的歌曲
            if filter_recent and song['file_id'] in user_songs:
                continue

            # 计算相似度
            song_tags = {
                'mood': song.get('mood'),
                'energy': song.get('energy'),
                'genre': song.get('genre'),
                'region': song.get('region')
            }

            score = self._calculate_similarity(song_tags, user_profile.get('profile', {}))

            # 添加随机扰动
            randomness = ALGORITHM_CONFIG.get('randomness', 0.1)
            if randomness > 0:
                score *= (1 + random.uniform(-randomness, randomness))

            candidates.append({
                'file_id': song['file_id'],
                'title': song['title'],
                'artist': song['artist'],
                'album': song['album'],
                'mood': song.get('mood'),
                'energy': song.get('energy'),
                'genre': song.get('genre'),
                'region': song.get('region'),
                'confidence': song.get('confidence'),
                'similarity': score
            })

        # 5. 应用多样性控制
        if diversity:
            recommendations = self._apply_diversity(candidates, limit)
        else:
            recommendations = sorted(candidates, key=lambda x: x.get('similarity', 0), reverse=True)[:limit]

        # 6. 获取完整歌曲信息
        file_ids = [r['file_id'] for r in recommendations]
        full_songs = self.song_repo.get_songs_with_tags(file_ids)

        # 合并相似度分数
        song_map = {s['id']: s for s in full_songs}
        for rec in recommendations:
            if rec['file_id'] in song_map:
                rec.update(song_map[rec['file_id']])

        return recommendations

    def get_user_songs(self, user_id: str) -> List[str]:
        """
        获取用户相关的歌曲ID列表

        Args:
            user_id: 用户ID

        Returns:
            歌曲ID列表
        """
        return self.user_repo.get_user_songs(user_id)
