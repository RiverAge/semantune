"""
标签生成 CLI 命令
"""

import logging
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

logger = setup_logger("cli", level=logging.INFO)


class TaggingCLI:
    """标签生成命令行接口"""

    @staticmethod
    def main():
        """生成语义标签的主函数"""
        logger.info("🏷️  生成语义标签...")

        try:
            tagging_service = ServiceFactory.create_tagging_service()
            result = tagging_service.process_all_songs()

            logger.info(f"✅ 标签生成完成!")
            logger.info(f"   总歌曲数: {result['total']}")
            logger.info(f"   已标记: {result['tagged']}")
            logger.info(f"   本次处理: {result['processed']}")
            logger.info(f"   失败: {result['failed']}")
            logger.info(f"   剩余: {result['remaining']}")

        except Exception as e:
            logger.error(f"❌ 标签生成失败: {e}")
            raise

    @staticmethod
    def preview():
        """预览标签生成"""
        logger.info("👁️  预览标签生成...")

        try:
            from src.core.database import nav_db_context
            from src.repositories.navidrome_repository import NavidromeRepository

            with nav_db_context() as nav_conn:
                nav_repo = NavidromeRepository(nav_conn)
                songs = nav_repo.get_all_songs()

            tagging_service = ServiceFactory.create_tagging_service()

            # 预览前 5 首歌曲
            for song in songs[:5]:
                try:
                    result = tagging_service.generate_tag(
                        song['title'],
                        song['artist'],
                        song.get('album', '')
                    )
                    logger.info(f"\n🎵 {song['artist']} - {song['title']}")
                    logger.info(f"   Mood: {result['tags'].get('mood')}")
                    logger.info(f"   Energy: {result['tags'].get('energy')}")
                    logger.info(f"   Genre: {result['tags'].get('genre')}")
                    logger.info(f"   Region: {result['tags'].get('region')}")
                    logger.info(f"   Confidence: {result['tags'].get('confidence')}")

                except Exception as e:
                    logger.error(f"   ❌ 生成失败: {e}")

        except Exception as e:
            logger.error(f"❌ 预览失败: {e}")
            raise
