"""快速测试单首歌曲"""
from src.services.llm_client import LLMClient
from config.constants import get_allowed_labels

llm = LLMClient()
allowed = get_allowed_labels()

# 测试 Dragonborn
title = "Dragonborn"
artist = "Jeremy Soule"
album = "Skyrim OST"

print(f"Testing: {artist} - {title}")
print("-" * 60)

tags, raw_raw = llm.call_llm_api(title, artist, album)

if tags:
    print("\nTags:")
    for key, value in tags.items():
        if key != 'confidence':
            print(f"  {key}: {value}")

    print(f"\nConfidence: {tags.get('confidence', 0.0)}")

    # 验证
    violations = {}
    for dim in ['mood', 'energy', 'genre', 'style', 'region', 'culture', 'language']:
        value = tags.get(dim)
        if not value or value == 'None':
            continue

        if isinstance(value, str):
            values = [v.strip() for v in value.split(',')]
        else:
            values = [str(v) for v in value]

        invalid = [v for v in values if v not in allowed.get(dim, set())]
        if invalid:
            violations[dim] = invalid

    print(f"\nValidation: {'VALID' if not violations else 'INVALID'}")
    if violations:
        print(f"Violations: {violations}")
else:
    print("LLM returned None (API error)")
    print(f"Raw response: {raw_raw}")
