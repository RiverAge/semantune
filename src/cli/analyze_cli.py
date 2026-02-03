"""
分析 CLI 命令
"""

from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

logger = setup_logger("cli", level=logging.INFO)


class AnalyzeCLI:
    """分析命令行接口"""

    @staticmethod
    def main():
        """分析数据的主函数"""
        logger.info("📊 分析数据...")

        try:
            analyze_service = ServiceFactory.create_analyze_service()

            # 获取概览
            overview = analyze_service.get_overview()
            logger.info(f"\n{'=' * 60}")
            logger.info(f"  数据概览")
            logger.info(f"{'=' * 60}")
            logger.info(f"  总歌曲数: {overview['total_songs']}")
            logger.info(f"  平均置信度: {overview['average_confidence']}")
            logger.info(f"  低置信度歌曲: {overview['low_confidence_count']} ({overview['low_confidence_percentage']}%)")

            # 获取分布分析
            fields = ['mood', 'energy', 'genre', 'region']
            for field in fields:
                distribution = analyze_service.get_distribution(field)
                logger.info(f"\n{'=' * 60}")
                logger.info(f"  {distribution['field_name']} 分布 (Top 10)")
                logger.info(f"{'=' * 60}")
                logger.info(f"{'标签':<15} {'数量':>8} {'占比':>8}")
                logger.info("-" * 35)

                for item in distribution['distribution'][:10]:
                    logger.info(f"{item['label']:<15} {item['count']:>8} {item['percentage']:>7}%")

            # 获取组合分析
            combinations = analyze_service.get_combinations()
            logger.info(f"\n{'=' * 60}")
            logger.info(f"  最常见的 Mood + Energy 组合 (Top 10)")
            logger.info(f"{'=' * 60}")
            logger.info(f"{'Mood':<12} {'Energy':<8} {'数量':>8} {'占比':>8}")
            logger.info("-" * 40)

            for combo in combinations['combinations'][:10]:
                logger.info(f"{combo['mood']:<12} {combo['energy']:<8} {combo['count']:>8} {combo['percentage']:>7}%")

            # 获取质量分析
            quality = analyze_service.get_quality_stats()
            logger.info(f"\n{'=' * 60}")
            logger.info(f"  数据质量分析")
            logger.info(f"{'=' * 60}")
            logger.info(f"{'字段':<15} {'空值数量':>10} {'占比':>8}")
            logger.info("-" * 35)

            for field, stats in quality['none_stats'].items():
                logger.info(f"{field:<15} {stats['count']:>10} {stats['percentage']:>7}%")

            logger.info(f"\n{'=' * 60}")
            logger.info(f"  分析完成!")
            logger.info(f"{'=' * 60}")

        except Exception as e:
            logger.error(f"❌ 分析失败: {e}")
            raise
