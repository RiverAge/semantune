"""测试改进版提示词的新40首歌曲标签合规性"""
import json
import sys
import time
from src.services.llm_client import LLMClient
from config.constants import get_allowed_labels

# 禁用DEBUG日志
import logging
logging.getLogger('llm_client').setLevel(logging.WARNING)

# 新的40首测试数据
TEST_SONGS = [
    { "num": "1", "artist": "周杰伦", "title": "七里香", "album": "七里香" },
    { "num": "2", "artist": "林俊杰", "title": "江南", "album": "第二天堂" },
    { "num": "3", "artist": "李圣杰", "title": "痴心绝对", "album": "痴心绝对" },
    { "num": "4", "artist": "陈奕迅", "title": "十年", "album": "黑·白·灰" },
    { "num": "5", "artist": "张学友", "title": "她来听我的演唱会", "album": "想和你去吹吹风" },
    { "num": "6", "artist": "王菲", "title": "红豆", "album": "唱游" },
    { "num": "7", "artist": "五月天", "title": "温柔", "album": "人生海海" },
    { "num": "8", "artist": "伍佰", "title": "挪威的森林", "album": "爱情的尽头" },
    { "num": "9", "artist": "朴树", "title": "平凡之路", "album": "后会无期 OST" },
    { "num": "10", "artist": "毛不易", "title": "消愁", "album": "平凡的一天" },
    { "num": "11", "artist": "Aimer", "title": "残響散歌", "album": "鬼滅の刃" },
    { "num": "12", "artist": "LiSA", "title": "Gurenge", "album": "鬼滅の刃" },
    { "num": "13", "artist": "RADWIMPS", "title": "なんでもないや", "album": "君の名は OST" },
    { "num": "14", "artist": "YOASOBI", "title": "夜に駆ける", "album": "夜に駆ける" },
    { "num": "15", "artist": "米津玄師", "title": "Lemon", "album": "Lemon" },
    { "num": "16", "artist": "Kalafina", "title": "Magia", "album": "魔法少女まどか☆マギカ" },
    { "num": "17", "artist": "澤野弘之", "title": "YouSeeBIGGIRL/T:T", "album": "進撃の巨人 OST" },
    { "num": "18", "artist": "久石譲", "title": "One Summer’s Day", "album": "千と千尋の神隠し OST" },
    { "num": "19", "artist": "初音ミク", "title": "千本桜", "album": "Vocaloid Collection" },
    { "num": "20", "artist": "澤野弘之", "title": "Call of Silence", "album": "Attack on Titan OST" },
    { "num": "21", "artist": "Nobuo Uematsu", "title": "To Zanarkand", "album": "Final Fantasy X OST" },
    { "num": "22", "artist": "Austin Wintory", "title": "Journey", "album": "Journey OST" },
    { "num": "23", "artist": "Hans Zimmer", "title": "Time", "album": "Inception OST" },
    { "num": "24", "artist": "Joe Hisaishi", "title": "Summer", "album": "菊次郎の夏 OST" },
    { "num": "25", "artist": "Jeremy Soule", "title": "Dragonborn", "album": "Skyrim OST" },
    { "num": "26", "artist": "Adele", "title": "Someone Like You", "album": "21" },
    { "num": "27", "artist": "Billie Eilish", "title": "everything i wanted", "album": "everything i wanted" },
    { "num": "28", "artist": "Coldplay", "title": "Fix You", "album": "X&Y" },
    { "num": "29", "artist": "Linkin Park", "title": "Numb", "album": "Meteora" },
    { "num": "30", "artist": "Taylor Swift", "title": "Love Story", "album": "Fearless" },
    { "num": "31", "artist": "Kendrick Lamar", "title": "HUMBLE.", "album": "DAMN." },
    { "num": "32", "artist": "Daft Punk", "title": "Get Lucky", "album": "Random Access Memories" },
    { "num": "33", "artist": "Radiohead", "title": "Creep", "album": "Pablo Honey" },
    { "num": "34", "artist": "Imagine Dragons", "title": "Believer", "album": "Evolve" },
    { "num": "35", "artist": "YOASOBI", "title": "アイドル", "album": "アイドル" },
    { "num": "36", "artist": "Sigur Rós", "title": "Svefn-g-englar", "album": "Ágætis byrjun" },
    { "num": "37", "artist": "坂本龙一", "title": "Merry Christmas Mr. Lawrence", "album": "Soundtrack" },
    { "num": "38", "artist": "久石譲", "title": "Path of the Wind", "album": "龙猫 OST" },
    { "num": "39", "artist": "Porter Robinson", "title": "Sad Machine", "album": "Worlds" },
    { "num": "40", "artist": "宇多田ヒカル", "title": "First Love", "album": "First Love" }
]

def validate_tags(tags, allowed_labels):
    violations = {}
    overall_valid = True

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
                overall_valid = False

        if invalid_values:
            violations[dim] = invalid_values

    return overall_valid, violations

def main():
    print(f"Testing {len(TEST_SONGS)} new songs with improved prompt...")
    print("="*80)

    allowed_labels = get_allowed_labels()
    results = []
    valid_count = 0
    llm_client = LLMClient()

    for idx, song in enumerate(TEST_SONGS, 1):
        num = song['num']
        artist = song['artist']
        title = song['title']
        album = song['album']

        try:
            sys.stdout.write(f"\r[{idx}/{len(TEST_SONGS)}] Processing...")
            sys.stdout.flush()
        except:
            pass

        try:
            tags, raw_response = llm_client.call_llm_api(title, artist, album)

            if tags:
                is_valid, violations = validate_tags(tags, allowed_labels)

                if is_valid:
                    valid_count += 1

                results.append({
                    'num': num,
                    'artist': artist,
                    'title': title,
                    'album': album,
                    'valid': is_valid,
                    'violations': violations,
                    'tags': tags
                })
            else:
                results.append({
                    'num': num,
                    'artist': artist,
                    'title': title,
                    'album': album,
                    'valid': False,
                    'error': 'LLM returned empty result'
                })

        except Exception as e:
            results.append({
                'num': num,
                'artist': artist,
                'title': title,
                'album': album,
                'valid': False,
                'error': str(e)
            })

        time.sleep(0.5)

    # 输出统计结果
    print("\n" + "="*80)
    print("Test Results Summary")
    print("="*80)
    print(f"Total: {len(TEST_SONGS)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {len(TEST_SONGS) - valid_count}")
    print(f"Valid Rate: {valid_count/len(TEST_SONGS)*100:.1f}%")
    print("="*80)

    # 详细错误报告
    invalid_results = [r for r in results if not r['valid']]
    print("\nInvalid Songs:")
    print("="*80)
    if invalid_results:
        for r in invalid_results:
            print(f"\n#{r['num']} {r['artist']} - {r['title']}")
            if 'violations' in r:
                for dim, invalid_tags in r['violations'].items():
                    print(f"  {dim}: {invalid_tags}")
            if 'error' in r:
                print(f"  Error: {r['error']}")
    else:
        print("All songs are compliant!")

    # 重点案例分析
    print("\n" + "="*80)
    print("Key Test Cases Analysis")
    print("="*80)

    key_cases = {
        '11': ('Aimer', '残響散歌', 'J-Pop test'),
        '14': ('YOASOBI', '夜に駆ける', 'J-Pop test'),
        '19': ('初音ミク', '千本桜', 'Vocaloid language test'),
        '18': ('久石譲', 'One Summer’s Day', 'OST Instrumental test'),
        '37': ('坂本龙一', 'Merry Christmas Mr. Lawrence', 'OST Instrumental test')
    }

    for num, (artist, title, test_type) in key_cases.items():
        for r in results:
            if r['num'] == num:
                print(f"\n{num}. {artist} - {title} ({test_type})")
                print(f"  Valid: {r['valid']}")
                if 'tags' in r:
                    tags = r['tags']
                    print(f"  Genre: {tags.get('genre')}")
                    print(f"  Style: {tags.get('style')}")
                    print(f"  Region: {tags.get('region')}")
                    print(f"  Language: {tags.get('language')}")
                    print(f"  Culture: {tags.get('culture')}")
                if 'violations' in r:
                    print(f"  Violations: {r['violations']}")
                break

    # 分类统计
    print("\n" + "="*80)
    print("Category Analysis")
    print("="*80)
    
    categories = {
        'Chinese Pop': [r for r in results if r['num'] in ['1','2','3','4','5','6','7','8','9','10']],
        'Japanese Pop/Anime': [r for r in results if r['num'] in ['11','12','13','14','15','16','17','19','20','35']],
        'Game/Film OST': [r for r in results if r['num'] in ['18','21','22','23','24','25','37','38']],
        'Western Pop': [r for r in results if r['num'] in ['26','27','28','29','30']],
        'Hip-Hop/Electronic': [r for r in results if r['num'] in ['31','32','33','34','39','40']],
        'Other': [r for r in results if r['num'] == '36']
    }

    for cat_name, cat_results in categories.items():
        valid = sum(1 for r in cat_results if r['valid'])
        total = len(cat_results)
        print(f"\n{cat_name}: {valid}/{total} compliant ({valid/total*100:.1f}%)")

    # 保存结果到文件
    with open('new_40_songs_test.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': len(TEST_SONGS),
                'valid': valid_count,
                'invalid': len(TEST_SONGS) - valid_count,
                'valid_rate': f"{valid_count/len(TEST_SONGS)*100:.1f}%"
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: new_40_songs_test.json")

if __name__ == "__main__":
    main()
