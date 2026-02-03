"""
推荐引擎模块 - 基于用户画像和语义标签生成个性化推荐
"""

import json
import math
import random
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from config.settings import RECOMMEND_CONFIG, WEIGHT_CONFIG, ALGORITHM_CONFIG
from config.constants import ALLOWED_LABELS
from src.core.database import connect_nav_db, connect_sem_db
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

# 设置日志
logger = setup_logger('recommend', 'recommend.log', level=logging.INFO)


def build_user_profile(nav_conn, sem_conn, user_id: str, verbose: bool = True) -> Dict[str, Any]:
    """
    构建用户画像（即时生成）
    
    Args:
        nav_conn: Navidrome 数据库连接对象
        sem_conn: 语义数据库连接对象
        user_id: 用户ID
        verbose: 是否打印详细进度信息
        
    Returns:
        用户画像字典，包含:
        {
            'user_id': str,
            'profile': {
                'mood': {tag: weight, ...},
                'energy': {tag: weight, ...},
                'genre': {tag: weight, ...},
                'region': {tag: weight, ...}
            },
            'stats': {
                'total_plays': int,
                'starred_count': int,
                'playlist_songs': int,
                'unique_songs': int
            },
            'generated_at': str (ISO 8601 格式)
        }
    """
    if verbose:
        print(f"\n正在构建用户画像...")
        print("=" * 60)

    # 1. 获取播放历史
    if verbose:
        print("1. 读取播放历史...")
    play_history = get_play_history(nav_conn, user_id)
    if verbose:
        print(f"   找到 {len(play_history)} 首有播放记录的歌曲")

    # 2. 获取歌单信息
    if verbose:
        print("2. 读取歌单信息...")
    playlist_songs = get_playlist_songs(nav_conn, user_id)
    if verbose:
        print(f"   找到 {len(playlist_songs)} 首歌单中的歌曲")

    # 3. 合并所有歌曲ID
    all_song_ids = set(play_history.keys()) | set(playlist_songs.keys())
    if verbose:
        print(f"3. 合并数据...")
        print(f"   总共 {len(all_song_ids)} 首独立歌曲")

    # 4. 计算标签权重
    if verbose:
        print("4. 计算标签权重...")
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

    if verbose:
        logger.info(f"   处理成功: {processed} 首")
        logger.info(f"   跳过(无标签): {skipped} 首")

    # 5. 归一化权重
    if verbose:
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


def build_song_vectors(sem_conn) -> Dict[str, Dict[str, Any]]:
    """
    构建所有歌曲的向量表示（one-hot 编码）
    
    Args:
        sem_conn: 语义数据库连接对象
        
    Returns:
        字典，键为歌曲ID，值为包含向量和元数据的字典
        {
            'song_id': {
                'vector': {tag: 1.0, ...},
                'title': str,
                'artist': str,
                'album': str,
                'mood': str,
                'energy': str,
                'genre': str,
                'region': str
            }
        }
    """
    cursor = sem_conn.execute("""
        SELECT file_id, title, artist, album, mood, energy, genre, region
        FROM music_semantic
    """)

    song_vectors = {}
    for row in cursor.fetchall():
        file_id = row[0]
        vec = defaultdict(float)

        # 将标签转为向量（one-hot 编码）
        for tag in [row[4], row[5], row[6], row[7]]:  # mood, energy, genre, region
            if tag and tag != 'None':
                vec[tag] = 1.0

        song_vectors[file_id] = {
            'vector': dict(vec),
            'title': row[1],
            'artist': row[2],
            'album': row[3],
            'mood': row[4],
            'energy': row[5],
            'genre': row[6],
            'region': row[7]
        }

    return song_vectors


def weighted_similarity(user_vec: Dict[str, float], song_vec: Dict[str, float], tag_weights: Dict[str, float]) -> float:
    """
    计算加权相似度（拉开分布）
    
    Args:
        user_vec: 用户画像向量，键为标签，值为权重
        song_vec: 歌曲向量，键为标签，值为 1.0
        tag_weights: 标签权重配置，如 {'mood': 2.0, 'energy': 1.5, ...}
        
    Returns:
        归一化后的相似度分数，范围 [0, 1]
        
    计算逻辑:
        1. 分别计算各维度的匹配度（点积）
        2. 按标签权重加权求和
        3. 归一化到 [0, 1] 范围
        
    不同标签有不同的重要性：
    - mood 最重要（权重 2.0）
    - energy 次之（权重 1.5）
    - genre 中等（权重 1.2）
    - region 较低（权重 0.8）
    """
    # 分别计算各维度的匹配度
    mood_match = 0.0
    energy_match = 0.0
    genre_match = 0.0
    region_match = 0.0

    # Mood 维度
    for tag in ALLOWED_LABELS['mood']:
        if tag in user_vec and tag in song_vec:
            mood_match += user_vec[tag] * song_vec[tag]

    # Energy 维度
    for tag in ALLOWED_LABELS['energy']:
        if tag in user_vec and tag in song_vec:
            energy_match += user_vec[tag] * song_vec[tag]

    # Genre 维度
    for tag in ALLOWED_LABELS['genre']:
        if tag in user_vec and tag in song_vec:
            genre_match += user_vec[tag] * song_vec[tag]

    # Region 维度
    for tag in ALLOWED_LABELS['region']:
        if tag in user_vec and tag in song_vec:
            region_match += user_vec[tag] * song_vec[tag]

    # 加权求和
    weighted_score = (
        mood_match * tag_weights['mood'] +
        energy_match * tag_weights['energy'] +
        genre_match * tag_weights['genre'] +
        region_match * tag_weights['region']
    )

    # 归一化到 0-1 范围
    max_possible = (
        tag_weights['mood'] +
        tag_weights['energy'] +
        tag_weights['genre'] +
        tag_weights['region']
    )

    return weighted_score / max_possible if max_possible > 0 else 0.0


def get_recent_songs(nav_conn, user_id: str, limit: int = 100) -> set:
    """获取用户最近听过的歌曲ID"""
    cursor = nav_conn.execute("""
        SELECT item_id
        FROM annotation
        WHERE user_id = ? AND item_type = 'media_file'
        ORDER BY play_date DESC
        LIMIT ?
    """, (user_id, limit))

    return {row[0] for row in cursor.fetchall()}


def get_user_songs(nav_conn, user_id: str) -> set:
    """获取用户所有听过的歌曲ID（用于过滤）"""
    cursor = nav_conn.execute("""
        SELECT item_id
        FROM annotation
        WHERE user_id = ? AND item_type = 'media_file' AND play_count > 0
    """, (user_id,))

    return {row[0] for row in cursor.fetchall()}


def recommend(user_id: Optional[str] = None, limit: int = 30, filter_recent: bool = True, diversity: bool = True, exploration: bool = True) -> List[Dict[str, Any]]:
    """
    生成个性化推荐
    
    Args:
        user_id: 用户ID，如果为 None 则自动选择
        limit: 推荐数量
        filter_recent: 是否过滤最近听过的歌
        diversity: 是否启用多样性优化（限制每个歌手/专辑的推荐数量）
        exploration: 是否启用探索模式（混合高相似度和中等相似度的歌曲）
        
    Returns:
        推荐歌曲列表，每个元素包含:
        {
            'song_id': str,
            'similarity': float,
            'title': str,
            'artist': str,
            'album': str,
            'mood': str,
            'energy': str,
            'genre': str,
            'region': str
        }
        
    推荐流程:
        1. 即时构建用户画像
        2. 获取用户历史（用于过滤）
        3. 构建歌曲向量库
        4. 计算加权相似度
        5. 应用多样性约束
        6. 混合利用型和探索型推荐
    """
    # 1. 连接数据库
    nav_conn = connect_nav_db()
    sem_conn = connect_sem_db()

    # 2. 获取用户ID
    if user_id is None:
        user_id = get_user_id(nav_conn)

    # 3. 即时构建用户画像
    profile_data = build_user_profile(nav_conn, sem_conn, user_id, verbose=True)
    user_profile = profile_data['profile']

    # 将用户画像转为向量（使用归一化后的权重）
    user_vector = {}
    for category, tags in user_profile.items():
        for tag, weight in tags.items():
            user_vector[tag] = weight / 100.0  # 转回 0-1 范围

    print(f"   用户ID: {user_id}")
    print(f"   画像维度: {len(user_vector)} 个标签")

    # 4. 获取已听过的歌曲（用于过滤）
    print("2. 获取用户历史...")
    user_songs = get_user_songs(nav_conn, user_id)
    recent_songs = get_recent_songs(nav_conn, user_id, RECOMMEND_CONFIG['recent_filter_count']) if filter_recent else set()

    print(f"   已听过: {len(user_songs)} 首")
    print(f"   最近听过: {len(recent_songs)} 首")

    # 5. 构建歌曲向量
    print("3. 构建歌曲向量库...")
    song_vectors = build_song_vectors(sem_conn)
    print(f"   歌曲总数: {len(song_vectors)} 首")

    # 6. 计算相似度（使用加权相似度）
    print("4. 计算加权相似度...")
    scores = []
    tag_weights = RECOMMEND_CONFIG['tag_weights']

    for song_id, song_data in song_vectors.items():
        # 过滤已听过的歌
        if song_id in user_songs:
            continue

        # 过滤最近听过的歌
        if filter_recent and song_id in recent_songs:
            continue

        # 计算加权相似度
        similarity = weighted_similarity(user_vector, song_data['vector'], tag_weights)

        if similarity > 0:
            scores.append({
                'song_id': song_id,
                'similarity': similarity,
                'title': song_data['title'],
                'artist': song_data['artist'],
                'album': song_data['album'],
                'mood': song_data['mood'],
                'energy': song_data['energy'],
                'genre': song_data['genre'],
                'region': song_data['region']
            })

    # 6. 排序
    scores.sort(key=lambda x: x['similarity'], reverse=True)

    print(f"   候选歌曲: {len(scores)} 首")
    if scores:
        print(f"   相似度范围: {scores[0]['similarity']:.3f} ~ {scores[-1]['similarity']:.3f}")

    # 7. 分离利用型和探索型推荐
    if exploration and len(scores) > limit:
        exploration_count = int(limit * RECOMMEND_CONFIG['exploration_ratio'])
        exploitation_count = limit - exploration_count

        print(f"5. 混合推荐策略...")
        print(f"   利用型（高相似度）: {exploitation_count} 首")
        print(f"   探索型（多样性）: {exploration_count} 首")

        # 利用型：取高相似度的歌
        exploitation_pool = scores[:exploitation_count * ALGORITHM_CONFIG["exploitation_pool_multiplier"]]

        # 探索型：从中等相似度中随机选择
        mid_start = int(len(scores) * ALGORITHM_CONFIG["exploration_pool_start"])
        mid_end = int(len(scores) * ALGORITHM_CONFIG["exploration_pool_end"])
        exploration_pool = scores[mid_start:mid_end]

        random.shuffle(exploration_pool)

        # 合并
        combined_pool = exploitation_pool + exploration_pool[:exploration_count * 2]
    else:
        logger.info(f"5. 应用多样性优化...")
        combined_pool = scores

    # 8. 严格的多样性约束
    if diversity:
        diversified = []
        artist_count = defaultdict(int)
        album_count = defaultdict(int)

        max_per_artist = RECOMMEND_CONFIG['diversity_max_per_artist']
        max_per_album = RECOMMEND_CONFIG['diversity_max_per_album']

        for song in combined_pool:
            artist = song['artist']
            album = song['album']
            album_key = f"{artist}::{album}"  # 艺人+专辑组合键

            # 检查艺人约束
            if artist_count[artist] >= max_per_artist:
                continue

            # 检查专辑约束
            if album_count[album_key] >= max_per_album:
                continue

            diversified.append(song)
            artist_count[artist] += 1
            album_count[album_key] += 1

            if len(diversified) >= limit:
                break

        # 按相似度重新排序
        recommendations = sorted(diversified, key=lambda x: x['similarity'], reverse=True)

        logger.info(f"   最终推荐: {len(recommendations)} 首")
        logger.info(f"   独立艺人数: {len(artist_count)}")
        logger.info(f"   独立专辑数: {len(album_count)}")
    else:
        recommendations = combined_pool[:limit]

    nav_conn.close()
    sem_conn.close()

    return recommendations


def print_recommendations(recommendations: List[Dict[str, Any]]) -> None:
    """
    打印推荐结果到控制台
    
    Args:
        recommendations: 推荐歌曲列表
    """
    logger.info("=" * 80)
    logger.info(f"  为你推荐 (共 {len(recommendations)} 首)")
    logger.info("=" * 80)
    logger.info(f"{'#':<4} {'相似度':<8} {'歌手':<20} {'歌曲':<30} {'标签':<20}")
    logger.info("-" * 80)

    for idx, song in enumerate(recommendations, 1):
        artist = (song['artist'][:18] + '..') if len(song['artist']) > 18 else song['artist']
        title = (song['title'][:28] + '..') if len(song['title']) > 28 else song['title']
        tags = f"{song['mood']}/{song['energy']}/{song['genre']}"
        similarity = f"{song['similarity']:.3f}"

        logger.info(f"{idx:<4} {similarity:<8} {artist:<20} {title:<30} {tags:<20}")

    logger.info("=" * 80)


def main() -> None:
    """
    主函数 - 生成并显示个性化推荐
    
    流程:
        1. 获取用户ID
        2. 生成推荐
        3. 打印推荐结果
    """
    logger.info("=" * 80)
    logger.info("  个性化音乐推荐系统")
    logger.info("=" * 80)

    # 参数配置
    limit = 30
    filter_recent = True
    diversity = True

    # 生成推荐
    try:
        # 获取用户歌曲数（用于统计）
        nav_conn = connect_nav_db()
        user_id = get_user_id(nav_conn)
        user_songs = get_user_songs(nav_conn, user_id)
        nav_conn.close()

        recommendations = recommend(
            user_id=user_id,
            limit=limit,
            filter_recent=filter_recent,
            diversity=diversity
        )

        # 打印结果
        print_recommendations(recommendations)

        logger.info("提示:")
        logger.info("  - 使用加权相似度，拉开了分数分布")
        logger.info("  - 每个歌手最多推荐 2 首")
        logger.info("  - 每张专辑最多推荐 1 首")
        logger.info(f"  - 包含 {int(limit * RECOMMEND_CONFIG['exploration_ratio'])} 首探索型歌曲（发现新风格）")
        logger.info(f"  - 已过滤你听过的 {len(user_songs)} 首歌曲")
        logger.info("  - 用户画像即时生成，无需预先构建")

    except Exception as e:
        logger.error(f"推荐失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
