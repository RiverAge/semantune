"""
测试 Instrumental 误判修复效果
测试朋友提到的那些被错误标记为 Instrumental 的歌曲
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.llm_client import LLMClient

# 测试歌曲 - 这些都是有人声但可能被误判为 Instrumental 的歌曲
TEST_SONGS = [
    {
        "title": "平凡之路",
        "artist": "朴树",
        "album": "猎户星座",
        "expected_language": "Chinese",
        "note": "中文流行歌曲，有人声"
    },
    {
        "title": "残響散歌",
        "artist": "LiSA",
        "album": "Demon Slayer",
        "expected_language": "Japanese",
        "note": "动漫歌曲，日语人声"
    },
    {
        "title": "RAISE UR FLAGS",
        "artist": "Key Sounds Label",
        "album": "Summer Pockets Original Soundtrack",
        "expected_language": "Japanese",
        "note": "游戏 OST 主题曲，明确有人声"
    },
    {
        "title": "千本桜",
        "artist": "初音ミク",
        "album": "EXIT TUNES PRESENTS",
        "expected_language": "Japanese",
        "note": "Vocaloid 歌曲必须标日语，不是 Instrumental"
    },
    {
        "title": "Get Lucky",
        "artist": "Daft Punk",
        "album": "Random Access Memories",
        "expected_language": "English",
        "note": "电子音乐但有英语人声演唱"
    }
]

def test_instrumental_fix():
    """测试 Instrumental 误判修复"""
    print("=" * 80)
    print("测试 Instrumental 误判修复效果")
    print("=" * 80)
    print()

    llm_client = LLMClient()

    results = []
    for test in TEST_SONGS:
        print(f"\n[TEST] 歌曲: {test['artist']} - {test['title']}")
        print(f"   专辑: {test['album']}")
        print(f"   预期 language: {test['expected_language']}")
        print(f"   说明: {test['note']}")
        print("   标注中...")

        try:
            tags, raw_response = llm_client.call_llm_api(
                test['title'],
                test['artist'],
                test['album'],
                lyrics=None
            )

            actual_language = tags.get('language', 'N/A') if tags else 'N/A'
            is_instrumental = actual_language == 'Instrumental'

            if actual_language == test['expected_language']:
                status = "[PASS] 通过"
            else:
                status = "[FAIL] 失败"

            result = {
                "song": f"{test['artist']} - {test['title']}",
                "expected": test['expected_language'],
                "actual": actual_language,
                "is_instrumental": is_instrumental,
                "status": status
            }
            results.append(result)

            print(f"   实际 language: {actual_language}")
            print(f"   状态: {status}")

            # 如果标为 Instrumental，显示完整的标签
            if is_instrumental:
                print(f"   [WARNING] 被标记为纯音乐！")
                print(f"   完整标签: {tags}")

        except Exception as e:
            print(f"   [ERROR] 错误: {e}")
            results.append({
                "song": f"{test['artist']} - {test['title']}",
                "expected": test['expected_language'],
                "actual": "ERROR",
                "is_instrumental": False,
                "status": f"[ERROR] 错误: {e}"
            })

        print("-" * 80)

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    passed = sum(1 for r in results if r['status'].startswith('✅'))
    failed = sum(1 for r in results if r['status'].startswith('❌'))
    instrumental_errors = sum(1 for r in results if r['is_instrumental'])

    print(f"\n总测试数: {len(results)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"Instrumental 误判数: {instrumental_errors}")
    print(f"通过率: {passed/len(results)*100:.1f}%")

    # 详细结果表格
    print("\n详细结果:")
    print(f"{'歌曲':<40} {'预期':<12} {'实际':<12} {'状态':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['song']:<40} {r['expected']:<12} {r['actual']:<12} {r['status']:<10}")

    # 检查是否有 Instrumental 误判
    if instrumental_errors > 0:
        print("\n" + "!" * 80)
        print(f"[ERROR] 发现 {instrumental_errors} 个 Instrumental 误判！")
        print("!" * 80)
        return False
    else:
        print("\n" + "=" * 80)
        print("[SUCCESS] 所有测试通过，无 Instrumental 误判！")
        print("=" * 80)
        return True

if __name__ == "__main__":
    success = test_instrumental_fix()
    sys.exit(0 if success else 1)
