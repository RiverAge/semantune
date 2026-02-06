#!/usr/bin/env python3
"""重新运行40首歌曲的LLM标签生成"""

import json
import re
import time
from pathlib import Path
from src.services.llm_client import LLMClient
from config.settings import get_model

def parse_test_songs(file_path: str):
    """从test.txt解析歌曲列表"""
    songs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    pattern = r'^\s*(\d+)\.\s*(.+?)\s*—\s*(.+?)\s*—\s*(.+?)\s*$'

    for line in lines:
        match = re.match(pattern, line)
        if match:
            num, artist, title, album = match.groups()
            songs.append({
                'num': num,
                'artist': artist.strip(),
                'title': title.strip(),
                'album': album.strip()
            })

    return songs

def main():
    test_file = 'test.txt'
    output_file = 'test_40songs_tags.json'

    print(f"正在从 {test_file} 解析歌曲列表...")
    songs = parse_test_songs(test_file)
    print(f"找到 {len(songs)} 首歌曲\n")

    client = LLMClient()
    results = []

    for idx, song in enumerate(songs, 1):
        print(f"[{idx}/{len(songs)}] 处理: {song['artist']} — {song['title']}")

        try:
            labels, _ = client.call_llm_api(
                title=song['title'],
                artist=song['artist'],
                album=song['album'],
                lyrics=None
            )

            if labels:
                result = {
                    'num': song['num'],
                    'artist': song['artist'],
                    'title': song['title'],
                    'album': song['album'],
                    'tags': labels
                }
                results.append(result)
                print(f"  OK - confidence: {labels.get('confidence', 0):.2f}")
            else:
                print(f"  FAIL - 未返回有效标签")

        except Exception as e:
            print(f"  FAIL - {e}")
            continue

        time.sleep(1)

    print(f"\n完成！成功生成 {len(results)}/{len(songs)} 首歌曲的标签")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"结果已保存到 {output_file}")

if __name__ == '__main__':
    main()
