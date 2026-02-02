"""
通用工具模块 - 共享的工具函数
"""

import sys
import io


def setup_windows_encoding() -> None:
    """设置 Windows 控制台编码为 UTF-8"""
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
