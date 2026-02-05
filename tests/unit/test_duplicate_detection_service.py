"""
重复检测服务单元测试
"""
import pytest
import sqlite3
from src.services.duplicate_detection_service import DuplicateDetectionService


@pytest.fixture
def test_nav_conn():
    """创建测试用 Navidrome 数据库连接"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        CREATE TABLE media_file (
            id varchar(255) not null primary key,
            path varchar(255) default '' not null,
            title varchar(255) default '' not null,
            album varchar(255) default '' not null,
            artist varchar(255) default '' not null,
            album_id varchar(255) default '' not null,
            album_artist varchar(255) default '' not null,
            track_number integer default 0 not null,
            size integer default 0 not null
        )
    """)

    cursor.execute("""
        CREATE TABLE album (
            id varchar(255) not null primary key,
            name varchar(255) default '' not null,
            album_artist varchar(255) default '' not null,
            min_year int default 0 not null,
            max_year integer default 0 not null,
            song_count integer default 0 not null,
            date varchar(255) default '' not null
        )
    """)

    conn.commit()
    yield conn
    conn.close()


def test_detect_duplicate_songs_empty(test_nav_conn):
    """测试空库的重复歌曲检测"""
    service = DuplicateDetectionService(test_nav_conn)
    result = service.detect_duplicate_songs()

    assert result['type'] == 'duplicate_songs'
    assert result['total_groups'] == 0
    assert result['duplicates'] == []


def test_detect_duplicate_songs(test_nav_conn):
    """测试重复歌曲检测（基于size）"""
    service = DuplicateDetectionService(test_nav_conn)

    test_nav_conn.executemany(
        "INSERT INTO media_file (id, title, artist, album, path, album_id, album_artist, track_number, size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("song1", "Test Song", "Artist A", "Album A", "/path1.mp3", "album1", "Artist A", 1, 1000),
            ("song2", "Another Song", "Artist B", "Album B", "/path2.mp3", "album2", "Artist B", 1, 1000),
            ("song3", "Different Song", "Artist C", "Album C", "/path3.mp3", "album3", "Artist C", 1, 2000),
        ]
    )
    test_nav_conn.commit()

    result = service.detect_duplicate_songs()

    assert result['type'] == 'duplicate_songs'
    assert result['total_groups'] == 1
    assert len(result['duplicates']) == 1
    assert result['duplicates'][0]['size'] == 1000
    assert result['duplicates'][0]['count'] == 2


def test_detect_duplicate_albums_empty(test_nav_conn):
    """测试空库的重复专辑检测"""
    service = DuplicateDetectionService(test_nav_conn)
    result = service.detect_duplicate_albums()

    assert result['type'] == 'duplicate_albums'
    assert result['total_groups'] == 0
    assert result['duplicates'] == []


def test_detect_duplicate_albums(test_nav_conn):
    """测试重复专辑检测"""
    service = DuplicateDetectionService(test_nav_conn)

    cursor = test_nav_conn.executemany(
        "INSERT INTO album (id, name, album_artist, min_year, max_year, song_count, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("album1", "Test Album", "Artist A", 2020, 2020, 10, "2020"),
            ("album2", "Test Album", "Artist A", 2021, 2021, 8, "2021"),
            ("album3", "Different Album", "Artist B", 2022, 2022, 12, "2022"),
        ]
    )
    test_nav_conn.commit()

    result = service.detect_duplicate_albums()

    assert result['type'] == 'duplicate_albums'
    assert result['total_groups'] == 1
    assert len(result['duplicates']) == 1
    assert result['duplicates'][0]['album'] == "Test Album"
    assert result['duplicates'][0]['album_artist'] == "Artist A"
    assert result['duplicates'][0]['count'] == 2


def test_detect_duplicate_songs_in_album_empty(test_nav_conn):
    """测试空库的专辑内重复歌曲检测"""
    service = DuplicateDetectionService(test_nav_conn)
    result = service.detect_duplicate_songs_in_album()

    assert result['type'] == 'duplicate_songs_in_album'
    assert result['total_groups'] == 0
    assert result['duplicates'] == []


def test_detect_duplicate_songs_in_album(test_nav_conn):
    """测试专辑内重复歌曲检测（基于path）"""
    service = DuplicateDetectionService(test_nav_conn)

    test_nav_conn.executemany(
        "INSERT INTO media_file (id, title, artist, album, path, album_id, album_artist, track_number, size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("song1", "Test Song 1", "Artist A", "Album A", "/music/song.mp3", "album1", "Artist A", 1, 1000),
            ("song2", "Test Song 2", "Artist A", "Album A", "/music/song.mp3", "album2", "Artist A", 2, 1000),
            ("song3", "Different Song", "Artist A", "Album A", "/music/other.mp3", "album1", "Artist A", 3, 2000),
        ]
    )
    test_nav_conn.commit()

    result = service.detect_duplicate_songs_in_album()

    assert result['type'] == 'duplicate_songs_in_album'
    assert result['total_groups'] == 1
    assert len(result['duplicates']) == 1
    assert result['duplicates'][0]['path'] == "/music/song.mp3"
    assert result['duplicates'][0]['count'] == 2


def test_detect_all_duplicates(test_nav_conn):
    """测试检测所有类型重复"""
    service = DuplicateDetectionService(test_nav_conn)

    test_nav_conn.executemany(
        "INSERT INTO album (id, name, album_artist, min_year, max_year, song_count, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("album1", "Test Album", "Artist A", 2020, 2020, 10, "2020"),
            ("album2", "Test Album", "Artist A", 2021, 2021, 8, "2021"),
        ]
    )

    test_nav_conn.executemany(
        "INSERT INTO media_file (id, title, artist, album, path, album_id, album_artist, track_number, size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("song1", "Duplicated Song", "Artist A", "Test Album", "/path1.mp3", "album1", "Artist A", 1, 1000),
            ("song2", "Another Song", "Artist B", "Test Album", "/path2.mp3", "album2", "Artist A", 1, 1000),
            ("song3", "Repeated Song", "Artist C", "Album B", "/path3.mp3", "album3", "Artist B", 1, 2000),
            ("song4", "Repeated Song 2", "Artist D", "Album C", "/path3.mp3", "album4", "Artist B", 2, 2000),
        ]
    )
    test_nav_conn.commit()

    result = service.detect_all_duplicates()

    assert 'summary' in result
    assert 'duplicate_songs' in result
    assert 'duplicate_albums' in result
    assert 'duplicate_songs_in_album' in result

    assert result['summary']['duplicate_album_groups'] == 1
    assert result['summary']['duplicate_song_groups'] == 2
    assert result['summary']['duplicate_songs_in_album_groups'] == 1
