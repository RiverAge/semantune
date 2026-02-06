#!/usr/bin/env python3
"""添加获取验证失败记录的API端点"""

import sqlite3

def add_invalid_tags_api():
    """在API routes中添加获取验证失败记录的端点"""

    # 这里只是生成代码片段，需要手动添加到 endpoints.py
    endpoint_code = '''
@router.get("/validation/invalid")
def get_invalid_tags(
    limit: int = 50,
    offset: int = 0
):
    """获取验证失败的歌曲列表

    Args:
        limit: 返回数量，默认50
        offset: 偏移量，默认0

    Returns:
        验证失败的歌曲列表
    """
    cursor = sem_db_context().__enter__().cursor()

    cursor.execute("""
        SELECT file_id, title, artist, album,
               mood, energy, genre, style, scene, region, culture, language,
               confidence, model, updated_at,
               invalid_tags
        FROM music_semantic
        WHERE validation_status = 'invalid'
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))

    results = []
    for row in cursor.fetchall():
        results.append({
            "file_id": row[0],
            "title": row[1],
            "artist": row[2],
            "album": row[3],
            "mood": json.loads(row[4]) if row[4] else None,
            "energy": row[5],
            "genre": json.loads(row[6]) if row[6] else None,
            "style": json.loads(row[7]) if row[7] else None,
            "scene": json.loads(row[8]) if row[8] else None,
            "region": row[9],
            "culture": row[10],
            "language": row[11],
            "confidence": row[12],
            "model": row[13],
            "updated_at": row[14],
            "invalid_tags": json.loads(row[15]) if row[15] else None
        })

    sem_db_context().__exit__(None, None, None)

    return {
        "total": len(results),
        "limit": limit,
        "offset": offset,
        "data": results
    }


@router.get("/validation/stats")
def get_validation_stats():
    """获取验证统计信息

    Returns:
        验证统计信息
    """
    conn = sem_db_context().__enter__()
    cursor = conn.cursor()

    # 总数统计
    cursor.execute("SELECT COUNT(*) FROM music_semantic")
    total = cursor.fetchone()[0]

    # 有效统计
    cursor.execute("SELECT COUNT(*) FROM music_semantic WHERE validation_status = 'valid'")
    valid = cursor.fetchone()[0]

    # 无效统计
    cursor.execute("SELECT COUNT(*) FROM music_semantic WHERE validation_status = 'invalid'")
    invalid = cursor.fetchone()[0]

    # 按维度统计违规标签
    cursor.execute("""
        SELECT
            json_extract(invalid_tags, '$.*') as invalid_dimensions
        FROM music_semantic
        WHERE validation_status = 'invalid'
    """)

    invalid_by_dimension = {"mood": 0, "energy": 0, "genre": 0, "style": 0, "scene": 0, "region": 0, "culture": 0, "language": 0}

    for row in cursor.fetchall():
        try:
            invalid_dict = json.loads(row[0]) if row[0] else {}
            for dim, tags in invalid_dict.items():
                if dim in invalid_by_dimension:
                    invalid_by_dimension[dim] += len(tags)
        except:
            pass

    sem_db_context().__exit__(None, None, None)

    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "valid_rate": round(valid / total * 100, 2) if total > 0 else 0,
        "invalid_by_dimension": invalid_by_dimension
    }

@router.post("/validation/revalidate")
def revalidate_song(file_id: str):
    """重新验证单首歌曲的标签

    Args:
        file_id: 歌曲ID

    Returns:
        重新验证结果
    """
    from src.services.tagging_service import TaggingService
    from src.repositories.navidrome_repository import NavidromeRepository

    nav_db_cm = nav_db_context()
    nav_conn = nav_db_cm.__enter__()

    sem_db_cm = sem_db_context()
    sem_conn = sem_db_cm.__enter__()

    nav_repo = NavidromeRepository(nav_conn)
    sem_repo = SemanticRepository(sem_conn)
    service = TaggingService(nav_repo, sem_repo)

    try:
        # 获取歌曲信息
        song = nav_repo.get_song_by_id(file_id)
        if not song:
            return {"success": False, "error": "Song not found"}

        # 重新生成标签
        lyrics = nav_repo.extract_lyrics_text(song.get('lyrics'))
        result = service.generate_tag(
            title=song['title'],
            artist=song['artist'],
            album=song['album'],
            lyrics=lyrics
        )

        # 保存并验证
        is_valid, validation_result = sem_repo.save_song_tags_with_validation(
            file_id=file_id,
            title=song['title'],
            artist=song['artist'],
            album=song['album'],
            tags=result['tags'],
            confidence=result['tags'].get('confidence', 0.0),
            model=get_model()
        )

        nav_db_cm.__exit__(None, None, None)
        sem_db_cm.__exit__(None, None, None)

        return {
            "success": True,
            "is_valid": is_valid,
            "validation_result": validation_result,
            "tags": result['tags']
        }
    except Exception as e:
        nav_db_cm.__exit__(None, None, None)
        sem_db_cm.__exit__(None, None, None)
        return {"success": False, "error": str(e)}
'''

    print("请将以下代码添加到 src/api/routes/tagging/endpoints.py:")
    print(endpoint_code)

if __name__ == '__main__':
    add_invalid_tags_api()
