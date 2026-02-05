"""
服务工厂 - 用于创建服务实例

注意：所有工厂方法都需要传入数据库连接参数，不支持自动创建连接。
这是为了避免连接在上下文管理器退出后被关闭的问题。
"""

from typing import Optional
import sqlite3
from src.repositories import (
    NavidromeRepository,
    SemanticRepository,
    UserRepository,
    SongRepository
)
from src.services import (
    TaggingService,
    RecommendService,
    QueryService,
    AnalyzeService,
    ProfileService,
    DuplicateDetectionService
)


class ServiceFactory:
    """服务工厂类"""

    @staticmethod
    def create_tagging_service(nav_conn: sqlite3.Connection, sem_conn: sqlite3.Connection) -> TaggingService:
        """
        创建标签生成服务

        Args:
            nav_conn: Navidrome 数据库连接
            sem_conn: 语义数据库连接

        Returns:
            TaggingService 实例
        """
        nav_repo = NavidromeRepository(nav_conn)
        sem_repo = SemanticRepository(sem_conn)
        return TaggingService(nav_repo, sem_repo)

    @staticmethod
    def create_recommend_service(nav_conn: sqlite3.Connection, sem_conn: sqlite3.Connection) -> RecommendService:
        """
        创建推荐服务

        Args:
            nav_conn: Navidrome 数据库连接
            sem_conn: 语义数据库连接

        Returns:
            RecommendService 实例
        """
        nav_repo = UserRepository(nav_conn)
        sem_repo = SemanticRepository(sem_conn)
        song_repo = SongRepository(nav_conn, sem_conn)
        profile_service = ProfileService(nav_repo, sem_repo)
        return RecommendService(nav_repo, sem_repo, song_repo, profile_service)

    @staticmethod
    def create_query_service(nav_conn: sqlite3.Connection, sem_conn: sqlite3.Connection) -> QueryService:
        """
        创建查询服务

        Args:
            nav_conn: Navidrome 数据库连接
            sem_conn: 语义数据库连接

        Returns:
            QueryService 实例
        """
        song_repo = SongRepository(nav_conn, sem_conn)
        return QueryService(song_repo)

    @staticmethod
    def create_analyze_service(sem_conn: sqlite3.Connection) -> AnalyzeService:
        """
        创建分析服务

        Args:
            sem_conn: 语义数据库连接

        Returns:
            AnalyzeService 实例
        """
        sem_repo = SemanticRepository(sem_conn)
        return AnalyzeService(sem_repo)

    @staticmethod
    def create_profile_service(nav_conn: sqlite3.Connection, sem_conn: sqlite3.Connection) -> ProfileService:
        """
        创建用户画像服务

        Args:
            nav_conn: Navidrome 数据库连接
            sem_conn: 语义数据库连接

        Returns:
            ProfileService 实例
        """
        nav_repo = UserRepository(nav_conn)
        sem_repo = SemanticRepository(sem_conn)
        return ProfileService(nav_repo, sem_repo)

    @staticmethod
    def create_duplicate_detection_service(nav_conn: sqlite3.Connection) -> DuplicateDetectionService:
        """
        创建重复检测服务

        Args:
            nav_conn: Navidrome 数据库连接

        Returns:
            DuplicateDetectionService 实例
        """
        return DuplicateDetectionService(nav_conn)
