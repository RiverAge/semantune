"""
单元测试 - 数据库连接模块
测试覆盖率目标: 100%
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock, call

from src.core.database import (
    connect_nav_db,
    connect_sem_db,
    connect_dbs,
    nav_db_context,
    sem_db_context,
    dbs_context
)


class TestConnectNavDb:
    """测试connect_nav_db函数"""

    @patch('src.core.database.NAV_DB', ':memory:')
    def test_connect_to_memory_database(self):
        """测试连接内存数据库"""
        conn = connect_nav_db()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row
        conn.close()

    @patch('src.core.database.NAV_DB', ':memory:')
    def test_connect_creates_row_factory(self):
        """测试连接设置了row_factory"""
        conn = connect_nav_db()
        assert conn.row_factory == sqlite3.Row
        conn.close()


class TestConnectSemDb:
    """测试connect_sem_db函数"""

    @patch('src.core.database.SEM_DB', ':memory:')
    def test_connect_to_memory_database(self):
        """测试连接内存数据库"""
        conn = connect_sem_db()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row
        conn.close()

    @patch('src.core.database.SEM_DB', ':memory:')
    def test_connect_creates_row_factory(self):
        """测试连接设置了row_factory"""
        conn = connect_sem_db()
        assert conn.row_factory == sqlite3.Row
        conn.close()


class TestConnectDbs:
    """测试connect_dbs函数"""

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    def test_connect_to_both_databases(self):
        """测试同时连接两个数据库"""
        nav_conn, sem_conn = connect_dbs()

        assert nav_conn is not None
        assert sem_conn is not None
        assert isinstance(nav_conn, sqlite3.Connection)
        assert isinstance(sem_conn, sqlite3.Connection)

        nav_conn.close()
        sem_conn.close()

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    def test_both_databases_have_row_factory(self):
        """测试两个数据库都设置了row_factory"""
        nav_conn, sem_conn = connect_dbs()

        assert nav_conn.row_factory == sqlite3.Row
        assert sem_conn.row_factory == sqlite3.Row

        nav_conn.close()
        sem_conn.close()


class TestNavDbContext:
    """测试nav_db_context上下文管理器"""

    @patch('src.core.database.NAV_DB', ':memory:')
    def test_context_yields_connection(self):
        """测试上下文管理器返回连接对象"""
        with nav_db_context() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row

    @patch('src.core.database.NAV_DB', ':memory:')
    def test_context_closes_connection(self):
        """测试上下文管理器正确关闭连接"""
        with nav_db_context() as conn:
            conn_id = id(conn)
            pass

        # 连接应该被关闭，无法再执行查询
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT * FROM user")

    @patch('src.core.database.NAV_DB', ':memory:')
    def test_context_with_operation(self):
        """测试上下文管理器支持数据库操作"""
        with nav_db_context() as conn:
            # 创建测试表
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")

            # 查询数据
            cursor = conn.execute("SELECT * FROM test WHERE id = 1")
            row = cursor.fetchone()
            assert row[0] == 1
            assert row[1] == "test"

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.connect_nav_db')
    def test_context_closes_on_exception(self, mock_connect):
        """测试上下文管理器在异常时关闭连接"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with pytest.raises(ValueError):
            with nav_db_context() as conn:
                raise ValueError("Test exception")

        mock_conn.close.assert_called_once()

    @patch('src.core.database.NAV_DB', ':memory:')
    def test_context_supports_multiple_operations(self):
        """测试上下文管理器支持多次数据库操作"""
        with nav_db_context() as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")
            conn.execute("INSERT INTO test VALUES (2)")
            cursor = conn.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            assert count == 2


class TestSemDbContext:
    """测试sem_db_context上下文管理器"""

    @patch('src.core.database.SEM_DB', ':memory:')
    def test_context_yields_connection(self):
        """测试上下文管理器返回连接对象"""
        with sem_db_context() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)
            assert conn.row_factory == sqlite3.Row

    @patch('src.core.database.SEM_DB', ':memory:')
    def test_context_closes_connection(self):
        """测试上下文管理器正确关闭连接"""
        with sem_db_context() as conn:
            conn_id = id(conn)
            pass

        # 连接应该被关闭，无法再执行查询
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT * FROM music_semantic")

    @patch('src.core.database.SEM_DB', ':memory:')
    def test_context_with_operation(self):
        """测试上下文管理器支持数据库操作"""
        with sem_db_context() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")

            cursor = conn.execute("SELECT * FROM test WHERE id = 1")
            row = cursor.fetchone()
            assert row[0] == 1
            assert row[1] == "test"

    @patch('src.core.database.SEM_DB', ':memory:')
    @patch('src.core.database.connect_sem_db')
    def test_context_closes_on_exception(self, mock_connect):
        """测试上下文管理器在异常时关闭连接"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with pytest.raises(ValueError):
            with sem_db_context() as conn:
                raise ValueError("Test exception")

        mock_conn.close.assert_called_once()


class TestDbsContext:
    """测试dbs_context上下文管理器"""

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    def test_context_yields_both_connections(self):
        """测试上下文管理器返回两个连接对象"""
        with dbs_context() as (nav_conn, sem_conn):
            assert nav_conn is not None
            assert sem_conn is not None
            assert isinstance(nav_conn, sqlite3.Connection)
            assert isinstance(sem_conn, sqlite3.Connection)
            assert nav_conn.row_factory == sqlite3.Row
            assert sem_conn.row_factory == sqlite3.Row

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    def test_context_closes_both_connections(self):
        """测试上下文管理器正确关闭两个连接"""
        with dbs_context() as (nav_conn, sem_conn):
            nav_id = id(nav_conn)
            sem_id = id(sem_conn)
            pass

        # 两个连接都应该被关闭
        with pytest.raises(sqlite3.ProgrammingError):
            nav_conn.execute("SELECT * FROM user")

        with pytest.raises(sqlite3.ProgrammingError):
            sem_conn.execute("SELECT * FROM music_semantic")

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    def test_context_with_operation_on_both_dbs(self):
        """测试上下文管理器支持两个数据库操作"""
        with dbs_context() as (nav_conn, sem_conn):
            # Navidrome DB 操作
            nav_conn.execute("CREATE TABLE nav_test (id INTEGER)")
            nav_conn.execute("INSERT INTO nav_test VALUES (1)")

            # Semantic DB 操作
            sem_conn.execute("CREATE TABLE sem_test (id INTEGER)")
            sem_conn.execute("INSERT INTO sem_test VALUES (2)")

            # 验证两个DB的数据
            nav_cursor = nav_conn.execute("SELECT * FROM nav_test")
            assert nav_cursor.fetchone()[0] == 1

            sem_cursor = sem_conn.execute("SELECT * FROM sem_test")
            assert sem_cursor.fetchone()[0] == 2

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    @patch('src.core.database.connect_nav_db')
    @patch('src.core.database.connect_sem_db')
    def test_context_closes_both_on_exception(self, mock_connect_sem, mock_connect_nav):
        """测试上下文管理器在异常时关闭两个连接"""
        mock_nav_conn = MagicMock()
        mock_sem_conn = MagicMock()
        mock_connect_nav.return_value = mock_nav_conn
        mock_connect_sem.return_value = mock_sem_conn

        with pytest.raises(ValueError):
            with dbs_context() as (nav_conn, sem_conn):
                raise ValueError("Test exception")

        mock_nav_conn.close.assert_called_once()
        mock_sem_conn.close.assert_called_once()

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    @patch('src.core.database.connect_nav_db')
    @patch('src.core.database.connect_sem_db')
    def test_context_raises_if_close_fails(self, mock_connect_sem, mock_connect_nav):
        """测试上下文管理器在关闭连接失败时抛出异常"""
        mock_nav_conn = MagicMock()
        mock_sem_conn = MagicMock()
        mock_connect_nav.return_value = mock_nav_conn
        mock_connect_sem.return_value = mock_sem_conn

        # 让 nav_conn.close 抛出异常
        mock_nav_conn.close.side_effect = ValueError("Close failed")

        with pytest.raises(ValueError, match="Close failed"):
            with dbs_context() as (nav_conn, sem_conn):
                pass

        # 只有 nav_conn.close 被调用，因为异常发生在那时
        mock_nav_conn.close.assert_called_once()

    @patch('src.core.database.NAV_DB', ':memory:')
    @patch('src.core.database.SEM_DB', ':memory:')
    def test_context_connection_separation(self):
        """测试两个数据库连接是独立的"""
        with dbs_context() as (nav_conn, sem_conn):
            # 创建不同的表
            nav_conn.execute("CREATE TABLE nav_only (id INTEGER)")
            sem_conn.execute("CREATE TABLE sem_only (id INTEGER)")

            # 验证访问各自的表
            nav_cursor = nav_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nav_only'")
            assert nav_cursor.fetchone() is not None

            sem_cursor = sem_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sem_only'")
            assert sem_cursor.fetchone() is not None
