"""
数据库迁移模型
"""
from typing import Optional


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
