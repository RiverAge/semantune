"""
推荐 CLI 命令
"""

import logging
from src.services.service_factory import ServiceFactory
from src.core.database import nav_db_context
from src.repositories.user_repository import UserRepository
from src.utils.logger import setup_logger

logger = setup_logger("cli", level=logging.INFO)


class RecommendCLI:
    """推荐命令行接口"""

    @staticmethod
    def main():
        """生成个性化推荐的主函数"""
        logger.info("🎯 生成个性化推荐...")

        try:
            # 获取用户ID
            with nav_db_context() as nav_conn:
                user_repo = UserRepository(nav_conn)
                users = user_repo.get_all_users()

                if not users:
                    logger.error("❌ 未找到用户")
                    return

                # 如果只有一个用户，自动选择
                if len(users) == 1:
                    user_id = users[0]['id']
                    user_name = users[0]['name']
                else:
                    # 让用户选择
                    logger.info("\n可用用户:")
                    for idx, user in enumerate(users, 1):
                        logger.info(f"  {idx}. {user['name']} ({user['id']})")

                    choice = int(input("\n请选择用户 (输入序号): ")) - 1
                    user_id = users[choice]['id']
                    user_name = users[choice]['name']

            logger.info(f"\n为用户 {user_name} 生成推荐...")

            # 生成推荐
            recommend_service = ServiceFactory.create_recommend_service()
            recommendations = recommend_service.recommend(
                user_id=user_id,
                limit=30,
                filter_recent=True,
                diversity=True
            )

            # 显示推荐结果
            logger.info(f"\n✅ 推荐完成! 共 {len(recommendations)} 首歌曲\n")
            logger.info(f"{'#':<4} {'歌手':<20} {'歌曲':<30} {'标签':<25}")
            logger.info("-" * 80)

            for idx, song in enumerate(recommendations, 1):
                artist = (song['artist'][:18] + '..') if len(song['artist']) > 18 else song['artist']
                title = (song['title'][:28] + '..') if len(song['title']) > 28 else song['title']
                tags = f"{song.get('mood', 'N/A')}/{song.get('energy', 'N/A')}/{song.get('genre', 'N/A')}"
                logger.info(f"{idx:<4} {artist:<20} {title:<30} {tags:<25}")

            logger.info("-" * 80)

        except Exception as e:
            logger.error(f"❌ 推荐失败: {e}")
            raise
