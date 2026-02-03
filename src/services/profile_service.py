"""
用户画像服务 - 封装用户画像构建的业务逻辑
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict
from datetime import datetime

from config.settings import WEIGHT_CONFIG
from config.constants import ALLOWED_LABELS, SECONDS_PER_DAY
from src.repositories.user_repository import UserRepository
from src.repositories.semantic_repository import SemanticRepository


class ProfileService:
    """用户画像服务类"""

    def __init__(
        self,
        user_repo: UserRepository,
        sem_repo: SemanticRepository
    ):
        """
        初始化用户画像服务

        Args:
            user_repo: 用户数据仓库
            sem_repo: 语义数据仓库
        """
        self.user_repo = user_repo
        self.sem_repo = sem_repo

    def _calculate_time_decay(self, play_date: float) -> float:
        """
        计算时间衰减系数

        Args:
            play_date: 播放时间的 Unix 时间戳

        Returns:
            衰减系数，范围 [min_decay, 1.0]
        """
        if not play_date:
            return WEIGHT_CONFIG['min_decay']

        now = time.time()
        days_ago = (now - play_date) / SECONDS_PER_DAY

        decay = max(
            WEIGHT_CONFIG['min_decay'],
            1.0 - days_ago / WEIGHT_CONFIG['time_decay_days']
        )

        return decay

    def _calculate_song_weight(self, play_data: Dict[str, Any], playlist_count: int) -> float:
        """
        计算单首歌的综合权重

        Args:
            play_data: 播放数据字典
            playlist_count: 该歌曲在歌单中出现的次数

        Returns:
            综合权重值
        """
        weight = 0.0

        # 1. 播放次数基础权重
        weight += play_data['play_count'] * WEIGHT_CONFIG['play_count']

        # 2. 收藏加分
        if play_data['starred']:
            weight += WEIGHT_CONFIG['starred']

        # 3. 歌单加分
        if playlist_count > 0:
            weight += WEIGHT_CONFIG['in_playlist'] * playlist_count

        # 4. 时间衰减
        decay = self._calculate_time_decay(play_data['play_date'])
        weight *= decay

        return weight

    def _get_tag_type(self, tag: str) -> Optional[str]:
        """
        获取标签类型

        Args:
            tag: 标签值

        Returns:
            标签类型 (mood, energy, genre, region)，如果不在任何类型中则返回 None
        """
        for tag_type, allowed_tags in ALLOWED_LABELS.items():
            if tag in allowed_tags:
                return tag_type
        return None

    def build_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        构建用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像字典
        """
        # 1. 获取播放历史
        play_history = self.user_repo.get_play_history(user_id)

        # 2. 获取歌单信息
        playlist_songs = self.user_repo.get_playlist_songs(user_id)

        # 3. 合并所有歌曲ID
        all_song_ids = set(play_history.keys()) | set(playlist_songs.keys())

        # 4. 计算标签权重
        tag_weights = defaultdict(float)
        processed = 0
        skipped = 0

        stats = {
            'total_plays': 0,
            'starred_count': 0,
            'playlist_songs': len(playlist_songs),
            'unique_songs': len(all_song_ids)
        }

        for song_id in all_song_ids:
            # 获取歌曲标签
            tags = self.sem_repo.get_song_tags(song_id)
            if not tags:
                skipped += 1
                continue

            # 获取播放数据
            play_data = play_history.get(song_id, {
                'play_count': 0,
                'starred': False,
                'play_date': 0
            })

            # 获取歌单数据
            playlist_count = playlist_songs.get(song_id, 0)

            # 计算权重
            weight = self._calculate_song_weight(play_data, playlist_count)

            # 累加标签权重
            for tag_type in ['mood', 'energy', 'genre', 'region']:
                tag_value = tags.get(tag_type)
                if tag_value and tag_value != 'None':
                    tag_weights[tag_value] += weight

            # 统计信息
            stats['total_plays'] += play_data['play_count']
            if play_data['starred']:
                stats['starred_count'] += 1

            processed += 1

        # 5. 归一化权重到 0-1 范围
        total_weight = sum(tag_weights.values())
        if total_weight > 0:
            normalized_weights = {
                tag: weight / total_weight
                for tag, weight in tag_weights.items()
            }
        else:
            normalized_weights = {}

        # 6. 按类型分组标签 - 确保所有类型都存在
        profile = {
            'mood': {},
            'energy': {},
            'genre': {},
            'region': {}
        }

        for tag, weight in normalized_weights.items():
            tag_type = self._get_tag_type(tag)
            if tag_type and tag_type in profile:
                profile[tag_type][tag] = weight

        # 7. 排序
        for category in profile:
            profile[category] = dict(sorted(
                profile[category].items(),
                key=lambda x: x[1],
                reverse=True
            ))

        return {
            'user_id': user_id,
            'profile': profile,
            'stats': stats,
            'generated_at': datetime.now().isoformat()
        }

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户画像（如果已存在则返回，否则构建）

        Args:
            user_id: 用户ID

        Returns:
            用户画像字典，如果用户不存在则返回 None
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return None

        return self.build_user_profile(user_id)
