"""
标签生成后台任务模块 - 处理批量标签生成任务
"""

import logging
import os
from typing import List

from src.core.database import dbs_context
from src.core.schema import init_semantic_db
from src.repositories.navidrome_repository import NavidromeRepository
from src.repositories.semantic_repository import SemanticRepository
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger
from .tagging_sse import update_tagging_progress, broadcast_progress

# 从环境变量读取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logger = setup_logger("api", level=log_level, console_level=log_level)


def run_tagging_task_sync():
    """
    后台任务的同步实现（在线程中运行）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            init_semantic_db(sem_conn)

            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)
            tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)

            orphan_count = tagging_service.cleanup_orphans()
            if orphan_count > 0:
                logger.info(f"后台任务：已清理 {orphan_count} 个孤儿标签")

            nav_songs = nav_repo.get_all_songs()

            processed_ids = set()
            cursor = sem_conn.execute("SELECT file_id FROM music_semantic")
            for row in cursor.fetchall():
                processed_ids.add(row[0])

            todo_songs = [s for s in nav_songs if s['id'] not in processed_ids]

            update_tagging_progress(total=len(todo_songs))

            if len(todo_songs) == 0:
                update_tagging_progress(status="completed")
                logger.info("没有需要处理的歌曲")
                return

        with dbs_context() as (nav_conn, sem_conn):
            tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
            result = tagging_service.process_all_songs()

        update_tagging_progress(status="completed")
        logger.info(f"标签生成任务完成: {result}")

    except Exception as e:
        logger.error(f"标签生成任务失败: {e}")
        update_tagging_progress(status="failed")


async def run_tagging_task():
    """
    后台任务：处理所有未标签的歌曲
    在单独的线程中运行，避免阻塞事件循环
    """
    import asyncio
    await asyncio.to_thread(run_tagging_task_sync)


def process_batch_tags_sync(songs: List[dict]):
    """
    批量标签生成的同步实现（在线程中运行）

    Args:
        songs: 歌曲列表，每首歌曲包含 title, artist, album
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            init_semantic_db(sem_conn)

            for idx, song in enumerate(songs):
                try:
                    tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
                    result = tagging_service.generate_tag(
                        song["title"],
                        song["artist"],
                        song.get("album", "")
                    )

                    if result:
                        sem_conn.execute("""
                            INSERT OR REPLACE INTO music_semantic
                            (file_id, title, artist, album, mood, energy, genre, region, subculture, scene, confidence)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            f"song_{idx}",
                            song["title"],
                            song["artist"],
                            song.get("album", ""),
                            result['tags'].get("mood"),
                            result['tags'].get("energy"),
                            result['tags'].get("genre"),
                            result['tags'].get("region"),
                            result['tags'].get("subculture"),
                            result['tags'].get("scene"),
                            result['tags'].get("confidence", 0.0)
                        ))
                        sem_conn.commit()

                    update_tagging_progress(processed=idx + 1)

                except Exception as e:
                    logger.error(f"处理歌曲 {song['artist']} - {song['title']} 失败: {e}")
                    continue

            update_tagging_progress(status="completed")
            logger.info(f"批量标签生成完成，共处理 {len(songs)} 首歌曲")

    except Exception as e:
        logger.error(f"批量标签生成失败: {e}")
        update_tagging_progress(status="failed")


async def process_batch_tags(songs: List[dict]):
    """
    后台处理批量标签生成
    在单独的线程中运行，避免阻塞事件循环

    Args:
        songs: 歌曲列表，每首歌曲包含 title, artist, album
    """
    import asyncio
    await asyncio.to_thread(process_batch_tags_sync, songs)
