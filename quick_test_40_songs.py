"""快速验证40首歌曲的LLM标签"""
import json
import sys
from src.services.llm_client import LLMClient
from config.constants import get_allowed_labels

# 禁用DEBUG日志
import logging
logging.getLogger('llm_client').setLevel(logging.INFO)

# 40首测试数据
TEST_SONGS = [
    { "num": "1", "artist": "周杰伦", "title": "晴天", "album": "叶惠美" },
    { "num": "2", "artist": "林宥嘉", "title": "说谎", "album": "感官/世界" },
    { "num": "3", "artist": "陈奕迅", "title": "浮夸", "album": "U87" },
    { "num": "4", "artist": "王菲", "title": "匆匆那年", "album": "匆匆那年 OST" },
    { "num": "5", "artist": "五月天", "title": "倔强", "album": "神的孩子都在跳舞" },
    { "num": "6", "artist": "朴树", "title": "那些花儿", "album": "我去2000年" },
    { "num": "7", "artist": "Aimer", "title": "Ref:rain", "album": "Ref:rain" },
    { "num": "8", "artist": "RADWIMPS", "title": "Sparkle", "album": "君の名は OST" },
    { "num": "9", "artist": "LiSA", "title": "Homura", "album": "鬼滅の刃" },
    { "num": "10", "artist": "米津玄師", "title": "LOSER", "album": "BOOTLEG" },
    { "num": "11", "artist": "久石譲", "title": "The Sixth Station", "album": "千と千尋の神隠し OST" },
    { "num": "12", "artist": "泽野弘之", "title": "Before Lights Out", "album": "进击的巨人 OST" },
    { "num": "13", "artist": "Hans Zimmer", "title": "Cornfield Chase", "album": "Interstellar OST" },
    { "num": "14", "artist": "Ludovico Einaudi", "title": "Nuvole Bianche", "album": "Una Mattina" },
    { "num": "15", "artist": "Adele", "title": "Hello", "album": "25" },
    { "num": "16", "artist": "Sam Smith", "title": "Stay With Me", "album": "In the Lonely Hour" },
    { "num": "17", "artist": "Coldplay", "title": "Adventure of a Lifetime", "album": "A Head Full of Dreams" },
    { "num": "18", "artist": "Imagine Dragons", "title": "Demons", "album": "Night Visions" },
    { "num": "19", "artist": "Linkin Park", "title": "In the End", "album": "Hybrid Theory" },
    { "num": "20", "artist": "Eminem", "title": "Lose Yourself", "album": "8 Mile OST" },
    { "num": "21", "artist": "Daft Punk", "title": "Instant Crush", "album": "Random Access Memories" },
    { "num": "22", "artist": "Porter Robinson", "title": "Goodbye To A World", "album": "Worlds" },
    { "num": "23", "artist": "The Chainsmokers", "title": "Closer", "album": "Collage" },
    { "num": "24", "artist": "Taylor Swift", "title": "Enchanted", "album": "Speak Now" },
    { "num": "25", "artist": "Bruno Mars", "title": "24K Magic", "album": "24K Magic" },
    { "num": "26", "artist": "The Weeknd", "title": "Blinding Lights", "album": "After Hours" },
    { "num": "27", "artist": "Arctic Monkeys", "title": "Do I Wanna Know?", "album": "AM" },
    { "num": "28", "artist": "Radiohead", "title": "No Surprises", "album": "OK Computer" },
    { "num": "29", "artist": "Nirvana", "title": "Come As You Are", "album": "Nevermind" },
    { "num": "30", "artist": "Queen", "title": "Bohemian Rhapsody", "album": "A Night at the Opera" },
    { "num": "31", "artist": "Kanye West", "title": "Stronger", "album": "Graduation" },
    { "num": "32", "artist": "Travis Scott", "title": "SICKO MODE", "album": "ASTROWORLD" },
    { "num": "33", "artist": "Avicii", "title": "Levels", "album": "Levels" },
    { "num": "34", "artist": "ODESZA", "title": "A Moment Apart", "album": "A Moment Apart" },
    { "num": "35", "artist": "Ólafur Arnalds", "title": "Saman", "album": "Island Songs" },
    { "num": "36", "artist": "坂本龙一", "title": "Bibo no Aozora", "album": "Babel OST" },
    { "num": "37", "artist": "久石譲", "title": "The Path of the Wind", "album": "となりのトトロ OST" },
    { "num": "38", "artist": "Jeremy Soule", "title": "Far Horizons", "album": "Skyrim OST" },
    { "num": "39", "artist": "Yiruma", "title": "River Flows in You", "album": "First Love" },
    { "num": "40", "artist": "Joe Hisaishi", "title": "Ashitaka and San", "album": "もののけ姫 OST" }
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
            values = [str(value)]

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
    print(f"Testing {len(TEST_SONGS)} songs...")
    print("-" * 80)

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
                    'error': 'LLM返回空结果'
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

    # 输出统计结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    print(f"总测试数: {len(TEST_SONGS)}")
    print(f"合规数量: {valid_count}")
    print(f"不合规数量: {len(TEST_SONGS) - valid_count}")
    print(f"合规率: {valid_count/len(TEST_SONGS)*100:.1f}%")
    print("=" * 80)

    # 详细错误报告
    print("\n详细错误报告:")
    print("=" * 80)
    has_errors = False
    for r in results:
        if not r['valid']:
            has_errors = True
            print(f"\n#{r['num']} {r['artist']} - {r['title']}")
            if 'violations' in r:
                for dim, invalid_tags in r['violations'].items():
                    print(f"  {dim}: {invalid_tags}")
            if 'error' in r:
                print(f"  错误: {r['error']}")

    if not has_errors:
        print("\n[OK] 所有测试歌曲均符合白名单要求！")

    # 保存结果到文件
    with open('test_40_songs_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total': len(TEST_SONGS),
                'valid': valid_count,
                'invalid': len(TEST_SONGS) - valid_count,
                'valid_rate': f"{valid_count/len(TEST_SONGS)*100:.1f}%"
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n完整结果已保存到: test_40_songs_results.json")

if __name__ == "__main__":
    main()
