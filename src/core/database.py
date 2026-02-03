"""
数据库连接模块 - 提供上下文管理器支持，防止连接泄漏
"""

import sqlite3
from typing import Tuple, Generator
from contextlib import contextmanager
from config.settings import NAV_DB, SEM_DB


def connect_nav_db() -> sqlite3.Connection:
    """
    连接 Navidrome 数据库
    
    Returns:
        sqlite3.Connection: Navidrome 数据库连接对象，使用 Row 工厂模式
    """
    conn = sqlite3.connect(NAV_DB)
    conn.row_factory = sqlite3.Row
    return conn


def connect_sem_db() -> sqlite3.Connection:
    """
    连接语义数据库
    
    Returns:
        sqlite3.Connection: 语义数据库连接对象，使用 Row 工厂模式
    """
    conn = sqlite3.connect(SEM_DB)
    conn.row_factory = sqlite3.Row
    return conn


def connect_dbs() -> Tuple[sqlite3.Connection, sqlite3.Connection]:
    """
    同时连接两个数据库
    
    Returns:
        Tuple[sqlite3.Connection, sqlite3.Connection]:
            (Navidrome 数据库连接, 语义数据库连接)
    """
    nav = connect_nav_db()
    sem = connect_sem_db()
    return nav, sem


@contextmanager
def nav_db_context() -> Generator[sqlite3.Connection, None, None]:
    """
    Navidrome 数据库上下文管理器，自动关闭连接
    
    Usage:
        with nav_db_context() as conn:
            cursor = conn.execute("SELECT * FROM user")
            # 使用连接...
        # 连接自动关闭
    """
    conn = connect_nav_db()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def sem_db_context() -> Generator[sqlite3.Connection, None, None]:
    """
    语义数据库上下文管理器，自动关闭连接
    
    Usage:
        with sem_db_context() as conn:
            cursor = conn.execute("SELECT * FROM music_semantic")
            # 使用连接...
        # 连接自动关闭
    """
    conn = connect_sem_db()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def dbs_context() -> Generator[Tuple[sqlite3.Connection, sqlite3.Connection], None, None]:
    """
    双数据库上下文管理器，自动关闭两个连接
    
    Usage:
        with dbs_context() as (nav_conn, sem_conn):
            # 使用两个连接...
        # 连接自动关闭
    """
    nav_conn = connect_nav_db()
    sem_conn = connect_sem_db()
    try:
        yield nav_conn, sem_conn
    finally:
        nav_conn.close()
        sem_conn.close()
