"""
测试 src.utils.common 模块
"""

import sys
import io
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.utils.common import setup_windows_encoding


class TestSetupWindowsEncoding:
    """测试 setup_windows_encoding 函数"""

    @patch('src.utils.common.sys.platform', 'win32')
    @patch('src.utils.common.sys.modules', {})
    def test_setup_windows_encoding_on_windows(self):
        """测试在 Windows 平台上设置编码"""
        # 模拟 stdout 和 stderr
        mock_stdout = Mock()
        mock_stdout.buffer = Mock()
        mock_stderr = Mock()
        mock_stderr.buffer = Mock()

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                with patch('src.utils.common.io.TextIOWrapper') as mock_wrapper:
                    setup_windows_encoding()
                    
                    # 验证 TextIOWrapper 被调用了两次（stdout 和 stderr）
                    assert mock_wrapper.call_count == 2

    @patch('src.utils.common.sys.platform', 'linux')
    def test_setup_windows_encoding_on_linux(self):
        """测试在非 Windows 平台上不设置编码"""
        mock_stdout = Mock()
        mock_stderr = Mock()

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                with patch('src.utils.common.io.TextIOWrapper') as mock_wrapper:
                    setup_windows_encoding()
                    
                    # 验证 TextIOWrapper 没有被调用
                    assert mock_wrapper.call_count == 0

    @patch('src.utils.common.sys.platform', 'win32')
    @patch('src.utils.common.sys.modules', {'uvicorn': Mock()})
    def test_setup_windows_encoding_with_uvicorn(self):
        """测试在 uvicorn 环境中不设置编码"""
        mock_stdout = Mock()
        mock_stderr = Mock()

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                with patch('src.utils.common.io.TextIOWrapper') as mock_wrapper:
                    setup_windows_encoding()
                    
                    # 验证 TextIOWrapper 没有被调用
                    assert mock_wrapper.call_count == 0

    @patch('src.utils.common.sys.platform', 'win32')
    @patch('src.utils.common.sys.modules', {})
    def test_setup_windows_encoding_without_buffer(self):
        """测试当 stdout 没有 buffer 属性时不报错"""
        mock_stdout = Mock(spec=[])  # 没有 buffer 属性
        mock_stderr = Mock(spec=[])

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                # 不应该抛出异常
                setup_windows_encoding()

    @patch('src.utils.common.sys.platform', 'win32')
    @patch('src.utils.common.sys.modules', {})
    def test_setup_windows_encoding_value_error(self):
        """测试当 TextIOWrapper 抛出 ValueError 时不报错"""
        mock_stdout = Mock()
        mock_stdout.buffer = Mock()
        mock_stderr = Mock()
        mock_stderr.buffer = Mock()

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                with patch('src.utils.common.io.TextIOWrapper', side_effect=ValueError("Test error")):
                    # 不应该抛出异常
                    setup_windows_encoding()

    @patch('src.utils.common.sys.platform', 'win32')
    @patch('src.utils.common.sys.modules', {})
    def test_setup_windows_encoding_attribute_error(self):
        """测试当 TextIOWrapper 抛出 AttributeError 时不报错"""
        mock_stdout = Mock()
        mock_stdout.buffer = Mock()
        mock_stderr = Mock()
        mock_stderr.buffer = Mock()

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                with patch('src.utils.common.io.TextIOWrapper', side_effect=AttributeError("Test error")):
                    # 不应该抛出异常
                    setup_windows_encoding()

    @patch('src.utils.common.sys.platform', 'win32')
    @patch('src.utils.common.sys.modules', {})
    def test_setup_windows_encoding_os_error(self):
        """测试当 TextIOWrapper 抛出 OSError 时不报错"""
        mock_stdout = Mock()
        mock_stdout.buffer = Mock()
        mock_stderr = Mock()
        mock_stderr.buffer = Mock()

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                with patch('src.utils.common.io.TextIOWrapper', side_effect=OSError("Test error")):
                    # 不应该抛出异常
                    setup_windows_encoding()

    @patch('src.utils.common.sys.platform', 'win32')
    @patch('src.utils.common.sys.modules', {})
    def test_setup_windows_encoding_encoding_parameter(self):
        """测试使用 UTF-8 编码参数"""
        mock_stdout = Mock()
        mock_stdout.buffer = Mock()
        mock_stderr = Mock()
        mock_stderr.buffer = Mock()

        with patch('src.utils.common.sys.stdout', mock_stdout):
            with patch('src.utils.common.sys.stderr', mock_stderr):
                with patch('src.utils.common.io.TextIOWrapper') as mock_wrapper:
                    setup_windows_encoding()
                    
                    # 验证编码参数为 utf-8
                    calls = mock_wrapper.call_args_list
                    for call in calls:
                        assert call[1].get('encoding') == 'utf-8'
