"""
日志配置模块 - 统一的日志管理
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config.settings import LOG_DIR, LOG_FILES


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_level: int = logging.INFO
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称（如果 log_file 为 None，将从 LOG_FILES 中查找对应的日志文件名）
        log_file: 日志文件路径（可选，如果为 None 则使用 LOG_FILES 中的配置）
        level: 文件日志级别
        console_level: 控制台日志级别
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # 设置最低级别，由 handler 控制
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器 - 使用 sys.stderr 而不是 sys.stdout，避免与 uvicorn 冲突
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件或从配置中查找）
    if log_file is None:
        # 尝试从 LOG_FILES 中查找对应的日志文件名
        log_file = LOG_FILES.get(name)
    
    if log_file:
        log_path = Path(LOG_DIR) / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取已配置的日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器
    """
    return logging.getLogger(name)
