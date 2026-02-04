"""
测试标签 API 路由模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient

from src.api.app import app


class TestTaggingAPI:
    """测试标签 API 路由"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def sample_tags(self):
        """示例标签数据"""
        return {
            "mood": "happy",
            "energy": "medium",
            "genre": "pop",
            "region": "Western",
            "subculture": "None",
            "scene": "None",
            "confidence": 0.85
        }

    def test_generate_tag_success(self, client, sample_tags):
        """测试成功生成标签"""
        with patch('src.api.routes.tagging.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_tagging_service = Mock()
            mock_tagging_service.generate_tag = Mock(return_value={
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "Test Album",
                "tags": sample_tags,
                "raw_response": "Mock LLM response"
            })

            with patch('src.api.routes.tagging.endpoints.ServiceFactory.create_tagging_service', return_value=mock_tagging_service):
                request_data = {
                    "title": "Test Song",
                    "artist": "Test Artist",
                    "album": "Test Album"
                }

                response = client.post("/api/v1/tagging/generate", json=request_data)

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["title"] == "Test Song"
                assert data["data"]["tags"]["mood"] == "happy"

    def test_generate_tag_without_album(self, client, sample_tags):
        """测试不提供专辑名称时生成标签"""
        with patch('src.api.routes.tagging.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_tagging_service = Mock()
            mock_tagging_service.generate_tag = Mock(return_value={
                "title": "Test Song",
                "artist": "Test Artist",
                "album": "",
                "tags": sample_tags,
                "raw_response": "Mock LLM response"
            })

            with patch('src.api.routes.tagging.endpoints.ServiceFactory.create_tagging_service', return_value=mock_tagging_service):
                request_data = {
                    "title": "Test Song",
                    "artist": "Test Artist"
                }

                response = client.post("/api/v1/tagging/generate", json=request_data)

                assert response.status_code == 200

    def test_generate_tag_failure(self, client):
        """测试标签生成失败"""
        with patch('src.api.routes.tagging.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_tagging_service = Mock()
            mock_tagging_service.generate_tag = Mock(side_effect=Exception("LLM API Error"))

            with patch('src.api.routes.tagging.endpoints.ServiceFactory.create_tagging_service', return_value=mock_tagging_service):
                request_data = {
                    "title": "Test Song",
                    "artist": "Test Artist"
                }

                response = client.post("/api/v1/tagging/generate", json=request_data)

                assert response.status_code == 500

    def test_batch_generate_tags_success(self, client):
        """测试批量生成标签成功"""
        mock_background_tasks = Mock(spec=BackgroundTasks)

        with patch('src.api.routes.tagging.endpoints.update_tagging_progress') as mock_update:
            with patch('src.api.routes.tagging.endpoints.process_batch_tags') as mock_process:
                request_data = {
                    "songs": [
                        {"title": "Song 1", "artist": "Artist 1"},
                        {"title": "Song 2", "artist": "Artist 2"}
                    ]
                }

                with patch.object(BackgroundTasks, 'add_task') as mock_add_task:
                    response = client.post("/api/v1/tagging/batch", json=request_data)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["data"]["total"] == 2
                    assert data["data"]["status"] == "processing"

    def test_get_tagging_progress(self, client):
        """测试获取标签生成进度"""
        with patch('src.api.routes.tagging.endpoints.get_tagging_progress') as mock_get_progress:
            mock_get_progress.return_value = {
                "total": 100,
                "processed": 50,
                "remaining": 50,
                "status": "processing"
            }

            response = client.get("/api/v1/tagging/progress")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 100
            assert data["processed"] == 50
            assert data["status"] == "processing"

    def test_sync_tags_to_db_success(self, client):
        """测试同步标签到数据库"""
        with patch('src.api.routes.tagging.endpoints.sem_db_context') as mock_sem:
            sem_conn = Mock()
            mock_sem.return_value.__enter__ = Mock(return_value=sem_conn)
            mock_sem.return_value.__exit__ = Mock(return_value=False)

            with patch('src.api.routes.tagging.endpoints.init_semantic_db'):
                with patch('src.api.routes.tagging.endpoints.dbs_context') as mock_dbs:
                    mock_nav_conn = Mock()
                    mock_sem_conn = Mock()
                    mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
                    mock_dbs.return_value.__exit__ = Mock(return_value=False)

                    mock_nav_repo = Mock()
                    mock_nav_repo.get_all_songs = Mock(return_value=[
                        {"id": "song1", "title": "Song 1", "artist": "Artist 1"},
                        {"id": "song2", "title": "Song 2", "artist": "Artist 2"}
                    ])
                    mock_nav_repo.get_total_count = Mock(return_value=2)

                    mock_sem_repo = Mock()
                    mock_sem_conn.execute = Mock(return_value=Mock(
                        fetchall=Mock(return_value=[("song1",)])
                    ))
                    mock_sem_repo.get_total_count = Mock(return_value=1)

                    with patch('src.api.routes.tagging.endpoints.NavidromeRepository', return_value=mock_nav_repo):
                        with patch('src.api.routes.tagging.endpoints.SemanticRepository') as MockSemRepo:
                            mock_sem_instance = Mock()
                            mock_sem_instance.sem_conn = mock_sem_conn
                            mock_sem_instance.get_total_count = Mock(return_value=1)
                            MockSemRepo.return_value = mock_sem_instance

                            response = client.post("/api/v1/tagging/sync")

                            assert response.status_code == 200
                            data = response.json()
                            assert data["success"] is True
                            assert data["data"]["total_songs"] == 2
                            assert data["data"]["processed_songs"] == 1
                            assert data["data"]["new_songs"] == 1

    def test_get_tagging_status(self, client):
        """测试获取标签生成状态"""
        with patch('src.api.routes.tagging.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_nav_repo = Mock()
            mock_nav_repo.get_total_count = Mock(return_value=100)

            mock_sem_repo = Mock()
            mock_sem_repo.get_total_count = Mock(return_value=75)

            with patch('src.api.routes.tagging.endpoints.init_semantic_db'):
                with patch('src.api.routes.tagging.endpoints.NavidromeRepository', return_value=mock_nav_repo):
                    with patch('src.api.routes.tagging.endpoints.SemanticRepository', return_value=mock_sem_repo):
                        with patch('src.api.routes.tagging.endpoints.get_tagging_progress') as mock_get_progress:
                            mock_get_progress.return_value = {
                                "total": 100,
                                "processed": 75,
                                "remaining": 25,
                                "status": "idle"
                            }

                            response = client.get("/api/v1/tagging/status")

                            assert response.status_code == 200
                            data = response.json()
                            assert data["success"] is True
                            assert data["data"]["total"] == 100
                            assert data["data"]["processed"] == 75
                            assert data["data"]["progress"] == 75.0

    def test_preview_tagging(self, client, sample_tags):
        """测试预览标签生成"""
        with patch('src.api.routes.tagging.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_nav_repo = Mock()
            mock_nav_repo.get_all_songs = Mock(return_value=[
                {"title": "Song 1", "artist": "Artist 1", "album": "Album 1"},
                {"title": "Song 2", "artist": "Artist 2", "album": "Album 2"}
            ])

            mock_tagging_service = Mock()
            mock_tagging_service.generate_tag = Mock(return_value={
                "title": "Test Song",
                "artist": "Test Artist",
                "tags": sample_tags
            })

            with patch('src.api.routes.tagging.endpoints.NavidromeRepository', return_value=mock_nav_repo):
                with patch('src.api.routes.tagging.endpoints.ServiceFactory.create_tagging_service', return_value=mock_tagging_service):
                    response = client.get("/api/v1/tagging/preview?limit=2")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert len(data["data"]) == 2

    def test_start_tagging_success(self, client):
        """测试启动标签生成"""
        with patch('src.api.routes.tagging.endpoints.get_tagging_progress') as mock_get_progress:
            mock_get_progress.return_value = {"status": "idle"}

            with patch('src.api.routes.tagging.endpoints.update_tagging_progress'):
                with patch('src.api.routes.tagging.endpoints.broadcast_progress', new_callable=AsyncMock):
                    with patch('src.api.routes.tagging.endpoints.run_tagging_task'):
                        with patch.object(BackgroundTasks, 'add_task') as mock_add_task:
                            response = client.post("/api/v1/tagging/start")

                            assert response.status_code == 200
                            data = response.json()
                            assert data["success"] is True

    def test_start_tagging_already_running(self, client):
        """测试任务已运行时再次启动"""
        with patch('src.api.routes.tagging.endpoints.get_tagging_progress') as mock_get_progress:
            mock_get_progress.return_value = {"status": "processing"}

            response = client.post("/api/v1/tagging/start")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "运行" in data["error"]["message"]

    def test_stop_tagging_success(self, client):
        """测试停止标签生成"""
        with patch('src.api.routes.tagging.endpoints.get_tagging_progress') as mock_get_progress:
            mock_get_progress.return_value = {"status": "processing"}

            with patch('src.api.routes.tagging.endpoints.update_tagging_progress'):
                with patch('src.api.routes.tagging.endpoints.broadcast_progress', new_callable=AsyncMock):
                    response = client.post("/api/v1/tagging/stop")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True

    def test_stop_tagging_no_running_task(self, client):
        """测试没有运行任务时停止"""
        with patch('src.api.routes.tagging.endpoints.get_tagging_progress') as mock_get_progress:
            mock_get_progress.return_value = {"status": "idle"}

            response = client.post("/api/v1/tagging/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_get_tagging_history(self, client):
        """测试获取标签生成历史"""
        with patch('src.api.routes.tagging.endpoints.sem_db_context') as mock_sem:
            sem_conn = Mock()

            # Mock the history query cursor
            mock_cursor = Mock()
            mock_cursor.fetchall = Mock(return_value=[
                ("song1", "Song 1", "Artist 1", "Album 1", "happy", "medium", "None", "Western", "None", "pop", 0.85, "2026-02-01 12:00:00")
            ])

            # Mock the count query cursor
            mock_count_cursor = Mock()
            mock_count_cursor.fetchone = Mock(return_value=[1])

            # Set up execute to return appropriate cursors based on call order
            sem_conn.execute = Mock(side_effect=[mock_cursor, mock_count_cursor])

            mock_sem.return_value.__enter__ = Mock(return_value=sem_conn)
            mock_sem.return_value.__exit__ = Mock(return_value=False)

            response = client.get("/api/v1/tagging/history?limit=10&offset=0")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "items" in data["data"]
            assert "total" in data["data"]

    def test_preview_tagging_limit_validation(self, client):
        """测试预览 limit 参数验证"""
        response = client.get("/api/v1/tagging/preview?limit=25")

        # FastAPI 会自动验证，limit 最大值为 20
        assert response.status_code == 422
