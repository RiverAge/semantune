"""
测试 src.services.tagging_service 模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.tagging_service import TaggingService


class TestTaggingService:
    """测试 TaggingService 类"""

    def test_tagging_service_initialization(self, mock_nav_repo, mock_sem_repo):
        """测试 TaggingService 初始化"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        assert service.nav_repo == mock_nav_repo
        assert service.sem_repo == mock_sem_repo
        assert service.llm_client is not None

    def test_generate_tag_success(self, mock_nav_repo, mock_sem_repo, sample_tags):
        """测试成功生成标签"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        # Mock LLM 客户端返回
        service.llm_client.call_llm_api = Mock(return_value=(sample_tags, "Mock response"))

        result = service.generate_tag(
            title="Test Song",
            artist="Test Artist",
            album="Test Album"
        )

        assert result["title"] == "Test Song"
        assert result["artist"] == "Test Artist"
        assert result["album"] == "Test Album"
        assert result["tags"] == sample_tags
        assert result["raw_response"] == "Mock response"

    def test_generate_tag_failure(self, mock_nav_repo, mock_sem_repo):
        """测试标签生成失败"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        # Mock LLM 客户端返回空标签
        service.llm_client.call_llm_api = Mock(return_value=(None, "Error response"))

        with pytest.raises(ValueError) as exc_info:
            service.generate_tag(
                title="Test Song",
                artist="Test Artist",
                album="Test Album"
            )

        assert "标签生成失败" in str(exc_info.value)

    def test_generate_tag_without_album(self, mock_nav_repo, mock_sem_repo, sample_tags):
        """测试不提供专辑名称时生成标签"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        service.llm_client.call_llm_api = Mock(return_value=(sample_tags, "Mock response"))

        result = service.generate_tag(
            title="Test Song",
            artist="Test Artist"
        )

        assert result["title"] == "Test Song"
        assert result["artist"] == "Test Artist"
        assert result["album"] == ""

    def test_batch_generate_tags_success(self, mock_nav_repo, mock_sem_repo, sample_songs, sample_tags):
        """测试批量生成标签成功"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        service.llm_client.call_llm_api = Mock(return_value=(sample_tags, "Mock response"))

        results = service.batch_generate_tags(sample_songs)

        assert len(results) == 3
        assert all(result["success"] for result in results)
        assert all("data" in result for result in results)

    def test_batch_generate_tags_partial_failure(self, mock_nav_repo, mock_sem_repo, sample_songs, sample_tags):
        """测试批量生成标签部分失败"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        # 第一次调用成功，第二次失败，第三次成功
        call_count = [0]

        def mock_call_llm(title, artist, album):
            call_count[0] += 1
            if call_count[0] == 2:
                raise ValueError("API Error")
            return sample_tags, "Mock response"

        service.llm_client.call_llm_api = Mock(side_effect=mock_call_llm)

        results = service.batch_generate_tags(sample_songs)

        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[2]["success"] is True
        assert "error" in results[1]

    def test_batch_generate_tags_empty_list(self, mock_nav_repo, mock_sem_repo):
        """测试批量生成空列表"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        results = service.batch_generate_tags([])

        assert results == []

    def test_process_all_songs_success(self, mock_nav_repo, mock_sem_repo, sample_tags):
        """测试处理所有歌曲成功"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        # Mock 数据库返回
        mock_nav_repo.get_all_songs = Mock(return_value=[
            {"id": "song1", "title": "Song 1", "artist": "Artist 1", "album": "Album 1"},
            {"id": "song2", "title": "Song 2", "artist": "Artist 2", "album": "Album 2"},
            {"id": "song3", "title": "Song 3", "artist": "Artist 3", "album": "Album 3"},
        ])

        # Mock 已标记的歌曲
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[("song1",)])
        mock_sem_repo.sem_conn.execute = Mock(return_value=mock_cursor)

        service.llm_client.call_llm_api = Mock(return_value=(sample_tags, "Mock response"))

        with patch('src.services.tagging_service.MODEL', 'test-model'):
            result = service.process_all_songs()

        assert result["total"] == 3
        assert result["tagged"] == 1
        assert result["processed"] == 2
        assert result["failed"] == 0
        assert result["remaining"] == 0

    def test_process_all_songs_with_failures(self, mock_nav_repo, mock_sem_repo, sample_tags):
        """测试处理所有歌曲时有失败"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_all_songs = Mock(return_value=[
            {"id": "song1", "title": "Song 1", "artist": "Artist 1", "album": "Album 1"},
            {"id": "song2", "title": "Song 2", "artist": "Artist 2", "album": "Album 2"},
        ])

        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[])
        mock_sem_repo.sem_conn.execute = Mock(return_value=mock_cursor)

        # 第一次成功，第二次失败
        call_count = [0]

        def mock_call_llm(title, artist, album):
            call_count[0] += 1
            if call_count[0] == 2:
                raise ValueError("API Error")
            return sample_tags, "Mock response"

        service.llm_client.call_llm_api = Mock(side_effect=mock_call_llm)

        with patch('src.services.tagging_service.MODEL', 'test-model'):
            result = service.process_all_songs()

        assert result["total"] == 2
        assert result["tagged"] == 0
        assert result["processed"] == 1
        assert result["failed"] == 1
        assert result["remaining"] == 0

    def test_process_all_songs_all_tagged(self, mock_nav_repo, mock_sem_repo):
        """测试所有歌曲都已标记"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_all_songs = Mock(return_value=[
            {"id": "song1", "title": "Song 1", "artist": "Artist 1", "album": "Album 1"},
            {"id": "song2", "title": "Song 2", "artist": "Artist 2", "album": "Album 2"},
        ])

        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[("song1",), ("song2",)])
        mock_sem_repo.sem_conn.execute = Mock(return_value=mock_cursor)

        result = service.process_all_songs()

        assert result["total"] == 2
        assert result["tagged"] == 2
        assert result["processed"] == 0
        assert result["failed"] == 0
        assert result["remaining"] == 0

    def test_process_all_songs_empty_database(self, mock_nav_repo, mock_sem_repo):
        """测试数据库为空"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_all_songs = Mock(return_value=[])

        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[])
        mock_sem_repo.sem_conn.execute = Mock(return_value=mock_cursor)

        result = service.process_all_songs()

        assert result["total"] == 0
        assert result["tagged"] == 0
        assert result["processed"] == 0
        assert result["failed"] == 0
        assert result["remaining"] == 0

    def test_get_progress(self, mock_nav_repo, mock_sem_repo):
        """测试获取进度"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_total_count = Mock(return_value=100)
        mock_sem_repo.get_total_count = Mock(return_value=75)

        result = service.get_progress()

        assert result["total"] == 100
        assert result["tagged"] == 75
        assert result["remaining"] == 25
        assert result["percentage"] == 75.0

    def test_get_progress_zero_total(self, mock_nav_repo, mock_sem_repo):
        """测试总数为零时的进度"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_total_count = Mock(return_value=0)
        mock_sem_repo.get_total_count = Mock(return_value=0)

        result = service.get_progress()

        assert result["total"] == 0
        assert result["tagged"] == 0
        assert result["remaining"] == 0
        assert result["percentage"] == 0

    def test_get_progress_all_tagged(self, mock_nav_repo, mock_sem_repo):
        """测试所有歌曲都已标记"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_total_count = Mock(return_value=50)
        mock_sem_repo.get_total_count = Mock(return_value=50)

        result = service.get_progress()

        assert result["total"] == 50
        assert result["tagged"] == 50
        assert result["remaining"] == 0
        assert result["percentage"] == 100.0

    def test_get_progress_none_tagged(self, mock_nav_repo, mock_sem_repo):
        """测试没有歌曲被标记"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_total_count = Mock(return_value=30)
        mock_sem_repo.get_total_count = Mock(return_value=0)

        result = service.get_progress()

        assert result["total"] == 30
        assert result["tagged"] == 0
        assert result["remaining"] == 30
        assert result["percentage"] == 0.0

    def test_save_song_tags_called(self, mock_nav_repo, mock_sem_repo, sample_tags):
        """测试保存歌曲标签被调用"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        mock_nav_repo.get_all_songs = Mock(return_value=[
            {"id": "song1", "title": "Song 1", "artist": "Artist 1", "album": "Album 1"},
        ])

        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[])
        mock_sem_repo.sem_conn.execute = Mock(return_value=mock_cursor)

        service.llm_client.call_llm_api = Mock(return_value=(sample_tags, "Mock response"))

        with patch('src.services.tagging_service.MODEL', 'test-model'):
            service.process_all_songs()

        # 验证 save_song_tags 被调用
        mock_sem_repo.save_song_tags.assert_called_once()
        call_args = mock_sem_repo.save_song_tags.call_args
        assert call_args[1]["file_id"] == "song1"
        assert call_args[1]["title"] == "Song 1"
        assert call_args[1]["artist"] == "Artist 1"
        assert call_args[1]["album"] == "Album 1"
        assert call_args[1]["tags"] == sample_tags
        assert call_args[1]["model"] == "test-model"

    def test_llm_client_call_parameters(self, mock_nav_repo, mock_sem_repo, sample_tags):
        """测试 LLM 客户端调用参数"""
        service = TaggingService(mock_nav_repo, mock_sem_repo)

        service.llm_client.call_llm_api = Mock(return_value=(sample_tags, "Mock response"))

        service.generate_tag(
            title="My Song",
            artist="My Artist",
            album="My Album"
        )

        # 验证 LLM 客户端被正确调用
        service.llm_client.call_llm_api.assert_called_once_with(
            "My Song", "My Artist", "My Album"
        )
