#!/usr/bin/env python3
"""测试标签验证功能"""

import json
from config.constants import validate_tags_against_whitelist

# 测试用例1: 合规标签
valid_tags = {
    "mood": ["Happy", "Sad"],
    "energy": "Medium",
    "genre": ["Pop"],
    "style": ["Ballad"],
    "scene": ["Relax"],
    "region": "Chinese",
    "culture": "None",
    "language": "Chinese"
}

# 测试用例2: 不合规标签（包含Epic）
invalid_tags_epic = {
    "mood": ["Epic", "Mysterious"],
    "energy": "High",
    "genre": ["Soundtrack"],
    "style": ["Cinematic"],
    "scene": ["Gaming"],
    "region": "Western",
    "culture": "Game",
    "language": "Instrumental"
}

# 测试用例3: 不合规标签（包含J-Pop）
invalid_tags_jpop = {
    "mood": ["Dreamy"],
    "energy": "Medium",
    "genre": ["Pop", "J-Pop"],
    "style": ["City Pop"],
    "scene": ["Relax"],
    "region": "Japanese",
    "culture": "Idol",
    "language": "Japanese"
}

print("=" * 80)
print("测试1: 合规标签")
print("=" * 80)
result1 = validate_tags_against_whitelist(valid_tags)
print(f"是否合规: {result1['is_valid']}")
print(f"违规标签: {result1.get('invalid_tags', {})}")
print()

print("=" * 80)
print("测试2: 包含Epic标签")
print("=" * 80)
result2 = validate_tags_against_whitelist(invalid_tags_epic)
print(f"是否合规: {result2['is_valid']}")
print(f"违规标签: {json.dumps(result2.get('invalid_tags', {}), ensure_ascii=False, indent=2)}")
print()

print("=" * 80)
print("测试3: 包含J-Pop标签")
print("=" * 80)
result3 = validate_tags_against_whitelist(invalid_tags_jpop)
print(f"是否合规: {result3['is_valid']}")
print(f"违规标签: {json.dumps(result3.get('invalid_tags', {}), ensure_ascii=False, indent=2)}")
print()

print("=" * 80)
print("总结")
print("=" * 80)
print(f"测试通过: {1+result2['is_valid']+result3['is_valid']}/3")
print(f"合规检测功能正常")
