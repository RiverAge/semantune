#!/usr/bin/env python3
"""添加验证API端点到endpoints.py"""

endpoint_code = '''

# ==================== 标签验证相关端点 ====================

@router.get("/validation/invalid")
def get_invalid_tags(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """获取验证失败的歌曲列表

    Args:
        limit: 返回数量，默认50，最大200
        offset: 偏移量，默认0

    Returns:
        验证失败的歌曲列表
    """
    try:
        with sem_db_context() as conn:
            cursor = conn.cursor()

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

        return ApiResponse.success(data={
            "total": len(results),
            "limit": limit,
            "offset": offset,
            "data": results
        })

    except Exception as e:
        logger.error(f"获取验证失败记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation/stats")
def get_validation_stats():
    """获取验证统计信息

    Returns:
        验证统计信息
    """
    try:
        with sem_db_context() as conn:
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
            invalid_by_dimension = {"mood": 0, "energy": 0, "genre": 0, "style": 0, "scene": 0, "region": 0, "culture": 0, "language": 0}

            cursor.execute("""
                SELECT invalid_tags
                FROM music_semantic
                WHERE validation_status = 'invalid'
            """)

            for row in cursor.fetchall():
                try:
                    invalid_dict = json.loads(row[0]) if row[0] else {}
                    for dim, tags in invalid_dict.items():
                        if dim in invalid_by_dimension:
                            invalid_by_dimension[dim] += len(tags)
                except:
                    pass

        return ApiResponse.success(data={
            "total": total,
            "valid": valid,
            "invalid": invalid,
            "valid_rate": round(valid / total * 100, 2) if total > 0 else 0,
            "invalid_by_dimension": invalid_by_dimension
        })

    except Exception as e:
        logger.error(f"获取验证统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validation/revalidate/{file_id}")
def revalidate_song(file_id: str):
    """重新验证单首歌曲的标签

    Args:
        file_id: 歌曲ID

    Returns:
        重新验证结果
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)
            tagging_service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)

            # 获取歌曲信息
            songs = nav_repo.search_by_id(file_id)
            if not songs:
                raise HTTPException(status_code=404, detail="Song not found")

            song = songs[0]

            # 重新生成标签
            lyrics = nav_repo.extract_lyrics_text(song.get('lyrics'))
            result = tagging_service.generate_tag(
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

            return ApiResponse.success(data={
                "success": True,
                "is_valid": is_valid,
                "validation_result": validation_result,
                "tags": result['tags']
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新验证歌曲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
'''

with open('src/api/routes/tagging/endpoints.py', 'a', encoding='utf-8') as f:
    f.write(endpoint_code)

print('已添加验证API端点到 endpoints.py')
