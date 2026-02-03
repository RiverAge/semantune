"""
数据库迁移模块 - 管理数据库版本和迁移
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import SEM_DB
from config.constants import DB_INDEXES


class Migration:
    """数据库迁移类"""
    
    def __init__(self, version: str, name: str, up_sql: str, down_sql: Optional[str] = None):
        """
        初始化迁移
        
        Args:
            version: 迁移版本号
            name: 迁移名称
            up_sql: 升级 SQL
            down_sql: 降级 SQL（可选）
        """
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
    
    def __repr__(self) -> str:
        return f"Migration({self.version}: {self.name})"


class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化迁移管理器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.migrations: List[Migration] = []
        self._init_migrations_table()
    
    def _init_migrations_table(self) -> None:
        """初始化迁移记录表"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()
    
    def register(self, migration: Migration) -> None:
        """
        注册迁移
        
        Args:
            migration: 迁移对象
        """
        self.migrations.append(migration)
        # 按版本号排序
        self.migrations.sort(key=lambda m: m.version)
    
    def get_applied_migrations(self) -> List[str]:
        """
        获取已应用的迁移版本列表
        
        Returns:
            已应用的迁移版本列表
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_pending_migrations(self) -> List[Migration]:
        """
        获取待应用的迁移列表
        
        Returns:
            待应用的迁移列表
        """
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied]
    
    def migrate(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        执行迁移
        
        Args:
            target_version: 目标版本，None 表示迁移到最新版本
            
        Returns:
            迁移结果
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            return {
                "status": "up_to_date",
                "message": "数据库已是最新版本",
                "applied": []
            }
        
        # 如果指定了目标版本，只迁移到该版本
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        applied = []
        conn = sqlite3.connect(self.db_path)
        
        try:
            for migration in pending:
                # 执行升级 SQL
                for statement in self._split_sql(migration.up_sql):
                    conn.execute(statement)
                
                # 记录迁移
                conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (migration.version, migration.name)
                )
                
                conn.commit()
                applied.append(migration.version)
            
            return {
                "status": "success",
                "message": f"成功应用 {len(applied)} 个迁移",
                "applied": applied
            }
        
        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "message": f"迁移失败: {str(e)}",
                "applied": applied
            }
        
        finally:
            conn.close()
    
    def rollback(self, target_version: str) -> Dict[str, Any]:
        """
        回滚迁移
        
        Args:
            target_version: 目标版本
            
        Returns:
            回滚结果
        """
        applied = self.get_applied_migrations()
        
        # 找出需要回滚的迁移
        to_rollback = [
            m for m in self.migrations
            if m.version in applied and m.version > target_version
        ]
        
        if not to_rollback:
            return {
                "status": "nothing_to_rollback",
                "message": "没有需要回滚的迁移",
                "rolled_back": []
            }
        
        # 按版本号倒序回滚
        to_rollback.sort(key=lambda m: m.version, reverse=True)
        
        rolled_back = []
        conn = sqlite3.connect(self.db_path)
        
        try:
            for migration in to_rollback:
                if not migration.down_sql:
                    continue
                
                # 执行降级 SQL
                for statement in self._split_sql(migration.down_sql):
                    conn.execute(statement)
                
                # 删除迁移记录
                conn.execute(
                    "DELETE FROM schema_migrations WHERE version = ?",
                    (migration.version,)
                )
                
                conn.commit()
                rolled_back.append(migration.version)
            
            return {
                "status": "success",
                "message": f"成功回滚 {len(rolled_back)} 个迁移",
                "rolled_back": rolled_back
            }
        
        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "message": f"回滚失败: {str(e)}",
                "rolled_back": rolled_back
            }
        
        finally:
            conn.close()
    
    def _split_sql(self, sql: str) -> List[str]:
        """
        分割 SQL 语句
        
        Args:
            sql: SQL 字符串
            
        Returns:
            SQL 语句列表
        """
        # 简单的分割逻辑，按分号分割
        statements = []
        current = []
        
        for line in sql.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current.append(line)
            
            if line.endswith(';'):
                statements.append('\n'.join(current))
                current = []
        
        if current:
            statements.append('\n'.join(current))
        
        return statements
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取迁移状态
        
        Returns:
            迁移状态信息
        """
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "current_version": applied[-1] if applied else None,
            "latest_version": self.migrations[-1].version if self.migrations else None,
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_migrations": applied,
            "pending_migrations": [m.version for m in pending]
        }


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
    up_sql="\n".join(DB_INDEXES),
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


def run_migrations() -> Dict[str, Any]:
    """
    运行所有待应用的迁移
    
    Returns:
        迁移结果
    """
    return migration_manager.migrate()


def get_migration_status() -> Dict[str, Any]:
    """
    获取迁移状态
    
    Returns:
        迁移状态信息
    """
    return migration_manager.get_status()
