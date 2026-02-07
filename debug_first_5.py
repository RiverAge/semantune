"""测试前5首歌的LLM标签验证"""
import sys
from src.services.llm_client import LLMClient
from config.constants import get_allowed_labels

TEST_SONGS = [
    { "num": "1", "artist": "周杰伦", "title": "晴天", "album": "叶惠美" },
    { "num": "2", "artist": "林宥嘉", "title": "说谎", "album": "感官/世界" },
    { "num": "3", "artist": "陈奕迅", "title": "浮夸", "album": "U87" },
]

llm_client = LLMClient()
allowed_labels = get_allowed_labels()

for song in TEST_SONGS:
    tags, raw = llm_client.call_llm_api(song['title'], song['artist'], song['album'])

    print(f"\n#{song['num']} {song['artist']} - {song['title']}")
    print(f"Raw tags type: {type(tags)}")
    print(f"Tags: {tags}")

    # 验证
    violations = {}
    dimensions = ['mood', 'energy', 'genre', 'style', 'scene', 'region', 'culture', 'language']

    for dim in dimensions:
        value = tags.get(dim)
        if not value or value == 'None':
            continue

        if isinstance(value, str):
            values = [v.strip() for v in value.split(',')]
        else:
            values = [str(v) for v in value]

        invalid_values = []
        allowed_set = allowed_labels.get(dim, set())
        for v in values:
            if v not in allowed_set:
                invalid_values.append(v)

        if invalid_values:
            violations[dim] = invalid_values
            print(f"  {dim} INVALID: {values} -> {invalid_values}")
        else:
            print(f"  {dim} OK: {values}")

    print(f"  Overall: {'VALID' if not violations else 'INVALID'} - {list(violations.keys()) if violations else 'None'}")
