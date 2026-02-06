"""
数据导出工具 - 导出用户数据、播放历史、歌单等
"""

import csv
import json
import sys
import logging
from datetime import datetime
from collections import defaultdict
from typing import Tuple, Dict, Any

from config.settings import EXPORT_DIR
from src.core.database import dbs_context
from src.utils.common import setup_windows_encoding
from src.utils.logger import setup_logger

# 设置 Windows 控制台编码
setup_windows_encoding()

# 设置日志（使用统一的日志配置）
logger = setup_logger('export', level=logging.INFO)


def get_user_id(nav_conn) -> Tuple[str, str]:
    """获取用户ID"""
    cursor = nav_conn.execute("SELECT id, user_name FROM user")
    users = cursor.fetchall()

    if len(users) == 1:
        return users[0][0], users[0][1]

    print("\n可用用户:")
    for idx, (uid, name) in enumerate(users, 1):
        print(f"  {idx}. {name} ({uid})")

    choice = int(input("\n请选择用户 (输入序号): ")) - 1
    logger.info(f"选择用户: {users[choice][1]} ({users[choice][0]})")
    return users[choice][0], users[choice][1]


def export_play_history(nav_conn, sem_conn, user_id: str, output_file: str) -> int:
    """导出播放历史（包含语义标签）"""
    cursor = nav_conn.execute("""
        SELECT
            a.item_id,
            a.play_count,
            a.starred,
            a.play_date,
            m.title,
            m.artist,
            m.album,
            m.year,
            m.genre as original_genre
        FROM annotation a
        JOIN media_file m ON a.item_id = m.id
        WHERE a.user_id = ? AND a.item_type = 'media_file'
        ORDER BY a.play_count DESC
    """, (user_id,))

    rows = cursor.fetchall()

    # 获取语义标签
    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'song_id', 'title', 'artist', 'album', 'year', 'original_genre',
            'play_count', 'starred', 'play_date',
            'mood', 'energy', 'genre', 'style', 'scene', 'region', 'culture', 'language'
        ])

        for row in rows:
            song_id = row[0]

            # 获取语义标签
            sem_cursor = sem_conn.execute("""
                SELECT mood, energy, genre, style, scene, region, culture, language
                FROM music_semantic
                WHERE file_id = ?
            """, (song_id,))

            sem_row = sem_cursor.fetchone()
            if sem_row:
                mood, energy, genre, style, scene, region, culture, language = sem_row
            else:
                mood = energy = genre = style = scene = region = culture = language = 'N/A'

            writer.writerow([
                song_id,
                row[4],  # title
                row[5],  # artist
                row[6],  # album
                row[7],  # year
                row[8],  # original_genre
                row[1],  # play_count
                'Yes' if row[2] else 'No',  # starred
                row[3],  # play_date
                mood,
                energy,
                genre,
                style,
                scene,
                region,
                culture,
                language
            ])

    return len(rows)


def export_playlists(nav_conn, sem_conn, user_id: str, output_file: str) -> int:
    """导出用户歌单"""
    # 获取用户的所有歌单
    playlists = nav_conn.execute("""
        SELECT id, name, updated_at
        FROM playlist
        WHERE owner_id = ?
        ORDER BY name
    """, (user_id,)).fetchall()

    with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'playlist_id', 'playlist_name', 'updated_at',
            'song_id', 'title', 'artist', 'album',
            'mood', 'energy', 'genre', 'style', 'scene', 'region', 'culture', 'language'
        ])

        for playlist in playlists:
            playlist_id, playlist_name, updated_at = playlist

            # 获取歌单中的歌曲
            songs = nav_conn.execute("""
                SELECT pt.media_file_id, m.title, m.artist, m.album
                FROM playlist_tracks pt
                JOIN media_file m ON pt.media_file_id = m.id
                WHERE pt.playlist_id = ?
                ORDER BY pt.position
            """, (playlist_id,)).fetchall()

            for song in songs:
                song_id, title, artist, album = song

                # 获取语义标签
                sem_cursor = sem_conn.execute("""
                    SELECT mood, energy, genre, style, scene, region, culture, language
                    FROM music_semantic
                    WHERE file_id = ?
                """, (song_id,))

                sem_row = sem_cursor.fetchone()
                if sem_row:
                    mood, energy, genre, style, scene, region, culture, language = sem_row
                else:
                    mood = energy = genre = style = scene = region = culture = language = 'N/A'

                writer.writerow([
                    playlist_id, playlist_name, updated_at,
                    song_id, title, artist, album,
                    mood, energy, genre, style, scene, region, culture, language
                ])

    return len(playlists)


def export_statistics(nav_conn, sem_conn, user_id: str, output_file: str) -> Dict[str, Any]:
    """导出用户统计数据"""
    # 播放统计
    play_stats = nav_conn.execute("""
        SELECT
            COUNT(*) as total_songs,
            SUM(play_count) as total_plays,
            COUNT(CASE WHEN starred = 1 THEN 1 END) as starred_count
        FROM annotation
        WHERE user_id = ? AND item_type = 'media_file'
    """, (user_id,)).fetchone()

    # 歌单统计
    playlist_count = nav_conn.execute("""
        SELECT COUNT(*)
        FROM playlist
        WHERE owner_id = ?
    """, (user_id,)).fetchone()[0]

    # 语义标签统计
    mood_dist = sem_conn.execute("""
        SELECT mood, COUNT(*) as count
        FROM music_semantic ms
        JOIN annotation a ON ms.file_id = a.item_id
        WHERE a.user_id = ? AND a.item_type = 'media_file'
        GROUP BY mood
        ORDER BY count DESC
    """, (user_id,)).fetchall()

    stats = {
        'user_id': user_id,
        'export_time': datetime.now().isoformat(),
        'total_songs': play_stats[0],
        'total_plays': play_stats[1],
        'starred_count': play_stats[2],
        'playlist_count': playlist_count,
        'mood_distribution': {row[0]: row[1] for row in mood_dist}
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    return stats


def main() -> None:
    """主函数"""
    logger.info("=" * 80)
    logger.info("  用户数据导出工具")
    logger.info("=" * 80)

    with dbs_context() as (nav_conn, sem_conn):
        # 获取用户ID
        user_id, user_name = get_user_id(nav_conn)

        # 创建导出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = f"{EXPORT_DIR}/export_{user_name}_{timestamp}"
        import os
        os.makedirs(export_dir, exist_ok=True)

        logger.info(f"导出目录: {export_dir}")

        # 导出播放历史
        logger.info("1. 导出播放历史...")
        play_history_file = f"{export_dir}/play_history.csv"
        count = export_play_history(nav_conn, sem_conn, user_id, play_history_file)
        logger.info(f"   已导出 {count} 首歌曲")

        # 导出歌单
        logger.info("2. 导出歌单...")
        playlists_file = f"{export_dir}/playlists.csv"
        count = export_playlists(nav_conn, sem_conn, user_id, playlists_file)
        logger.info(f"   已导出 {count} 个歌单")

        # 导出统计
        logger.info("3. 导出统计数据...")
        stats_file = f"{export_dir}/statistics.json"
        stats = export_statistics(nav_conn, sem_conn, user_id, stats_file)
        logger.info(f"   总歌曲数: {stats['total_songs']}")
        logger.info(f"   总播放次数: {stats['total_plays']}")
        logger.info(f"   收藏歌曲数: {stats['starred_count']}")
        logger.info(f"   歌单数量: {stats['playlist_count']}")

        # 创建 README
        readme_file = f"{export_dir}/README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(f"# 用户数据导出\n\n")
            f.write(f"**用户**: {user_name}\n")
            f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## 文件说明\n\n")
            f.write(f"- `play_history.csv` - 播放历史（包含语义标签）\n")
            f.write(f"- `playlists.csv` - 用户歌单\n")
            f.write(f"- `statistics.json` - 统计数据\n")

        logger.info(f"✅ 导出完成！")
        logger.info(f"   所有文件已保存到: {export_dir}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("已取消")
        sys.exit(0)
    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
