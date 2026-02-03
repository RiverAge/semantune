"""
推荐服务 - 封装音乐推荐的业务逻辑
"""

from typing import Dict, Any, List

from src.repositories.user_repository import UserRepository
from src.repositories.semantic_repository import SemanticRepository
from src.repositories.song_repository import SongRepository
from .profile_service import ProfileService
from .recommend_similarity import SimilarityCalculator
from .recommend_diversity import DiversityController


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
        self.similarity_calculator = SimilarityCalculator()
        self.diversity_controller = DiversityController()

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
        profile = user_profile.get('profile', {})

        # 2. 获取用户歌曲（用于过滤），转换为 set 以提高查找速度
        user_songs = set(self.user_repo.get_user_songs(user_id))

        # 3. 获取所有候选歌曲
        all_songs = self.sem_repo.get_all_songs()

        # 4. 计算每首歌的相似度
        candidates = []
        for song in all_songs:
            # 过滤用户已听过的歌曲（使用 set 查找，O(1) 复杂度）
            if filter_recent and song['file_id'] in user_songs:
                continue

            # 计算相似度
            song_tags = {
                'mood': song.get('mood'),
                'energy': song.get('energy'),
                'genre': song.get('genre'),
                'region': song.get('region')
            }

            score = self.similarity_calculator.calculate_similarity(song_tags, profile)

            # 添加随机扰动
            score = self.similarity_calculator.apply_randomness(score)

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
            recommendations = self.diversity_controller.apply_diversity(candidates, limit)
        else:
            recommendations = sorted(candidates, key=lambda x: x.get('similarity', 0), reverse=True)[:limit]

        # 6. 获取完整歌曲信息
        file_ids = [r['file_id'] for r in recommendations]
        full_songs = self.song_repo.get_songs_with_tags(file_ids)

        # 合并相似度分数 - 使用 file_id 作为键
        song_map = {s['file_id']: s for s in full_songs}
        for rec in recommendations:
            if rec['file_id'] in song_map:
                rec.update(song_map[rec['file_id']])
            else:
                # 如果没有找到完整信息，确保至少有基本字段
                rec.setdefault('mood', '未知')
                rec.setdefault('energy', '未知')
                rec.setdefault('genre', '未知')

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
