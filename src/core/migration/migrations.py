"""
数据库迁移注册
"""
from config.settings import SEM_DB
from config.constants import DB_INDEXES
from .models import Migration
from .manager import MigrationManager


# 创建迁移管理器实例
migration_manager = MigrationManager(SEM_DB)


# 注册迁移
migration_manager.register(Migration(
    version="1.0.0",
    name="initial_schema",
    up_sql="""
        -- 创建音乐语义表
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
        );

        -- 创建同步状态表
        CREATE TABLE IF NOT EXISTS semantic_sync_state (
            file_id TEXT PRIMARY KEY,
            last_seen TIMESTAMP,
            status TEXT DEFAULT 'pending'
        );
    """,
    down_sql="""
        DROP TABLE IF EXISTS semantic_sync_state;
        DROP TABLE IF EXISTS music_semantic;
    """
))

migration_manager.register(Migration(
    version="1.1.0",
    name="add_indexes",
    up_sql="\n".join([s + ";" for s in DB_INDEXES]),
    down_sql="""
        DROP INDEX IF EXISTS idx_music_semantic_mood;
        DROP INDEX IF EXISTS idx_music_semantic_energy;
        DROP INDEX IF EXISTS idx_music_semantic_genre;
        DROP INDEX IF EXISTS idx_music_semantic_region;
        DROP INDEX IF EXISTS idx_music_semantic_scene;
        DROP INDEX IF EXISTS idx_music_semantic_confidence;
        DROP INDEX IF EXISTS idx_music_semantic_updated_at;
        DROP INDEX IF EXISTS idx_annotation_user_id;
        DROP INDEX IF EXISTS idx_annotation_item_id;
        DROP INDEX IF EXISTS idx_annotation_user_item;
    """
))


def run_migrations():
    """
    运行所有待应用的迁移

    Returns:
        迁移结果
    """
    return migration_manager.migrate()


def get_migration_status():
    """
    获取迁移状态

    Returns:
        迁移状态信息
    """
    return migration_manager.get_status()
