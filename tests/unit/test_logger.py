"""
测试 src.utils.logger 模块
"""

import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from src.utils.logger import setup_logger, get_logger


class TestSetupLogger:
    """测试 setup_logger 函数"""

    def test_setup_logger_basic(self):
        """测试基本日志记录器创建"""
        logger = setup_logger("test_basic")
        
        assert logger.name == "test_basic"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0

    def test_setup_logger_duplicate(self):
        """测试重复添加 handler 时直接返回"""
        logger = setup_logger("test_duplicate")
        first_handlers = len(logger.handlers)
        
        # 再次调用相同名称的 logger
        logger2 = setup_logger("test_duplicate")
        
        # 应该返回同一个对象，且 handler 数量不变
        assert logger is logger2
        assert len(logger.handlers) == first_handlers

    def test_setup_logger_with_file(self, tmp_path):
        """测试带指定文件的日志记录器"""
        log_file = "test.log"
        logger = setup_logger("test_with_file", log_file=log_file)
        
        # 写入日志
        logger.info("Test message")
        
        # 检查日志文件被创建
        # 注意：实际路径由 LOG_DIR 决定，这里只验证 handler 被添加
        assert len(logger.handlers) >= 2  # console + file

    def test_setup_logger_console_level(self):
        """测试控制台日志级别设置"""
        logger = setup_logger("test_console_level", console_level=logging.DEBUG)
        
        # 查找控制台处理器
        console_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.StreamHandler)),
            None
        )
        assert console_handler is not None
        assert console_handler.level == logging.DEBUG

    def test_setup_logger_file_level(self, tmp_path):
        """测试文件日志级别设置"""
        logger = setup_logger("test_file_level", log_file="file.log", level=logging.DEBUG)
        
        # 查找文件处理器
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is not None
        assert file_handler.level == logging.DEBUG

    def test_setup_logger_default_levels(self):
        """测试默认日志级别"""
        logger = setup_logger("test_default")
        
        # 默认应该是 INFO
        assert logger.level == logging.DEBUG  # logger 本身设置为 DEBUG

    @patch('src.utils.logger.LOG_FILES', {'test_lookup': 'app.log'})
    @patch('src.utils.logger.LOG_DIR', '/tmp/test_logs')
    def test_setup_logger_from_log_files_config(self):
        """测试从 LOG_FILES 配置中查找日志文件"""
        logger = setup_logger("test_lookup")
        
        # 应该从配置中找到日志文件名并创建文件处理器
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is not None

    @patch('src.utils.logger.LOG_FILES', {'test_config_none': None})
    def test_setup_logger_from_config_none(self):
        """测试从 LOG_FILES 配置查找到 None"""
        logger = setup_logger("test_config_none")
        
        # 不应该有文件处理器
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is None

    @patch('src.utils.logger.LOG_FILES', {})
    def test_setup_logger_from_config_missing(self):
        """测试从 LOG_FILES 配置中找不到对应名称"""
        logger = setup_logger("nonexistent_logger")
        
        # 应该只有控制台处理器
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) == 1

    def test_setup_logger_console_handler_exists(self):
        """测试控制台处理器被正确添加"""
        logger = setup_logger("test_console")
        
        console_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.StreamHandler)),
            None
        )
        assert console_handler is not None

    def test_setup_logger_file_handler_exists(self):
        """测试文件处理器被正确添加"""
        logger = setup_logger("test_file_handler", log_file="test.log")
        
        file_handler = next(
            (h for h in logger.handlers if isinstance(h, logging.FileHandler)),
            None
        )
        assert file_handler is not None

    def test_setup_logger_formatter(self):
        """测试日志格式化器"""
        logger = setup_logger("test_formatter")
        
        for handler in logger.handlers:
            formatter = handler.formatter
            assert '%(asctime)s' in formatter._fmt
            assert '%(name)s' in formatter._fmt
            assert '%(levelname)s' in formatter._fmt
            assert '%(message)s' in formatter._fmt

    def test_setup_logger_write_log(self, tmp_path):
        """测试写入日志"""
        logger = setup_logger("test_write", log_file="write_test.log")
        
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")


class TestGetLogger:
    """测试 get_logger 函数"""

    def test_get_logger_basic(self):
        """测试获取基本日志记录器"""
        logger = get_logger("test_get_basic")
        assert logger.name == "test_get_basic"

    def test_get_logger_same_name(self):
        """测试获取相同名称的日志记录器返回同一个实例"""
        logger1 = get_logger("test_get_same")
        logger2 = get_logger("test_get_same")
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """测试获取不同名称的日志记录器返回不同实例"""
        logger1 = get_logger("test_get_diff1")
        logger2 = get_logger("test_get_diff2")
        assert logger1 is not logger2

    def test_get_logger_level(self):
        """测试获取的日志记录器默认级别"""
        # 使用未配置的 logger 名称获取默认级别
        logger = get_logger("new_test_get_level")
        # 默认应该是 WARNING (如果 logger 未被配置)
        # NOTSET = 0 表示使用父 logger 的级别
        assert logger.level == logging.NOTSET
