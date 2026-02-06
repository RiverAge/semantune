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
        DROP INDEX IF EXISTS idx_annotation_user_item;
    """
))

migration_manager.register(Migration(
    version="2.0.0",
    name="upgrade_to_8_dimensions",
    up_sql="""
        -- 删除旧索引
        DROP INDEX IF EXISTS idx_music_semantic_mood;
        DROP INDEX IF EXISTS idx_music_semantic_energy;
        DROP INDEX IF EXISTS idx_music_semantic_genre;
        DROP INDEX IF EXISTS idx_music_semantic_region;
        DROP INDEX IF EXISTS idx_music_semantic_scene;
        DROP INDEX IF EXISTS idx_music_semantic_confidence;
        DROP INDEX IF EXISTS idx_music_semantic_updated_at;

        -- 删除所有现有数据（结构不兼容）
        DELETE FROM music_semantic;

        -- 重建表结构（包含新的字段）
        DROP TABLE music_semantic;
        CREATE TABLE music_semantic (
            file_id TEXT PRIMARY KEY,
            title TEXT,
            artist TEXT,
            album TEXT,
            mood TEXT,
            energy TEXT,
            genre TEXT,
            style TEXT,
            scene TEXT,
            region TEXT,
            culture TEXT,
            language TEXT,
            confidence REAL,
            model TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 创建新索引
        CREATE INDEX idx_music_semantic_mood ON music_semantic(mood);
        CREATE INDEX idx_music_semantic_energy ON music_semantic(energy);
        CREATE INDEX idx_music_semantic_genre ON music_semantic(genre);
        CREATE INDEX idx_music_semantic_style ON music_semantic(style);
        CREATE INDEX idx_music_semantic_scene ON music_semantic(scene);
        CREATE INDEX idx_music_semantic_region ON music_semantic(region);
        CREATE INDEX idx_music_semantic_culture ON music_semantic(culture);
        CREATE INDEX idx_music_semantic_language ON music_semantic(language);
        CREATE INDEX idx_music_semantic_confidence ON music_semantic(confidence);
        CREATE INDEX idx_music_semantic_updated_at ON music_semantic(updated_at);
    """,
    down_sql="""
        -- 此迁移不可逆（数据已清空）
        -- down_sql 提供空操作以支持回滚记录
        SELECT 1;
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
