"""
歌曲数据访问层 - 整合 Navidrome 和 Semantic 数据库的歌曲信息
"""

import sqlite3
from typing import List, Dict, Any, Optional


class SongRepository:
    """歌曲数据访问类 - 整合两个数据库"""

    def __init__(self, nav_conn: sqlite3.Connection, sem_conn: sqlite3.Connection):
        """
        初始化歌曲仓库

        Args:
            nav_conn: Navidrome 数据库连接对象
            sem_conn: 语义数据库连接对象
        """
        self.nav_conn = nav_conn
        self.sem_conn = sem_conn

    def get_song_with_tags(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        获取歌曲及其语义标签

        Args:
            file_id: 歌曲ID

        Returns:
            包含歌曲信息和语义标签的字典，如果不存在则返回 None
        """
        # 从 Navidrome 获取基本信息
        nav_cursor = self.nav_conn.execute("""
            SELECT id, title, artist, album, duration, path
            FROM media_file
            WHERE id = ?
        """, (file_id,))
        nav_row = nav_cursor.fetchone()

        if not nav_row:
            return None

        # 从 Semantic 获取标签
        sem_cursor = self.sem_conn.execute("""
            SELECT mood, energy, scene, region, subculture, genre, confidence
            FROM music_semantic
            WHERE file_id = ?
        """, (file_id,))
        sem_row = sem_cursor.fetchone()

        result = {
            'id': nav_row[0],
            'title': nav_row[1],
            'artist': nav_row[2],
            'album': nav_row[3],
            'duration': nav_row[4],
            'path': nav_row[5],
        }

        if sem_row:
            result.update({
                'mood': sem_row[0],
                'energy': sem_row[1],
                'scene': sem_row[2],
                'region': sem_row[3],
                'subculture': sem_row[4],
                'genre': sem_row[5],
                'confidence': sem_row[6],
            })
        else:
            result.update({
                'mood': None,
                'energy': None,
                'scene': None,
                'region': None,
                'subculture': None,
                'genre': None,
                'confidence': None,
            })

        return result

    def get_songs_with_tags(self, file_ids: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取歌曲及其语义标签

        Args:
            file_ids: 歌曲ID列表

        Returns:
            歌曲列表，每首歌包含基本信息和语义标签
        """
        if not file_ids:
            return []

        placeholders = ','.join('?' * len(file_ids))

        # 从 Navidrome 获取基本信息
        nav_cursor = self.nav_conn.execute(f"""
            SELECT id, title, artist, album, duration, path
            FROM media_file
            WHERE id IN ({placeholders})
        """, file_ids)

        nav_songs = {row[0]: dict(row) for row in nav_cursor.fetchall()}

        # 从 Semantic 获取标签
        sem_cursor = self.sem_conn.execute(f"""
            SELECT file_id, mood, energy, scene, region, subculture, genre, confidence
            FROM music_semantic
            WHERE file_id IN ({placeholders})
        """, file_ids)

        sem_tags = {row[0]: {
            'mood': row[1],
            'energy': row[2],
            'scene': row[3],
            'region': row[4],
            'subculture': row[5],
            'genre': row[6],
            'confidence': row[7],
        } for row in sem_cursor.fetchall()}

        # 合并数据
        result = []
        for file_id in file_ids:
            if file_id in nav_songs:
                song = nav_songs[file_id].copy()
                if file_id in sem_tags:
                    song.update(sem_tags[file_id])
                else:
                    song.update({
                        'mood': None,
                        'energy': None,
                        'scene': None,
                        'region': None,
                        'subculture': None,
                        'genre': None,
                        'confidence': None,
                    })
                result.append(song)

        return result

    def get_all_songs_with_tags(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取所有歌曲及其语义标签

        Args:
            limit: 返回数量限制，None 表示不限制

        Returns:
            歌曲列表，每首歌包含基本信息和语义标签
        """
        limit_clause = f"LIMIT {limit}" if limit else ""

        nav_cursor = self.nav_conn.execute(f"""
            SELECT id, title, artist, album, duration, path
            FROM media_file
            ORDER BY title
            {limit_clause}
        """)

        file_ids = [row[0] for row in nav_cursor.fetchall()]
        return self.get_songs_with_tags(file_ids)

    def search_songs_with_tags(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索歌曲及其语义标签

        Args:
            query: 搜索关键词
            limit: 返回数量限制

        Returns:
            歌曲列表，每首歌包含基本信息和语义标签
        """
        nav_cursor = self.nav_conn.execute("""
            SELECT id, title, artist, album, duration, path
            FROM media_file
            WHERE title LIKE ? OR artist LIKE ? OR album LIKE ?
            ORDER BY title
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))

        file_ids = [row[0] for row in nav_cursor.fetchall()]
        return self.get_songs_with_tags(file_ids)

    def get_songs_by_tags(
        self,
        mood: Optional[str] = None,
        energy: Optional[str] = None,
        genre: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        根据语义标签获取歌曲

        Args:
            mood: 情绪标签
            energy: 能量标签
            genre: 流派标签
            region: 地区标签
            limit: 返回数量限制

        Returns:
            歌曲列表，每首歌包含基本信息和语义标签
        """
        conditions = []
        params = []

        if mood:
            conditions.append("mood = ?")
            params.append(mood)
        if energy:
            conditions.append("energy = ?")
            params.append(energy)
        if genre:
            conditions.append("genre = ?")
            params.append(genre)
        if region:
            conditions.append("region = ?")
            params.append(region)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        sem_cursor = self.sem_conn.execute(f"""
            SELECT file_id
            FROM music_semantic
            WHERE {where_clause}
            ORDER BY RANDOM()
            LIMIT ?
        """, params + [limit])

        file_ids = [row[0] for row in sem_cursor.fetchall()]
        return self.get_songs_with_tags(file_ids)

    def get_songs_by_scene_preset(self, scene_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        根据场景预设获取歌曲

        Args:
            scene_name: 场景名称
            limit: 返回数量限制

        Returns:
            歌曲列表
        """
        # 场景预设定义
        presets = {
            "深夜": {"mood": ["Peaceful", "Sad", "Dreamy", "Chill"], "energy": ["Low"]},
            "运动": {"mood": ["Energetic", "Epic"], "energy": ["High"]},
            "学习": {"mood": ["Peaceful", "Chill"], "energy": ["Low", "Medium"]},
            "开车": {"mood": ["Energetic", "Upbeat", "Groovy"], "energy": ["Medium", "High"]},
            "放松": {"mood": ["Peaceful", "Dreamy", "Chill"], "energy": ["Low"]},
            "派对": {"mood": ["Happy", "Energetic", "Upbeat"], "energy": ["High"]},
            "伤心": {"mood": ["Sad", "Emotional"], "energy": ["Low", "Medium"]},
            "励志": {"mood": ["Epic", "Energetic"], "energy": ["High"]},
        }

        if scene_name not in presets:
            return []

        preset = presets[scene_name]
        mood_list = preset["mood"]
        energy_list = preset["energy"]

        mood_placeholders = ','.join('?' * len(mood_list))
        energy_placeholders = ','.join('?' * len(energy_list))

        sem_cursor = self.sem_conn.execute(f"""
            SELECT file_id
            FROM music_semantic
            WHERE mood IN ({mood_placeholders}) AND energy IN ({energy_placeholders})
            ORDER BY RANDOM()
            LIMIT ?
        """, mood_list + energy_list + [limit])

        file_ids = [row[0] for row in sem_cursor.fetchall()]
        return self.get_songs_with_tags(file_ids)
