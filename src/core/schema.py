"""
数据库表结构定义
"""

import sqlite3

from config.constants import DB_INDEXES

# 语义标签表结构
MUSIC_SEMANTIC_SCHEMA = """
CREATE TABLE IF NOT EXISTS music_semantic (
    file_id TEXT PRIMARY KEY,
    title TEXT,
    artist TEXT,
    album TEXT,
    mood TEXT,
    energy TEXT,
    scene TEXT,
    region TEXT,
    subculture TEXT,
    genre TEXT,
    confidence REAL,
    model TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# 同步状态表结构
SYNC_STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS semantic_sync_state (
    file_id TEXT PRIMARY KEY,
    last_seen TIMESTAMP,
    status TEXT DEFAULT 'pending'
)
"""


def init_semantic_db(conn: sqlite3.Connection) -> None:
    """
    初始化语义数据库表结构
    
    Args:
        conn: SQLite 数据库连接对象
        
    创建以下表:
        - music_semantic: 存储歌曲的语义标签
        - semantic_sync_state: 存储同步状态
    """
    conn.execute(MUSIC_SEMANTIC_SCHEMA)
    conn.execute(SYNC_STATE_SCHEMA)
    
    # 创建索引
    for index_sql in DB_INDEXES:
        conn.execute(index_sql)
    
    conn.commit()
