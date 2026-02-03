"""
数据库迁移管理器
"""
import sqlite3
from typing import List, Dict, Any, Optional

from .models import Migration


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
