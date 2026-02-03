"""
Repository 层集成测试
测试 Repository 层与数据库的实际交互
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.core.schema import init_semantic_db
from src.core.database import nav_db_context, sem_db_context
from src.repositories.semantic_repository import SemanticRepository
from src.repositories.navidrome_repository import NavidromeRepository
from src.repositories.user_repository import UserRepository
from src.repositories.song_repository import SongRepository


class TestSemanticRepositoryIntegration:
    """SemanticRepository 集成测试"""

    @pytest.fixture
    def semantic_db(self, temp_dir):
        """创建临时语义数据库"""
        db_path = temp_dir / "test_semantic.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        init_semantic_db(conn)
        conn.commit()
        yield conn
        conn.close()

    def test_save_and_get_song_tags(self, semantic_db):
        """测试保存和获取歌曲标签"""
        repo = SemanticRepository(semantic_db)

        # 保存标签
        repo.save_song_tags(
            file_id="song_001",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            tags={
                "mood": "happy",
                "energy": "medium",
                "genre": "pop",
                "region": "Western",
                "subculture": "None",
                "scene": "None"
            },
            confidence=0.85,
            model="test-model"
        )

        # 获取标签
        tags = repo.get_song_tags("song_001")

        assert tags is not None
        assert tags["mood"] == "happy"
        assert tags["energy"] == "medium"
        assert tags["genre"] == "pop"
        assert tags["region"] == "Western"

    def test_get_all_songs(self, semantic_db):
        """测试获取所有歌曲"""
        repo = SemanticRepository(semantic_db)

        # 添加多首歌曲
        for i in range(3):
            repo.save_song_tags(
                file_id=f"song_{i:03d}",
                title=f"Song {i}",
                artist=f"Artist {i}",
                album=f"Album {i}",
                tags={"mood": "happy", "energy": "medium", "genre": "pop"},
                confidence=0.8 + i * 0.05,
                model="test-model"
            )

        songs = repo.get_all_songs()

        assert len(songs) == 3
        assert songs[0]["file_id"] == "song_000"
        assert songs[1]["file_id"] == "song_001"
        assert songs[2]["file_id"] == "song_002"

    def test_query_by_mood(self, semantic_db):
        """测试按情绪查询"""
        repo = SemanticRepository(semantic_db)

        # 添加不同情绪的歌曲
        songs_data = [
            ("song_1", "Song 1", "happy"),
            ("song_2", "Song 2", "happy"),
            ("song_3", "Song 3", "sad"),
        ]

        for file_id, title, mood in songs_data:
            repo.save_song_tags(
                file_id=file_id,
                title=title,
                artist="Artist",
                album="Album",
                tags={"mood": mood, "energy": "medium", "genre": "pop"},
                confidence=0.85,
                model="test-model"
            )

        happy_songs = repo.query_by_mood("happy")

        assert len(happy_songs) == 2
        assert all(song["mood"] == "happy" for song in happy_songs)

    def test_query_by_tags(self, semantic_db):
        """测试按多个标签组合查询"""
        repo = SemanticRepository(semantic_db)

        # 添加多首歌曲
        repo.save_song_tags(
            file_id="song_1",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            tags={"mood": "happy", "energy": "high", "genre": "pop", "region": "Western"},
            confidence=0.85,
            model="test-model"
        )

        repo.save_song_tags(
            file_id="song_2",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            tags={"mood": "happy", "energy": "low", "genre": "rock", "region": "Western"},
            confidence=0.90,
            model="test-model"
        )

        # 查询 happy + high + pop
        results = repo.query_by_tags(mood="happy", energy="high", genre="pop")

        assert len(results) >= 1
        # 查找结果中包含我们的歌曲
        found = False
        for result in results:
            if result.get("title") == "Song 1":
                found = True
                break
        assert found, "Should find Song 1 with happy/high/pop tags"

    def test_get_songs_by_ids(self, semantic_db):
        """测试根据ID列表获取歌曲"""
        repo = SemanticRepository(semantic_db)

        # 添加歌曲
        for i in range(5):
            repo.save_song_tags(
                file_id=f"song_{i}",
                title=f"Song {i}",
                artist=f"Artist {i}",
                album=f"Album {i}",
                tags={"mood": "happy", "energy": "medium", "genre": "pop"},
                confidence=0.85,
                model="test-model"
            )

        # 获取特定ID的歌曲
        ids_to_get = ["song_1", "song_3", "song_4"]
        songs = repo.get_songs_by_ids(ids_to_get)

        assert len(songs) == 3
        file_ids = [song["file_id"] for song in songs]
        assert "song_1" in file_ids
        assert "song_3" in file_ids
        assert "song_4" in file_ids
        assert "song_0" not in file_ids

    def test_get_distribution(self, semantic_db):
        """测试获取字段分布统计"""
        repo = SemanticRepository(semantic_db)

        # 添加歌曲
        mood_distribution = {"happy": 3, "sad": 2, "epic": 1}
        for mood, count in mood_distribution.items():
            tags = {"mood": mood, "energy": "medium", "genre": "pop"}
            for i in range(count):
                repo.save_song_tags(
                    file_id=f"song_{mood}_{i}",
                    title=f"Song {i}",
                    artist="Artist",
                    album="Album",
                    tags=tags,
                    confidence=0.85,
                    model="test-model"
                )

        distribution = repo.get_distribution("mood")

        # get_distribution 返回的是一个列表
        assert isinstance(distribution, list)
        assert len(distribution) >= 3

        # 验证分布数据 - 找到匹配的项
        dist_by_label = {item["label"]: item["count"] for item in distribution}
        assert dist_by_label["happy"] == 3
        assert dist_by_label["sad"] == 2
        assert dist_by_label["epic"] == 1

    def test_get_total_count(self, semantic_db):
        """测试获取歌曲总数"""
        repo = SemanticRepository(semantic_db)

        assert repo.get_total_count() == 0

        # 添加5首歌曲
        for i in range(5):
            repo.save_song_tags(
                file_id=f"song_{i}",
                title=f"Song {i}",
                artist=f"Artist {i}",
                album=f"Album {i}",
                tags={"mood": "happy", "energy": "medium", "genre": "pop"},
                confidence=0.85,
                model="test-model"
            )

        assert repo.get_total_count() == 5


class TestUserRepositoryIntegration:
    """UserRepository 集成测试"""

    @pytest.fixture
    def navidrome_db(self, temp_dir):
        """创建临时 Navidrome 数据库（简化版，只包含必要的表）"""
        db_path = temp_dir / "test_navidrome.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # 创建简化表结构
        conn.execute("""
            CREATE TABLE user (
                id TEXT PRIMARY KEY,
                user_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE media_file (
                id TEXT PRIMARY KEY,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration INTEGER,
                path TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE annotation (
                item_id TEXT,
                item_type TEXT,
                user_id TEXT,
                play_count INTEGER DEFAULT 0,
                starred INTEGER DEFAULT 0,
                play_date TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE playlist (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE playlist_tracks (
                id TEXT PRIMARY KEY,
                playlist_id TEXT,
                media_file_id TEXT
            )
        """)

        conn.commit()
        yield conn
        conn.close()

    def test_get_all_users(self, navidrome_db):
        """测试获取所有用户"""
        repo = UserRepository(navidrome_db)

        # 添加用户
        users = [
            {"id": "user_1", "user_name": "Alice"},
            {"id": "user_2", "user_name": "Bob"},
            {"id": "user_3", "user_name": "Charlie"}
        ]

        for user in users:
            navidrome_db.execute(
                "INSERT INTO user (id, user_name) VALUES (?, ?)",
                (user["id"], user["user_name"])
            )
        navidrome_db.commit()

        all_users = repo.get_all_users()

        assert len(all_users) == 3
        user_ids = [u["id"] for u in all_users]
        assert "user_1" in user_ids
        assert "user_2" in user_ids
        assert "user_3" in user_ids

    def test_get_first_user(self, navidrome_db):
        """测试获取第一个用户"""
        repo = UserRepository(navidrome_db)

        # 添加多个用户
        for i in range(3):
            navidrome_db.execute(
                "INSERT INTO user (id, user_name) VALUES (?, ?)",
                (f"user_{i}", f"User {i}")
            )
        navidrome_db.commit()

        first_user = repo.get_first_user()

        assert first_user is not None
        assert first_user["id"] == "user_0"

    def test_get_user_songs(self, navidrome_db):
        """测试获取用户歌曲"""
        repo = UserRepository(navidrome_db)

        # 添加用户
        navidrome_db.execute("INSERT INTO user (id, user_name) VALUES (?, ?)", ("user_1", "Alice"))

        # 添加媒体文件
        song_ids = ["song_1", "song_2", "song_3"]
        for song_id in song_ids:
            navidrome_db.execute(
                "INSERT INTO media_file (id, title, artist, album, duration, path) VALUES (?, ?, ?, ?, ?, ?)",
                (song_id, f"Song {song_id}", "Artist", "Album", 180, f"/path/to/{song_id}.mp3")
            )

        # 添加播放记录
        for song_id in song_ids:
            navidrome_db.execute(
                "INSERT INTO annotation (item_id, item_type, user_id, play_count, play_date) VALUES (?, ?, ?, ?, ?)",
                (song_id, "media_file", "user_1", 1, "2026-02-01")
            )

        navidrome_db.commit()

        user_songs = repo.get_user_songs("user_1")

        assert len(user_songs) >= 3
        assert "song_1" in user_songs
        assert "song_2" in user_songs
        assert "song_3" in user_songs


class TestNavidromeRepositoryIntegration:
    """NavidromeRepository 集成测试"""

    @pytest.fixture
    def navidrome_db(self, temp_dir):
        """创建临时 Navidrome 数据库"""
        db_path = temp_dir / "test_navidrome.db"
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        conn.execute("""
            CREATE TABLE media_file (
                id TEXT PRIMARY KEY,
                title TEXT,
                artist TEXT,
                album TEXT,
                duration INTEGER,
                path TEXT
            )
        """)

        conn.commit()
        yield conn
        conn.close()

    def test_get_all_songs(self, navidrome_db):
        """测试获取所有歌曲"""
        repo = NavidromeRepository(navidrome_db)

        # 添加歌曲
        songs = [
            ("song_1", "Song 1", "Artist 1", "Album 1", 180, "/path/to/song1.mp3"),
            ("song_2", "Song 2", "Artist 2", "Album 2", 200, "/path/to/song2.mp3"),
            ("song_3", "Song 3", "Artist 3", "Album 3", 210, "/path/to/song3.mp3")
        ]

        for song_id, title, artist, album, duration, path in songs:
            navidrome_db.execute(
                "INSERT INTO media_file (id, title, artist, album, duration, path) VALUES (?, ?, ?, ?, ?, ?)",
                (song_id, title, artist, album, duration, path)
            )

        navidrome_db.commit()

        all_songs = repo.get_all_songs()

        assert len(all_songs) == 3
        assert all_songs[0]["title"] == "Song 1"
        assert all_songs[1]["title"] == "Song 2"
        assert all_songs[2]["title"] == "Song 3"

    def test_get_total_count(self, navidrome_db):
        """测试获取歌曲总数"""
        repo = NavidromeRepository(navidrome_db)

        # 添加歌曲
        for i in range(10):
            navidrome_db.execute(
                "INSERT INTO media_file (id, title, artist, album, duration, path) VALUES (?, ?, ?, ?, ?, ?)",
                (f"song_{i}", f"Song {i}", f"Artist {i}", f"Album {i}", 180, f"/path/to/song{i}.mp3")
            )

        navidrome_db.commit()

        total = repo.get_total_count()

        assert total == 10


class TestSongRepositoryIntegration:
    """SongRepository 集成测试"""

    @pytest.fixture
    def databases(self, temp_dir):
        """创建临时数据库"""
        nav_db_path = temp_dir / "test_navidrome.db"
        sem_db_path = temp_dir / "test_semantic.db"

        nav_conn = sqlite3.connect(nav_db_path)
        nav_conn.row_factory = sqlite3.Row

        sem_conn = sqlite3.connect(sem_db_path)
        sem_conn.row_factory = sqlite3.Row

        # 创建 Navidrome 表
        nav_conn.execute("""
            CREATE TABLE media_file (
                id TEXT PRIMARY KEY,
                title TEXT,
                artist TEXT,
                album TEXT,
                year INTEGER,
                duration INTEGER
            )
        """)

        # 创建语义表
        init_semantic_db(sem_conn)

        yield nav_conn, sem_conn

        nav_conn.close()
        sem_conn.close()

    def test_get_songs_with_tags(self, databases):
        """测试获取带标签的歌曲"""
        nav_conn, sem_conn = databases

        # 添加 Navidrome 歌曲
        nav_conn.execute(
            "INSERT INTO media_file (id, title, artist, album, duration) VALUES (?, ?, ?, ?, ?)",
            ("song_1", "Test Song", "Test Artist", "Test Album", 180)
        )
        nav_conn.commit()

        # 添加语义标签
        sem_repo = SemanticRepository(sem_conn)
        sem_repo.save_song_tags(
            file_id="song_1",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            tags={"mood": "happy", "energy": "medium", "genre": "pop"},
            confidence=0.85,
            model="test-model"
        )

        # 使用 SongRepository 获取带标签的歌曲
        song_repo = SongRepository(nav_conn, sem_conn)
        songs = song_repo.get_songs_with_tags(["song_1"])

        assert len(songs) == 1
        assert songs[0]["title"] == "Test Song"
        assert songs[0]["mood"] == "happy"
