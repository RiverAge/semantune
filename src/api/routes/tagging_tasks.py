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


import sys


def run_tagging_task_sync():
    """
    后台任务的同步实现（在线程中运行）
    """
    logger.info("=" * 60)
    logger.info("标签生成任务开始执行")
    logger.info("=" * 60)
    sys.stderr.flush()

    try:
        with dbs_context() as (nav_conn, sem_conn):
            init_semantic_db(sem_conn)

            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)
            tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)

            orphan_count = tagging_service.cleanup_orphans()
            if orphan_count > 0:
                logger.info(f"后台任务：已清理 {orphan_count} 个孤儿标签")
                sys.stderr.flush()

            nav_songs = nav_repo.get_all_songs()
            logger.info(f"从 Navidrome 获取到 {len(nav_songs)} 首歌曲")
            sys.stderr.flush()

            processed_ids = set()
            cursor = sem_conn.execute("SELECT file_id FROM music_semantic")
            for row in cursor.fetchall():
                processed_ids.add(row[0])

            todo_songs = [s for s in nav_songs if s['id'] not in processed_ids]

            update_tagging_progress(total=len(todo_songs))
            logger.info(f"待处理歌曲数: {len(todo_songs)}")
            sys.stderr.flush()

            if len(todo_songs) == 0:
                update_tagging_progress(status="completed")
                logger.info("没有需要处理的歌曲")
                sys.stderr.flush()
                return

        with dbs_context() as (nav_conn, sem_conn):
            tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)

            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)

            all_songs = nav_repo.get_all_songs()

            tagged_ids = set()
            cursor = sem_conn.execute("SELECT file_id FROM music_semantic")
            for row in cursor.fetchall():
                tagged_ids.add(row[0])

            untagged_songs = [s for s in all_songs if s['id'] not in tagged_ids]

            processed = 0
            failed = 0

            from .tagging_sse import get_tagging_progress

            for idx, song in enumerate(untagged_songs, 1):
                progress = get_tagging_progress()

                if progress["status"] == "stopped":
                    logger.info("标签生成任务已被中止")
                    update_tagging_progress(status="stopped")
                    sys.stderr.flush()
                    return

                try:
                    logger.info(f"[{idx}/{len(untagged_songs)}] 正在处理: {song['title']} - {song['artist']}")
                    sys.stderr.flush()

                    result = tagging_service.generate_tag(
                        title=song['title'],
                        artist=song['artist'],
                        album=song['album']
                    )

                    sem_repo.save_song_tags(
                        file_id=song['id'],
                        title=song['title'],
                        artist=song['artist'],
                        album=song['album'],
                        tags=result['tags'],
                        confidence=result['tags'].get('confidence', 0.0),
                        model=""
                    )
                    processed += 1
                    update_tagging_progress(processed=processed)
                    logger.info(f"[{idx}/{len(untagged_songs)}] ✓ 处理完成: {song['title']} - {song['artist']}")
                    sys.stderr.flush()
                except Exception as e:
                    logger.error(f"[{idx}/{len(untagged_songs)}] ✗ 处理失败: {song['title']} - {song['artist']} - {str(e)}", exc_info=True)
                    sys.stderr.flush()
                    failed += 1

            logger.info(f"处理完成: 总数={len(untagged_songs)}, 已标记={processed}, 失败={failed}")
            sys.stderr.flush()

        update_tagging_progress(status="completed")
        logger.info("=" * 60)
        logger.info("标签生成任务完成")
        logger.info("=" * 60)
        sys.stderr.flush()

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"标签生成任务失败: {e}")
        logger.error("=" * 60, exc_info=True)
        sys.stderr.flush()
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
