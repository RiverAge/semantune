"""
标签生成服务 - 封装 LLM 标签生成的业务逻辑
"""

from typing import Dict, Any, List, Optional
import logging
import json

from config.settings import get_model
from src.repositories.navidrome_repository import NavidromeRepository
from src.repositories.semantic_repository import SemanticRepository
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


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

    def generate_tag(self, title: str, artist: str, album: str = "", lyrics: Optional[str] = None) -> Dict[str, Any]:
        """
        为单首歌曲生成语义标签

        Args:
            title: 歌曲标题
            artist: 歌手名称
            album: 专辑名称
            lyrics: 歌词文本（可选）

        Returns:
            包含标签和原始响应的字典
        """
        tags, raw_response = self.llm_client.call_llm_api(title, artist, album, lyrics)

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
            songs: 歌曲列表，每首歌包含 title, artist, album, lyrics (可选)

        Returns:
            标签结果列表
        """
        results = []
        for idx, song in enumerate(songs, 1):
            try:
                result = self.generate_tag(
                    title=song['title'],
                    artist=song['artist'],
                    album=song.get('album', ''),
                    lyrics=song.get('lyrics')
                )
                results.append({
                    "success": True,
                    "data": result
                })
            except Exception as e:
                logger.error(f"生成标签失败 [{idx}/{len(songs)}]: {song.get('title', '')} - {song.get('artist', '')} - {str(e)}", exc_info=True)
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
        validation_failed = 0

        for idx, song in enumerate(untagged_songs, 1):
            try:
                lyrics = self.nav_repo.extract_lyrics_text(song.get('lyrics'))
                result = self.generate_tag(
                    title=song['title'],
                    artist=song['artist'],
                    album=song['album'],
                    lyrics=lyrics
                )

                # 使用带验证的保存方法
                is_valid, validation_result = self.sem_repo.save_song_tags_with_validation(
                    file_id=song['id'],
                    title=song['title'],
                    artist=song['artist'],
                    album=song['album'],
                    tags=result['tags'],
                    confidence=result['tags'].get('confidence', 0.0),
                    model=get_model()
                )

                if is_valid:
                    processed += 1
                    logger.info(f"处理进度 [{idx}/{len(untagged_songs)}]: {song['title']} - {song['artist']} - VALID")
                else:
                    validation_failed += 1
                    invalid_tags_str = json.dumps(validation_result['invalid_tags'], ensure_ascii=False)
                    logger.warning(f"处理进度 [{idx}/{len(untagged_songs)}]: {song['title']} - {song['artist']} - INVALID - 违规标签: {invalid_tags_str}")
            except Exception as e:
                logger.error(f"处理歌曲失败 [{idx}/{len(untagged_songs)}]: {song['title']} - {song['artist']} - {str(e)}", exc_info=True)
                failed += 1

        logger.info(f"处理完成: 总数={total}, 已标记={len(tagged_ids)}, 本次处理={processed}, 验证失败={validation_failed}, 失败={failed}, 剩余={len(untagged_songs) - processed - validation_failed - failed}")

        return {
            "total": total,
            "tagged": len(tagged_ids),
            "processed": processed,
            "validation_failed": validation_failed,
            "failed": failed,
            "remaining": len(untagged_songs) - processed - validation_failed - failed
        }

    def cleanup_orphans(self) -> int:
        """
        清理孤儿标签（删除在 Semantune 库中存在但在 Navidrome 库中已删除的歌曲）

        Returns:
            清理的记录数量
        """
        # 获取 Semantune 中所有的 file_id
        cursor = self.sem_repo.sem_conn.execute("SELECT file_id FROM music_semantic")
        sem_ids = {row[0] for row in cursor.fetchall()}

        if not sem_ids:
            return 0

        # 获取 Navidrome 中所有的歌曲 ID
        nav_songs = self.nav_repo.get_all_songs()
        nav_ids = {s['id'] for s in nav_songs}

        # 找出在 Semantune 中但不在 Navidrome 中的 ID
        orphan_ids = list(sem_ids - nav_ids)

        if orphan_ids:
            logger.info(f"发现 {len(orphan_ids)} 个孤儿标签，正在清理...")
            count = self.sem_repo.delete_songs_by_ids(orphan_ids)
            logger.info(f"成功清理 {count} 个孤儿标签")
            return count
        
        return 0

    def get_progress(self) -> Dict[str, Any]:
        """
        获取标签生成进度

        Returns:
            进度信息
        """
        nav_songs = self.nav_repo.get_all_songs()
        total = len(nav_songs)
        nav_ids = set(s['id'] for s in nav_songs)

        cursor = self.sem_repo.sem_conn.execute("SELECT file_id FROM music_semantic")
        sem_ids = {row[0] for row in cursor.fetchall()}

        tagged = len(nav_ids & sem_ids)
        remaining = len(nav_ids - sem_ids)

        return {
            "total": total,
            "tagged": tagged,
            "remaining": remaining,
            "percentage": round(tagged * 100.0 / total, 2) if total > 0 else 0
        }
