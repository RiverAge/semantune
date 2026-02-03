"""
查询 CLI 命令
"""

import logging
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

logger = setup_logger("cli", level=logging.INFO)


class QueryCLI:
    """查询命令行接口"""

    @staticmethod
    def main():
        """查询歌曲的主函数"""
        logger.info("🔍 查询歌曲...")

        try:
            query_service = ServiceFactory.create_query_service()

            # 显示可用场景
            logger.info("\n可用场景:")
            scenes = query_service.get_available_scenes()
            for idx, scene in enumerate(scenes, 1):
                logger.info(f"  {idx}. {scene}")

            # 让用户选择场景
            choice = int(input("\n请选择场景 (输入序号): ")) - 1
            scene_name = scenes[choice]

            logger.info(f"\n查询场景: {scene_name}")

            # 查询歌曲
            songs = query_service.query_by_scene_preset(scene_name, limit=20)

            # 显示结果
            logger.info(f"\n✅ 查询完成! 共 {len(songs)} 首歌曲\n")
            logger.info(f"{'#':<4} {'歌手':<20} {'歌曲':<30} {'标签':<25}")
            logger.info("-" * 80)

            for idx, song in enumerate(songs, 1):
                artist = (song['artist'][:18] + '..') if len(song['artist']) > 18 else song['artist']
                title = (song['title'][:28] + '..') if len(song['title']) > 28 else song['title']
                tags = f"{song.get('mood', 'N/A')}/{song.get('energy', 'N/A')}/{song.get('genre', 'N/A')}"
                logger.info(f"{idx:<4} {artist:<20} {title:<30} {tags:<25}")

            logger.info("-" * 80)

        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            raise
