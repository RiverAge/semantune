"""
重复检测服务 - 检测 Navidrome 中的重复项
"""
from typing import Dict, Any, List


class DuplicateDetectionService:
    """重复检测服务类"""

    def __init__(self, nav_conn):
        """
        初始化重复检测服务

        Args:
            nav_conn: Navidrome 数据库连接对象
        """
        self.nav_conn = nav_conn

    def detect_duplicate_songs(self) -> Dict[str, Any]:
        """
        检测重复歌曲
        基于文件大小（size）判断重复

        Returns:
            重复歌曲检测结果
        """
        cursor = self.nav_conn.execute("""
            SELECT
                size,
                COUNT(*) as count,
                GROUP_CONCAT(id, ',') as song_ids,
                GROUP_CONCAT(path, '|||') as paths,
                GROUP_CONCAT(title, ',') as titles,
                GROUP_CONCAT(artist, ',') as artists,
                GROUP_CONCAT(album, ',') as albums
            FROM media_file
            WHERE size > 0
            GROUP BY size
            HAVING count > 1
            ORDER BY count DESC
        """)

        duplicates = []
        for row in cursor.fetchall():
            song_ids = row['song_ids'].split(',')
            paths = row['paths'].split('|||')
            titles = row['titles'].split(',')
            artists = row['artists'].split(',')
            albums = row['albums'].split(',')

            duplicates.append({
                'size': row['size'],
                'count': row['count'],
                'songs': [
                    {
                        'id': song_id,
                        'path': path,
                        'title': title,
                        'artist': artist,
                        'album': album
                    }
                    for song_id, path, title, artist, album in zip(song_ids, paths, titles, artists, albums)
                ]
            })

        return {
            'type': 'duplicate_songs',
            'total_groups': len(duplicates),
            'duplicates': duplicates
        }

    def detect_duplicate_albums(self) -> Dict[str, Any]:
        """
        检测重复专辑
        基于同一艺术家的相同专辑名称判断重复
        专辑可能因为发行时间不同而被拆分

        Returns:
            重复专辑检测结果
        """
        cursor = self.nav_conn.execute("""
            SELECT
                name,
                album_artist,
                COUNT(*) as album_count,
                GROUP_CONCAT(id, ',') as album_ids,
                GROUP_CONCAT(DISTINCT date) as dates,
                GROUP_CONCAT(DISTINCT min_year) as years,
                SUM(song_count) as total_songs
            FROM album
            WHERE name != '' AND album_artist != ''
            GROUP BY name, album_artist
            HAVING album_count > 1
            ORDER BY album_count DESC
        """)

        duplicates = []
        for row in cursor.fetchall():
            album_ids = row['album_ids'].split(',')
            dates = row['dates'].split(',') if row['dates'] else []
            years = row['years'].split(',') if row['years'] else []

            duplicate_albums = []
            for idx, album_id in enumerate(album_ids):
                album_detail = self.nav_conn.execute("""
                    SELECT id, name, album_artist, min_year, max_year, song_count, date
                    FROM album
                    WHERE id = ?
                """, (album_id,)).fetchone()

                duplicate_albums.append({
                    'id': album_id,
                    'name': album_detail['name'],
                    'album_artist': album_detail['album_artist'],
                    'min_year': album_detail['min_year'],
                    'max_year': album_detail['max_year'],
                    'song_count': album_detail['song_count'],
                    'date': album_detail['date']
                })

            duplicates.append({
                'album': row['name'],
                'album_artist': row['album_artist'],
                'count': row['album_count'],
                'total_songs': row['total_songs'],
                'albums': duplicate_albums
            })

        return {
            'type': 'duplicate_albums',
            'total_groups': len(duplicates),
            'duplicates': duplicates
        }

    def detect_duplicate_songs_in_album(self) -> Dict[str, Any]:
        """
        检测同一专辑中的重复歌曲
        基于媒体文件路径（path）判断重复

        Returns:
            专辑内重复歌曲检测结果
        """
        cursor = self.nav_conn.execute("""
            SELECT
                path,
                COUNT(*) as count,
                GROUP_CONCAT(id, ',') as song_ids,
                GROUP_CONCAT(album_id, ',') as album_ids,
                GROUP_CONCAT(album, ',') as albums,
                GROUP_CONCAT(album_artist, ',') as album_artists,
                GROUP_CONCAT(title, ',') as titles
            FROM media_file
            WHERE path != ''
            GROUP BY path
            HAVING count > 1
            ORDER BY count DESC
        """)

        duplicates = []
        for row in cursor.fetchall():
            song_ids = row['song_ids'].split(',')
            album_ids = row['album_ids'].split(',')
            albums = row['albums'].split(',')
            album_artists = row['album_artists'].split(',')
            titles = row['titles'].split(',')

            duplicates.append({
                'path': row['path'],
                'count': row['count'],
                'songs': [
                    {
                        'id': song_id,
                        'album_id': album_id,
                        'album': album,
                        'album_artist': album_artist,
                        'title': title
                    }
                    for song_id, album_id, album, album_artist, title in zip(
                        song_ids, album_ids, albums, album_artists, titles
                    )
                ]
            })

        return {
            'type': 'duplicate_songs_in_album',
            'total_groups': len(duplicates),
            'duplicates': duplicates
        }

    def detect_all_duplicates(self) -> Dict[str, Any]:
        """
        检测所有类型的重复

        Returns:
            所有重复检测结果的汇总
        """
        duplicate_songs = self.detect_duplicate_songs()
        duplicate_albums = self.detect_duplicate_albums()
        duplicate_songs_in_album = self.detect_duplicate_songs_in_album()

        return {
            'duplicate_songs': duplicate_songs,
            'duplicate_albums': duplicate_albums,
            'duplicate_songs_in_album': duplicate_songs_in_album,
            'summary': {
                'duplicate_song_groups': duplicate_songs['total_groups'],
                'duplicate_album_groups': duplicate_albums['total_groups'],
                'duplicate_songs_in_album_groups': duplicate_songs_in_album['total_groups'],
                'total_issues': (
                    duplicate_songs['total_groups'] + 
                    duplicate_albums['total_groups'] + 
                    duplicate_songs_in_album['total_groups']
                )
            }
        }
