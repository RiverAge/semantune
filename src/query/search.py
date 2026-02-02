"""
查询工具模块 - 按标签查询歌曲
"""

import sys
import logging
from typing import List, Optional, Dict, Any

from config.constants import ALLOWED_LABELS
from src.core.database import connect_sem_db
from src.utils.common import setup_windows_encoding
from src.utils.logger import setup_logger

# 设置 Windows 控制台编码
setup_windows_encoding()

# 设置日志
logger = setup_logger('query', 'query.log', level=logging.INFO)


def print_songs(songs: List[Dict[str, Any]], title: str = "查询结果") -> None:
    """格式化打印歌曲列表"""
    if not songs:
        logger.warning(f"{title}: 没有找到符合条件的歌曲")
        return

    logger.info("=" * 80)
    logger.info(f"  {title} (共 {len(songs)} 首)")
    logger.info("=" * 80)
    logger.info(f"{'#':<4} {'歌手':<20} {'歌曲':<30} {'标签':<25}")
    logger.info("-" * 80)

    for idx, song in enumerate(songs, 1):
        artist = (song['artist'][:18] + '..') if len(song['artist']) > 18 else song['artist']
        title = (song['title'][:28] + '..') if len(song['title']) > 28 else song['title']
        tags = f"{song['mood']}/{song['energy']}/{song['genre']}"
        logger.info(f"{idx:<4} {artist:<20} {title:<30} {tags:<25}")

    logger.info("=" * 80)


def query_by_mood(sem, mood: str, limit: int = 20) -> List[Dict[str, Any]]:
    """按情绪查询"""
    cursor = sem.execute("""
        SELECT title, artist, album, mood, energy, genre, region, confidence
        FROM music_semantic
        WHERE mood = ?
        ORDER BY confidence DESC
        LIMIT ?
    """, (mood, limit))
    return cursor.fetchall()


def query_by_tags(sem, mood: Optional[str] = None, energy: Optional[str] = None, genre: Optional[str] = None, region: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """按多个标签组合查询"""
    conditions = []
    params = []

    if mood:
        conditions.append("mood = ?")
        params.append(mood)
    if energy:
        conditions.append("energy = ?")
        params.append(energy)
    if genre:
        conditions.append("genre = ?")
        params.append(genre)
    if region:
        conditions.append("region = ?")
        params.append(region)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    cursor = sem.execute(f"""
        SELECT title, artist, album, mood, energy, genre, region, confidence
        FROM music_semantic
        WHERE {where_clause}
        ORDER BY RANDOM()
        LIMIT ?
    """, params + [limit])

    return cursor.fetchall()


def query_scene_preset(sem, scene_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """预设场景查询"""
    # 场景预设定义（业务逻辑）
    presets = {
        "深夜": {"mood": ["Peaceful", "Sad", "Dreamy", "Chill"], "energy": list(ALLOWED_LABELS['energy'] & {"Low"})},
        "运动": {"mood": ["Energetic", "Epic"], "energy": list(ALLOWED_LABELS['energy'] & {"High"})},
        "学习": {"mood": ["Peaceful", "Chill"], "energy": list(ALLOWED_LABELS['energy'] & {"Low", "Medium"})},
        "开车": {"mood": ["Energetic", "Upbeat", "Groovy"], "energy": list(ALLOWED_LABELS['energy'] & {"Medium", "High"})},
        "放松": {"mood": ["Peaceful", "Dreamy", "Chill"], "energy": list(ALLOWED_LABELS['energy'] & {"Low"})},
        "派对": {"mood": ["Happy", "Energetic", "Upbeat"], "energy": list(ALLOWED_LABELS['energy'] & {"High"})},
        "伤心": {"mood": ["Sad", "Emotional"], "energy": list(ALLOWED_LABELS['energy'] & {"Low", "Medium"})},
        "励志": {"mood": ["Epic", "Energetic"], "energy": list(ALLOWED_LABELS['energy'] & {"High"})},
    }
    
    # 验证预设中的标签是否都在 ALLOWED_LABELS 中
    for scene_name_key, preset in presets.items():
        for mood_tag in preset["mood"]:
            if mood_tag not in ALLOWED_LABELS['mood']:
                raise ValueError(f"场景预设 '{scene_name_key}' 中的 mood 标签 '{mood_tag}' 不在 ALLOWED_LABELS 中")
        for energy_tag in preset["energy"]:
            if energy_tag not in ALLOWED_LABELS['energy']:
                raise ValueError(f"场景预设 '{scene_name_key}' 中的 energy 标签 '{energy_tag}' 不在 ALLOWED_LABELS 中")

    if scene_name not in presets:
        logger.warning(f"未知场景。可用场景: {', '.join(presets.keys())}")
        return []

    preset = presets[scene_name]
    mood_list = preset["mood"]
    energy_list = preset["energy"]

    # 使用参数化查询防止 SQL 注入
    # 动态生成占位符
    mood_placeholders = ','.join(['?' for _ in mood_list])
    energy_placeholders = ','.join(['?' for _ in energy_list])
    
    cursor = sem.execute(f"""
        SELECT title, artist, album, mood, energy, genre, region, confidence
        FROM music_semantic
        WHERE mood IN ({mood_placeholders}) AND energy IN ({energy_placeholders})
        ORDER BY RANDOM()
        LIMIT ?
    """, mood_list + energy_list + [limit])

    return cursor.fetchall()


def query_similar_to_song(sem, song_title: str, limit: int = 20) -> List[Dict[str, Any]]:
    """找相似歌曲（基于标签匹配）"""
    # 先找到目标歌曲
    target = sem.execute("""
        SELECT mood, energy, genre, region
        FROM music_semantic
        WHERE title LIKE ?
        LIMIT 1
    """, (f"%{song_title}%",)).fetchone()

    if not target:
        logger.warning(f"找不到歌曲: {song_title}")
        return []

    # 找相似的歌曲（相同 mood + energy + genre）
    cursor = sem.execute("""
        SELECT title, artist, album, mood, energy, genre, region, confidence
        FROM music_semantic
        WHERE mood = ? AND energy = ? AND genre = ?
        AND title NOT LIKE ?
        ORDER BY RANDOM()
        LIMIT ?
    """, (target['mood'], target['energy'], target['genre'], f"%{song_title}%", limit))

    logger.info(f"[目标] 歌曲标签: {target['mood']} / {target['energy']} / {target['genre']} / {target['region']}")

    return cursor.fetchall()


def export_playlist(songs, filename):
    """导出歌单到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 推荐歌单\n\n")
        for idx, song in enumerate(songs, 1):
            f.write(f"{idx}. {song['artist']} - {song['title']}\n")
            f.write(f"   专辑: {song['album']}\n")
            f.write(f"   标签: {song['mood']} / {song['energy']} / {song['genre']} / {song['region']}\n\n")

    logger.info(f"歌单已导出到: {filename}")


def show_menu():
    """显示菜单"""
    print("\n" + "="*80)
    print("  语义标签查询工具")
    print("="*80)
    print("  1. 按情绪查询 (Mood)")
    print("  2. 按标签组合查询 (Mood + Energy + Genre + Region)")
    print("  3. 按场景查询 (预设场景)")
    print("  4. 找相似歌曲")
    print("  5. 随机推荐")
    print("  6. 导出上次查询结果")
    print("  0. 退出")
    print("="*80)


def main() -> None:
    """主函数"""
    sem = connect_sem_db()
    last_results = []

    logger.info("欢迎使用语义标签查询工具！")

    while True:
        show_menu()
        choice = input("\n请选择功能 (0-6): ").strip()

        if choice == "0":
            logger.info("再见！")
            break

        elif choice == "1":
            mood_list = ", ".join(sorted(ALLOWED_LABELS['mood']))
            print(f"\n可用情绪: {mood_list}")
            mood = input("请输入情绪: ").strip()
            limit = int(input("返回数量 (默认20): ").strip() or "20")

            results = query_by_mood(sem, mood, limit)
            print_songs(results, f"情绪={mood}")
            last_results = results

        elif choice == "2":
            print("\n请输入查询条件 (留空跳过):")
            mood = input("  情绪 (Mood): ").strip() or None
            energy_list = "/".join(sorted(ALLOWED_LABELS['energy']))
            energy = input(f"  能量 (Energy: {energy_list}): ").strip() or None
            genre_list = "/".join(sorted(ALLOWED_LABELS['genre']))
            genre = input(f"  流派 (Genre: {genre_list}): ").strip() or None
            region_list = "/".join(sorted(ALLOWED_LABELS['region']))
            region = input(f"  地区 (Region: {region_list}): ").strip() or None
            limit = int(input("  返回数量 (默认20): ").strip() or "20")

            results = query_by_tags(sem, mood, energy, genre, region, limit)
            tag_desc = " + ".join(filter(None, [mood, energy, genre, region]))
            print_songs(results, f"标签组合: {tag_desc}")
            last_results = results

        elif choice == "3":
            print("\n可用场景: 深夜, 运动, 学习, 开车, 放松, 派对, 伤心, 励志")
            scene = input("请选择场景: ").strip()
            limit = int(input("返回数量 (默认20): ").strip() or "20")

            results = query_scene_preset(sem, scene, limit)
            print_songs(results, f"场景: {scene}")
            last_results = results

        elif choice == "4":
            song_title = input("\n请输入歌曲名 (支持模糊搜索): ").strip()
            limit = int(input("返回数量 (默认20): ").strip() or "20")

            results = query_similar_to_song(sem, song_title, limit)
            print_songs(results, f"与 '{song_title}' 相似的歌曲")
            last_results = results

        elif choice == "5":
            limit = int(input("\n返回数量 (默认20): ").strip() or "20")
            results = query_by_tags(sem, limit=limit)
            print_songs(results, "随机推荐")
            last_results = results

        elif choice == "6":
            if not last_results:
                logger.warning("没有可导出的结果")
                continue

            filename = input("\n请输入文件名 (默认: playlist.txt): ").strip() or "playlist.txt"
            export_playlist(last_results, filename)

        else:
            logger.warning("无效选择，请重试")

    sem.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("已退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"错误: {e}")
        sys.exit(1)
