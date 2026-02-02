"""
通用工具模块 - 共享的工具函数
"""

import sys
import io


def setup_windows_encoding() -> None:
    """设置 Windows 控制台编码为 UTF-8"""
    if sys.platform == 'win32':
        try:
            # 检查是否在 uvicorn 环境中运行
            if 'uvicorn' in sys.modules:
                return
            
            # 检查 stdout 和 stderr 是否可用
            if hasattr(sys.stdout, 'buffer') and hasattr(sys.stderr, 'buffer'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except (ValueError, AttributeError, OSError):
            # 如果文件句柄已关闭或不可用，跳过编码设置
            pass
