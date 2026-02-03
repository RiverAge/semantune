"""
服务工厂 - 用于创建服务实例
"""

from src.core.database import nav_db_context, sem_db_context, dbs_context
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
    ProfileService
)


class ServiceFactory:
    """服务工厂类"""

    @staticmethod
    def create_tagging_service(nav_conn=None, sem_conn=None):
        """
        创建标签生成服务

        Args:
            nav_conn: Navidrome 数据库连接（可选）
            sem_conn: 语义数据库连接（可选）
        """
        if nav_conn is None or sem_conn is None:
            with dbs_context() as (nav_conn, sem_conn):
                nav_repo = NavidromeRepository(nav_conn)
                sem_repo = SemanticRepository(sem_conn)
                return TaggingService(nav_repo, sem_repo)
        else:
            nav_repo = NavidromeRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)
            return TaggingService(nav_repo, sem_repo)

    @staticmethod
    def create_recommend_service(nav_conn=None, sem_conn=None):
        """
        创建推荐服务

        Args:
            nav_conn: Navidrome 数据库连接（可选）
            sem_conn: 语义数据库连接（可选）
        """
        if nav_conn is None or sem_conn is None:
            with dbs_context() as (nav_conn, sem_conn):
                nav_repo = UserRepository(nav_conn)
                sem_repo = SemanticRepository(sem_conn)
                song_repo = SongRepository(nav_conn, sem_conn)
                profile_service = ProfileService(nav_repo, sem_repo)
                return RecommendService(nav_repo, sem_repo, song_repo, profile_service)
        else:
            nav_repo = UserRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)
            song_repo = SongRepository(nav_conn, sem_conn)
            profile_service = ProfileService(nav_repo, sem_repo)
            return RecommendService(nav_repo, sem_repo, song_repo, profile_service)

    @staticmethod
    def create_query_service(nav_conn=None, sem_conn=None):
        """
        创建查询服务

        Args:
            nav_conn: Navidrome 数据库连接（可选）
            sem_conn: 语义数据库连接（可选）
        """
        if nav_conn is None or sem_conn is None:
            with dbs_context() as (nav_conn, sem_conn):
                song_repo = SongRepository(nav_conn, sem_conn)
                return QueryService(song_repo)
        else:
            song_repo = SongRepository(nav_conn, sem_conn)
            return QueryService(song_repo)

    @staticmethod
    def create_analyze_service(sem_conn=None):
        """
        创建分析服务

        Args:
            sem_conn: 语义数据库连接（可选）
        """
        if sem_conn is None:
            with sem_db_context() as sem_conn:
                sem_repo = SemanticRepository(sem_conn)
                return AnalyzeService(sem_repo)
        else:
            sem_repo = SemanticRepository(sem_conn)
            return AnalyzeService(sem_repo)

    @staticmethod
    def create_profile_service(nav_conn=None, sem_conn=None):
        """
        创建用户画像服务

        Args:
            nav_conn: Navidrome 数据库连接（可选）
            sem_conn: 语义数据库连接（可选）
        """
        if nav_conn is None or sem_conn is None:
            with dbs_context() as (nav_conn, sem_conn):
                nav_repo = UserRepository(nav_conn)
                sem_repo = SemanticRepository(sem_conn)
                return ProfileService(nav_repo, sem_repo)
        else:
            nav_repo = UserRepository(nav_conn)
            sem_repo = SemanticRepository(sem_conn)
            return ProfileService(nav_repo, sem_repo)
