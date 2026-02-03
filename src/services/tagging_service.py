"""
标签生成服务 - 封装 LLM 标签生成的业务逻辑
"""

from typing import Dict, Any, List

from config.settings import MODEL
from src.repositories.navidrome_repository import NavidromeRepository
from src.repositories.semantic_repository import SemanticRepository
from .llm_client import LLMClient


class TaggingService:
    """标签生成服务类"""

    def __init__(
        self,
        nav_repo: NavidromeRepository,
        sem_repo: SemanticRepository
    ):
        """
        初始化标签服务

        Args:
            nav_repo: Navidrome 数据仓库
            sem_repo: 语义数据仓库
        """
        self.nav_repo = nav_repo
        self.sem_repo = sem_repo
        self.llm_client = LLMClient()

    def generate_tag(self, title: str, artist: str, album: str = "") -> Dict[str, Any]:
        """
        为单首歌曲生成语义标签

        Args:
            title: 歌曲标题
            artist: 歌手名称
            album: 专辑名称

        Returns:
            包含标签和原始响应的字典
        """
        tags, raw_response = self.llm_client.call_llm_api(title, artist, album)

        if not tags:
            raise ValueError("标签生成失败")

        return {
            "title": title,
            "artist": artist,
            "album": album,
            "tags": tags,
            "raw_response": raw_response
        }

    def batch_generate_tags(self, songs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        批量生成标签

        Args:
            songs: 歌曲列表，每首歌包含 title, artist, album

        Returns:
            标签结果列表
        """
        results = []
        for song in songs:
            try:
                result = self.generate_tag(
                    title=song['title'],
                    artist=song['artist'],
                    album=song.get('album', '')
                )
                results.append({
                    "success": True,
                    "data": result
                })
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "song": song
                })
        return results

    def process_all_songs(self) -> Dict[str, Any]:
        """
        处理所有未标记的歌曲

        Returns:
            处理结果统计
        """
        # 获取所有歌曲
        all_songs = self.nav_repo.get_all_songs()
        total = len(all_songs)

        # 获取已标记的歌曲ID
        tagged_ids = set()
        cursor = self.sem_repo.sem_conn.execute("SELECT file_id FROM music_semantic")
        for row in cursor.fetchall():
            tagged_ids.add(row[0])

        # 筛选未标记的歌曲
        untagged_songs = [s for s in all_songs if s['id'] not in tagged_ids]

        processed = 0
        failed = 0

        for song in untagged_songs:
            try:
                result = self.generate_tag(
                    title=song['title'],
                    artist=song['artist'],
                    album=song['album']
                )

                # 保存到数据库
                self.sem_repo.save_song_tags(
                    file_id=song['id'],
                    title=song['title'],
                    artist=song['artist'],
                    album=song['album'],
                    tags=result['tags'],
                    confidence=result['tags'].get('confidence', 0.0),
                    model=MODEL
                )
                processed += 1
            except Exception:
                failed += 1

        return {
            "total": total,
            "tagged": len(tagged_ids),
            "processed": processed,
            "failed": failed,
            "remaining": len(untagged_songs) - processed - failed
        }

    def get_progress(self) -> Dict[str, Any]:
        """
        获取标签生成进度

        Returns:
            进度信息
        """
        total = self.nav_repo.get_total_count()
        tagged = self.sem_repo.get_total_count()

        return {
            "total": total,
            "tagged": tagged,
            "remaining": total - tagged,
            "percentage": round(tagged * 100.0 / total, 2) if total > 0 else 0
        }
