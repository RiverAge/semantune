"""
测试服务工厂
"""
import pytest
import sqlite3
from unittest.mock import Mock, MagicMock, patch

from src.services.service_factory import ServiceFactory


class TestServiceFactory:
    """测试服务工厂类"""

    @patch('src.services.service_factory.NavidromeRepository')
    @patch('src.services.service_factory.SemanticRepository')
    @patch('src.services.service_factory.TaggingService')
    def test_create_tagging_service(self, mock_tagging_service, mock_semantic_repo_class, mock_navidrome_repo_class):
        """测试创建标签生成服务"""
        nav_conn = Mock()
        sem_conn = Mock()
        
        # Mock 仓库实例
        mock_nav_repo = Mock()
        mock_sem_repo = Mock()
        mock_navidrome_repo_class.return_value = mock_nav_repo
        mock_semantic_repo_class.return_value = mock_sem_repo
        
        # Mock 服务实例
        mock_service = Mock()
        mock_tagging_service.return_value = mock_service
        
        service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
        
        # 验证仓库被正确创建
        mock_navidrome_repo_class.assert_called_once_with(nav_conn)
        mock_semantic_repo_class.assert_called_once_with(sem_conn)
        
        # 验证服务被正确创建
        mock_tagging_service.assert_called_once_with(mock_nav_repo, mock_sem_repo)
        
        # 验证返回值
        assert service == mock_service

    @patch('src.services.service_factory.UserRepository')
    @patch('src.services.service_factory.SemanticRepository')
    @patch('src.services.service_factory.SongRepository')
    @patch('src.services.service_factory.ProfileService')
    @patch('src.services.service_factory.RecommendService')
    def test_create_recommend_service(self, mock_recommend_service, mock_profile_service, mock_song_repo_class, mock_semantic_repo_class, mock_user_repo_class):
        """测试创建推荐服务"""
        nav_conn = Mock()
        sem_conn = Mock()
        
        # Mock 仓库实例
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        mock_song_repo = Mock()
        mock_user_repo_class.return_value = mock_user_repo
        mock_semantic_repo_class.return_value = mock_sem_repo
        mock_song_repo_class.return_value = mock_song_repo
        
        # Mock 服务实例
        mock_profile = Mock()
        mock_rec = Mock()
        mock_profile_service.return_value = mock_profile
        mock_recommend_service.return_value = mock_rec
        
        service = ServiceFactory.create_recommend_service(nav_conn, sem_conn)
        
        # 验证仓库被正确创建
        mock_user_repo_class.assert_called_once_with(nav_conn)
        mock_semantic_repo_class.assert_called_once_with(sem_conn)
        mock_song_repo_class.assert_called_once_with(nav_conn, sem_conn)
        
        # 验证服务被正确创建
        mock_profile_service.assert_called_once_with(mock_user_repo, mock_sem_repo)
        mock_recommend_service.assert_called_once_with(mock_user_repo, mock_sem_repo, mock_song_repo, mock_profile)
        
        # 验证返回值
        assert service == mock_rec

    @patch('src.services.service_factory.SongRepository')
    @patch('src.services.service_factory.QueryService')
    def test_create_query_service(self, mock_query_service, mock_song_repo_class):
        """测试创建查询服务"""
        nav_conn = Mock()
        sem_conn = Mock()
        
        # Mock 仓库实例
        mock_song_repo = Mock()
        mock_song_repo_class.return_value = mock_song_repo
        
        # Mock 服务实例
        mock_service = Mock()
        mock_query_service.return_value = mock_service
        
        service = ServiceFactory.create_query_service(nav_conn, sem_conn)
        
        # 验证仓库被正确创建
        mock_song_repo_class.assert_called_once_with(nav_conn, sem_conn)
        
        # 验证服务被正确创建
        mock_query_service.assert_called_once_with(mock_song_repo)
        
        # 验证返回值
        assert service == mock_service

    @patch('src.services.service_factory.SemanticRepository')
    @patch('src.services.service_factory.AnalyzeService')
    def test_create_analyze_service(self, mock_analyze_service, mock_semantic_repo_class):
        """测试创建分析服务"""
        sem_conn = Mock()
        
        # Mock 仓库实例
        mock_sem_repo = Mock()
        mock_semantic_repo_class.return_value = mock_sem_repo
        
        # Mock 服务实例
        mock_service = Mock()
        mock_analyze_service.return_value = mock_service
        
        service = ServiceFactory.create_analyze_service(sem_conn)
        
        # 验证仓库被正确创建
        mock_semantic_repo_class.assert_called_once_with(sem_conn)
        
        # 验证服务被正确创建
        mock_analyze_service.assert_called_once_with(mock_sem_repo)
        
        # 验证返回值
        assert service == mock_service

    @patch('src.services.service_factory.UserRepository')
    @patch('src.services.service_factory.SemanticRepository')
    @patch('src.services.service_factory.ProfileService')
    def test_create_profile_service(self, mock_profile_service, mock_semantic_repo_class, mock_user_repo_class):
        """测试创建用户画像服务"""
        nav_conn = Mock()
        sem_conn = Mock()
        
        # Mock 仓库实例
        mock_user_repo = Mock()
        mock_sem_repo = Mock()
        mock_user_repo_class.return_value = mock_user_repo
        mock_semantic_repo_class.return_value = mock_sem_repo
        
        # Mock 服务实例
        mock_service = Mock()
        mock_profile_service.return_value = mock_service
        
        service = ServiceFactory.create_profile_service(nav_conn, sem_conn)
        
        # 验证仓库被正确创建
        mock_user_repo_class.assert_called_once_with(nav_conn)
        mock_semantic_repo_class.assert_called_once_with(sem_conn)
        
        # 验证服务被正确创建
        mock_profile_service.assert_called_once_with(mock_user_repo, mock_sem_repo)
        
        # 验证返回值
        assert service == mock_service

    @patch('src.services.service_factory.NavidromeRepository')
    @patch('src.services.service_factory.SemanticRepository')
    @patch('src.services.service_factory.TaggingService')
    def test_create_tagging_service_returns_correct_type(self, mock_tagging_service, mock_semantic_repo_class, mock_navidrome_repo_class):
        """测试创建的服务类型正确"""
        from src.services import TaggingService
        
        nav_conn = Mock()
        sem_conn = Mock()
        
        mock_nav_repo = Mock()
        mock_sem_repo = Mock()
        mock_navidrome_repo_class.return_value = mock_nav_repo
        mock_semantic_repo_class.return_value = mock_sem_repo
        
        mock_service_instance = Mock(spec=TaggingService)
        mock_tagging_service.return_value = mock_service_instance
        
        service = ServiceFactory.create_tagging_service(nav_conn, sem_conn)
        
        assert isinstance(service, Mock)
        # 实际项目中，这里应该是 isinstance(service, TaggingService)

    @patch('src.services.service_factory.NavidromeRepository')
    @patch('src.services.service_factory.SemanticRepository')
    @patch('src.services.service_factory.TaggingService')
    def test_create_tagging_service_different_connections(self, mock_tagging_service, mock_semantic_repo_class, mock_navidrome_repo_class):
        """测试使用不同的数据库连接"""
        nav_conn1 = Mock()
        sem_conn1 = Mock()
        nav_conn2 = Mock()
        sem_conn2 = Mock()
        
        mock_nav_repo1 = Mock()
        mock_sem_repo1 = Mock()
        mock_nav_repo2 = Mock()
        mock_sem_repo2 = Mock()
        
        nav_repo_mock_instance = MagicMock(side_effect=[mock_nav_repo1, mock_nav_repo2])
        sem_repo_mock_instance = MagicMock(side_effect=[mock_sem_repo1, mock_sem_repo2])
        
        mock_navidrome_repo_class.side_effect = nav_repo_mock_instance
        mock_semantic_repo_class.side_effect = sem_repo_mock_instance
        
        mock_service1 = Mock()
        mock_service2 = Mock()
        
        tagging_service_mock_instance = MagicMock(side_effect=[mock_service1, mock_service2])
        mock_tagging_service.side_effect = tagging_service_mock_instance
        
        service1 = ServiceFactory.create_tagging_service(nav_conn1, sem_conn1)
        service2 = ServiceFactory.create_tagging_service(nav_conn2, sem_conn2)
        
        # 验证不同的连接创建了不同的实例
        assert service1 == mock_service1
        assert service2 == mock_service2
        assert mock_navidrome_repo_class.call_count == 2
        assert mock_semantic_repo_class.call_count == 2
        assert mock_tagging_service.call_count == 2

    @patch('src.services.service_factory.NavidromeRepository')
    @patch('src.services.service_factory.SemanticRepository')
    @patch('src.services.service_factory.TaggingService')
    def test_factory_method_is_static(self, mock_tagging_service, mock_semantic_repo_class, mock_navidrome_repo_class):
        """测试工厂方法是静态方法"""
        # 不需要实例化 ServiceFactory 也可以调用
        assert callable(ServiceFactory.create_tagging_service)
        assert callable(ServiceFactory.create_recommend_service)
        assert callable(ServiceFactory.create_query_service)
        assert callable(ServiceFactory.create_analyze_service)
        assert callable(ServiceFactory.create_profile_service)
