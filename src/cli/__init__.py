"""
CLI 命令处理模块 - 使用 Service 层处理命令行操作
"""

from .tagging_cli import TaggingCLI
from .recommend_cli import RecommendCLI
from .query_cli import QueryCLI
from .analyze_cli import AnalyzeCLI

__all__ = [
    'TaggingCLI',
    'RecommendCLI',
    'QueryCLI',
    'AnalyzeCLI',
]
