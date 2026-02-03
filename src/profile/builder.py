"""
用户画像构建模块 - 基于播放历史、收藏和歌单分析用户音乐偏好
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, Optional

from config.settings import WEIGHT_CONFIG
from config.constants import ALLOWED_LABELS
from src.core.database import dbs_context
from src.utils.common import setup_windows_encoding
from src.utils.user import (
    get_user_id,
    get_play_history,
    get_playlist_songs,
    get_song_tags,
    calculate_time_decay,
    calculate_song_weight
)
from src.utils.logger import setup_logger

# 设置 Windows 控制台编码
setup_windows_encoding()

# 设置日志（使用统一的日志配置）
logger = setup_logger('profile', level=logging.INFO)


def build_user_profile(user_id: str) -> Dict[str, Any]:
    """构建用户画像"""
    with dbs_context() as (nav_conn, sem_conn):
        logger.info(f"正在构建用户画像...")
    logger.info("=" * 60)

    # 1. 获取播放历史
    logger.info("1. 读取播放历史...")
    play_history = get_play_history(nav_conn, user_id)
    logger.info(f"   找到 {len(play_history)} 首有播放记录的歌曲")

    # 2. 获取歌单信息
    logger.info("2. 读取歌单信息...")
    playlist_songs = get_playlist_songs(nav_conn, user_id)
    logger.info(f"   找到 {len(playlist_songs)} 首歌单中的歌曲")

    # 3. 合并所有歌曲ID
    all_song_ids = set(play_history.keys()) | set(playlist_songs.keys())
    logger.info(f"3. 合并数据...")
    logger.info(f"   总共 {len(all_song_ids)} 首独立歌曲")

    # 4. 计算标签权重
    logger.info("4. 计算标签权重...")
    tag_weights = defaultdict(float)
    processed = 0
    skipped = 0

    stats = {
        'total_plays': 0,
        'starred_count': 0,
        'playlist_songs': len(playlist_songs),
        'unique_songs': len(all_song_ids)
    }

    for song_id in all_song_ids:
        # 获取歌曲标签
        tags = get_song_tags(sem_conn, song_id)
        if not tags:
            skipped += 1
            continue

        # 获取播放数据
        play_data = play_history.get(song_id, {
            'play_count': 0,
            'starred': False,
            'play_date': 0
        })

        # 获取歌单数据
        playlist_count = playlist_songs.get(song_id, 0)

        # 计算权重
        weight = calculate_song_weight(play_data, playlist_count)

        # 累加标签权重
        for tag_type in ['mood', 'energy', 'genre', 'region']:
            tag_value = tags[tag_type]
            if tag_value and tag_value != 'None':
                tag_weights[tag_value] += weight

        # 统计信息
        stats['total_plays'] += play_data['play_count']
        if play_data['starred']:
            stats['starred_count'] += 1

        processed += 1

    logger.info(f"   处理成功: {processed} 首")
    logger.info(f"   跳过(无标签): {skipped} 首")

    # 5. 归一化权重
    logger.info("5. 归一化权重...")
    total_weight = sum(tag_weights.values())
    if total_weight > 0:
        normalized_weights = {
            tag: round(weight / total_weight * 100, 2)
            for tag, weight in tag_weights.items()
        }
    else:
        normalized_weights = {}

    # 6. 按类别分组
    profile = {
        'mood': {},
        'energy': {},
        'genre': {},
        'region': {}
    }

    for tag, weight in normalized_weights.items():
        for category, allowed_values in ALLOWED_LABELS.items():
            if tag in allowed_values:
                profile[category][tag] = weight
                break

    # 7. 排序
    for category in profile:
        profile[category] = dict(sorted(
            profile[category].items(),
            key=lambda x: x[1],
            reverse=True
        ))

        return {
        'user_id': user_id,
        'profile': profile,
        'stats': stats,
        'generated_at': datetime.now().isoformat()
    }


def print_profile(profile_data: Dict[str, Any]) -> None:
    """打印用户画像"""
    logger.info("=" * 60)
    logger.info("  用户音乐偏好画像")
    logger.info("=" * 60)

    # 统计信息
    stats = profile_data['stats']
    logger.info(f"基础统计:")
    logger.info(f"  总播放次数: {stats['total_plays']}")
    logger.info(f"  收藏歌曲数: {stats['starred_count']}")
    logger.info(f"  歌单歌曲数: {stats['playlist_songs']}")
    logger.info(f"  独立歌曲数: {stats['unique_songs']}")

    # 标签偏好
    profile = profile_data['profile']

    for category, display_name in [
        ('mood', '情绪偏好'),
        ('energy', '能量偏好'),
        ('genre', '流派偏好'),
        ('region', '地区偏好')
    ]:
        logger.info(f"{display_name}:")
        tags = profile[category]
        if tags:
            for tag, weight in list(tags.items())[:5]:  # 只显示前5个
                bar_length = int(weight / 2)  # 50% = 25个字符
                bar = "█" * bar_length
                logger.info(f"  {tag:<15} {weight:>6.2f}% {bar}")
        else:
            logger.info("  (无数据)")

    logger.info("=" * 60)


def save_profile(profile_data: Dict[str, Any], filename: str = "user_profile.json") -> None:
    """保存用户画像到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)
    logger.info(f"用户画像已保存到: {filename}")


def main() -> None:
    """主函数"""
    try:
        nav_conn = connect_nav_db()

        # 获取用户ID
        user_id = get_user_id(nav_conn)
        nav_conn.close()

        # 构建画像
        profile_data = build_user_profile(user_id)

        # 打印结果
        print_profile(profile_data)

        # 保存到文件
        save_profile(profile_data)

        logger.info("提示: 下一步可以使用这个画像进行个性化推荐")

    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
