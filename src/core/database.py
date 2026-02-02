"""
数据库连接模块
"""

import sqlite3
from typing import Tuple
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
