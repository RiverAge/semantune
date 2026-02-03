"""
数据分析工具 - 分析语义标签数据
"""

import sys
import logging

from src.core.database import sem_db_context
from src.utils.common import setup_windows_encoding
from src.utils.logger import setup_logger

# 设置 Windows 控制台编码
setup_windows_encoding()

# 设置日志（使用统一的日志配置）
logger = setup_logger('analyze', level=logging.INFO)


def print_section(title: str) -> None:
    """打印分隔线"""
    logger.info("=" * 80)
    logger.info(f"  {title}")
    logger.info("=" * 80)


def analyze_distribution(conn, field: str, field_name: str) -> None:
    """分析某个字段的分布"""
    cursor = conn.execute(f"""
        SELECT {field}, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as percentage
        FROM music_semantic
        GROUP BY {field}
        ORDER BY count DESC
    """)

    logger.info(f"{field_name} 分布:")
    logger.info(f"{'标签':<15} {'数量':>8} {'占比':>8}")
    logger.info("-" * 35)

    for row in cursor:
        label = row[0] if row[0] else "(空值)"
        count = row[1]
        pct = row[2]
        logger.info(f"{label:<15} {count:>8} {pct:>7}%")


def analyze_combinations(conn) -> None:
    """分析常见的标签组合"""
    logger.info("最常见的 Mood + Energy 组合 (Top 15):")
    logger.info(f"{'Mood':<12} {'Energy':<8} {'数量':>8} {'占比':>8}")
    logger.info("-" * 40)

    cursor = conn.execute("""
        SELECT mood, energy, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as pct
        FROM music_semantic
        GROUP BY mood, energy
        ORDER BY count DESC
        LIMIT 15
    """)

    for row in cursor:
        logger.info(f"{row[0]:<12} {row[1]:<8} {row[2]:>8} {row[3]:>7}%")


def analyze_by_region(conn) -> None:
    """按地区分析流派分布"""
    logger.info("各地区的流派分布 (Top 5 per region):")

    regions = conn.execute("SELECT DISTINCT region FROM music_semantic WHERE region != 'None'").fetchall()

    for (region,) in regions:
        logger.info(f"  【{region}】")
        cursor = conn.execute("""
            SELECT genre, COUNT(*) as count
            FROM music_semantic
            WHERE region = ? AND genre != 'None'
            GROUP BY genre
            ORDER BY count DESC
            LIMIT 5
        """, (region,))

        for row in cursor:
            logger.info(f"    {row[0]:<15} {row[1]:>6} 首")


def analyze_quality(conn) -> None:
    """分析数据质量"""
    logger.info("数据质量指标:")

    # 总数
    total = conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]
    logger.info(f"  总歌曲数: {total}")

    # None 值统计
    none_stats = {}
    for field in ['mood', 'energy', 'scene', 'region', 'subculture', 'genre']:
        none_count = conn.execute(f"SELECT COUNT(*) FROM music_semantic WHERE {field} = 'None'").fetchone()[0]
        none_pct = round(none_count * 100.0 / total, 2)
        none_stats[field] = (none_count, none_pct)

    logger.info("  标签缺失情况 (标记为 'None' 的数量):")
    logger.info(f"  {'字段':<12} {'None数量':>10} {'占比':>8}")
    logger.info("  " + "-" * 35)
    for field, (count, pct) in none_stats.items():
        logger.info(f"  {field:<12} {count:>10} {pct:>7}%")

    # 平均置信度
    avg_conf = conn.execute("SELECT AVG(confidence) FROM music_semantic").fetchone()[0]
    logger.info(f"  平均置信度: {avg_conf:.4f}")

    # 低置信度歌曲
    low_conf = conn.execute("SELECT COUNT(*) FROM music_semantic WHERE confidence < 0.5").fetchone()[0]
    logger.info(f"  低置信度歌曲 (<0.5): {low_conf} ({round(low_conf*100.0/total, 2)}%)")


def show_samples(conn) -> None:
    """展示一些样本数据"""
    logger.info("随机样本 (10首):")
    logger.info(f"{'歌手':<15} {'歌曲':<25} {'Mood':<10} {'Energy':<8} {'Genre':<10}")
    logger.info("-" * 80)

    cursor = conn.execute("""
        SELECT artist, title, mood, energy, genre
        FROM music_semantic
        ORDER BY RANDOM()
        LIMIT 10
    """)

    for row in cursor:
        artist = (row[0][:12] + '..') if len(row[0]) > 12 else row[0]
        title = (row[1][:22] + '..') if len(row[1]) > 22 else row[1]
        logger.info(f"{artist:<15} {title:<25} {row[2]:<10} {row[3]:<8} {row[4]:<10}")


def main() -> None:
    """主函数"""
    with sem_db_context() as conn:
        print_section("语义标签数据分析报告")

        # 1. 数据质量
        print_section("1. 数据质量")
        analyze_quality(conn)

        # 2. 各维度分布
        print_section("2. 标签分布统计")
        analyze_distribution(conn, "mood", "情绪 (Mood)")
        analyze_distribution(conn, "energy", "能量 (Energy)")
        analyze_distribution(conn, "genre", "流派 (Genre)")
        analyze_distribution(conn, "region", "地区 (Region)")
        analyze_distribution(conn, "subculture", "亚文化 (Subculture)")
        analyze_distribution(conn, "scene", "场景 (Scene)")

        # 3. 组合分析
        print_section("3. 标签组合分析")
        analyze_combinations(conn)

        # 4. 地区流派分析
        print_section("4. 地区流派分析")
        analyze_by_region(conn)

        # 5. 样本展示
        print_section("5. 随机样本")
        show_samples(conn)

        logger.info("=" * 80)
        logger.info("  分析完成!")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
