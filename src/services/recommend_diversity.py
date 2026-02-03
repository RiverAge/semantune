"""
推荐多样性控制模块 - 封装多样性控制逻辑
"""

from typing import List, Dict, Any

from config.settings import get_recommend_config


class DiversityController:
    """多样性控制器"""

    def apply_diversity(
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
        artist_count = {}
        album_count = {}

        recommend_config = get_recommend_config()
        max_per_artist = recommend_config.get('diversity_max_per_artist', 1)
        max_per_album = recommend_config.get('diversity_max_per_album', 1)

        for song in sorted_candidates:
            if len(selected) >= limit:
                break

            artist = song.get('artist')
            album = song.get('album')

            # 检查艺人约束
            if artist_count.get(artist, 0) >= max_per_artist:
                continue

            # 检查专辑约束（只使用专辑名称，不包含艺人）
            if album and album_count.get(album, 0) >= max_per_album:
                continue

            selected.append(song)
            artist_count[artist] = artist_count.get(artist, 0) + 1
            if album:
                album_count[album] = album_count.get(album, 0) + 1

        # 如果数量不足，从剩余候选中补充
        if len(selected) < limit:
            remaining = [s for s in sorted_candidates if s not in selected]
            selected.extend(remaining[:limit - len(selected)])

        return selected
