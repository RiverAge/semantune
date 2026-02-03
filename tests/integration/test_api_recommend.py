"""
测试推荐 API 路由模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.routes.recommend.endpoints import get_recommendations, list_users, get_recommendations_get, get_user_profile


class TestRecommendAPI:
    """测试推荐 API 路由"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def sample_user(self):
        """示例用户数据"""
        return {
            "id": "user_123",
            "name": "test_user"
        }

    @pytest.fixture
    def sample_recommendations(self):
        """示例推荐数据"""
        return [
            {
                "file_id": "song1",
                "title": "Test Song 1",
                "artist": "Artist 1",
                "album": "Album 1",
                "mood": "happy",
                "energy": "medium",
                "genre": "pop",
                "region": "Western",
                "confidence": 0.85,
                "similarity": 0.92
            },
            {
                "file_id": "song2",
                "title": "Test Song 2",
                "artist": "Artist 2",
                "album": "Album 2",
                "mood": "epic",
                "energy": "high",
                "genre": "rock",
                "region": "Western",
                "confidence": 0.90,
                "similarity": 0.88
            }
        ]

    def test_post_recommendations_success(self, client, sample_user, sample_recommendations):
        """测试成功获取推荐 (POST 方法)"""
        with patch('src.api.routes.recommend.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_first_user = Mock(return_value=sample_user)
            mock_user_repo.get_user_songs = Mock(return_value=["song1", "song2"])

            mock_recommend_service = Mock()
            mock_recommend_service.recommend = Mock(return_value=sample_recommendations)

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                with patch('src.api.routes.recommend.endpoints.ServiceFactory', return_value=mock_recommend_service):
                    request_data = {
                        "user_id": "user_123",
                        "limit": 30,
                        "filter_recent": True,
                        "diversity": True
                    }

                    response = client.post("/api/v1/recommend/", json=request_data)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert "data" in data
                    assert data["data"]["user_id"] == "user_123"
                    assert len(data["data"]["recommendations"]) == 2

    def test_post_recommendations_no_user_id(self, client, sample_user, sample_recommendations):
        """测试不提供 user_id 时自动选择第一个用户"""
        with patch('src.api.routes.recommend.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_first_user = Mock(return_value=sample_user)
            mock_user_repo.get_user_songs = Mock(return_value=[])

            mock_recommend_service = Mock()
            mock_recommend_service.recommend = Mock(return_value=sample_recommendations)

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                with patch('src.api.routes.recommend.endpoints.ServiceFactory', return_value=mock_recommend_service):
                    request_data = {
                        "limit": 30
                    }

                    response = client.post("/api/v1/recommend/", json=request_data)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["data"]["user_id"] == "user_123"

    def test_post_recommendations_user_not_found(self, client):
        """测试用户不存在"""
        with patch('src.api.routes.recommend.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_first_user = Mock(return_value=None)

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                request_data = {
                    "user_id": "non_existent_user",
                    "limit": 30
                }

                response = client.post("/api/v1/recommend/", json=request_data)

                assert response.status_code == 404

    def test_get_users_list_success(self, client, sample_user):
        """测试成功获取用户列表"""
        with patch('src.api.routes.recommend.endpoints.nav_db_context') as mock_nav:
            mock_nav_conn = Mock()
            mock_nav.return_value.__enter__ = Mock(return_value=mock_nav_conn)
            mock_nav.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_user])

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                response = client.get("/api/v1/recommend/users")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "users" in data["data"]
                assert len(data["data"]["users"]) == 1
                assert data["data"]["users"][0] == "test_user"

    def test_get_recommendations_get_success(self, client, sample_user, sample_recommendations):
        """测试成功获取推荐 (GET 方法)"""
        with patch('src.api.routes.recommend.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_user])

            mock_recommend_service = Mock()
            mock_recommend_service.recommend = Mock(return_value=sample_recommendations)

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                with patch('src.api.routes.recommend.endpoints.ServiceFactory', return_value=mock_recommend_service):
                    response = client.get("/api/v1/recommend/list?username=test_user&limit=30")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert len(data["data"]) == 2
                    assert "reason" in data["data"][0]

    def test_get_recommendations_get_user_not_found(self, client):
        """测试用户不存在 (GET 方法)"""
        with patch('src.api.routes.recommend.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[])

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                response = client.get("/api/v1/recommend/list?username=nonexistent&limit=30")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
                assert "error" in data

    def test_get_user_profile_success(self, client, sample_user):
        """测试成功获取用户画像"""
        with patch('src.api.routes.recommend.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[sample_user])
            mock_user_repo.get_user_songs = Mock(return_value=["song1", "song2"])
            mock_user_repo.get_playlist_songs = Mock(return_value=["song1"])
            mock_nav_conn.execute = Mock(return_value=Mock(fetchall=Mock(return_value=[])))

            mock_profile_service = Mock()
            mock_profile_service.build_user_profile = Mock(return_value={
                "profile": {
                    "mood": {"happy": 0.6, "epic": 0.4},
                    "energy": {"medium": 0.5, "high": 0.5},
                    "genre": {"pop": 0.7, "rock": 0.3}
                },
                "stats": {
                    "total_plays": 10,
                    "unique_songs": 5,
                    "starred_count": 2
                }
            })

            mock_sem_repo = Mock()
            mock_sem_repo.get_songs_by_ids = Mock(return_value=[
                {"artist": "Test Artist", "mood": "happy", "energy": "medium", "genre": "pop"}
            ])

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                with patch('src.api.routes.recommend.endpoints.ServiceFactory', return_value=mock_profile_service):
                    with patch('src.api.routes.recommend.endpoints.SemanticRepository', return_value=mock_sem_repo):
                        response = client.get("/api/v1/recommend/profile/test_user")

                        assert response.status_code == 200
                        data = response.json()
                        assert data["success"] is True
                        assert data["data"]["username"] == "test_user"
                        assert "top_artists" in data["data"]
                        assert "top_moods" in data["data"]

    def test_get_user_profile_user_not_found(self, client):
        """测试获取不存在用户的画像"""
        with patch('src.api.routes.recommend.endpoints.dbs_context') as mock_dbs:
            mock_nav_conn = Mock()
            mock_sem_conn = Mock()
            mock_dbs.return_value.__enter__ = Mock(return_value=(mock_nav_conn, mock_sem_conn))
            mock_dbs.return_value.__exit__ = Mock(return_value=False)

            mock_user_repo = Mock()
            mock_user_repo.get_all_users = Mock(return_value=[])

            with patch('src.api.routes.recommend.endpoints.UserRepository', return_value=mock_user_repo):
                response = client.get("/api/v1/recommend/profile/nonexistent")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False

    def test_get_recommendations_with_limit_validation(self, client):
        """测试 limit 参数验证"""
        response = client.get("/api/v1/recommend/list?username=test_user&limit=150")

        # FastAPI 会自动验证 Query 参数，limit 最大值为 100
        assert response.status_code == 422

    def test_post_recommendations_with_limit_validation(self, client):
        """测试 POST 方法 limit 参数验证"""
        request_data = {
            "limit": 150
        }

        response = client.post("/api/v1/recommend/", json=request_data)

        # FastAPI 会自动验证
        assert response.status_code == 422
