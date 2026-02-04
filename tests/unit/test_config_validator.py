"""
测试 src.core.config_validator 模块
"""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.config_validator import (
    ConfigValidationError,
    validate_config,
    validate_on_startup
)


class TestConfigValidationError:
    """测试 ConfigValidationError 异常类"""

    def test_config_validation_error_creation(self):
        """测试创建 ConfigValidationError"""
        error = ConfigValidationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestValidateConfig:
    """测试 validate_config 函数"""

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_success(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试配置验证成功"""
        # 设置 mock 返回值
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        # 创建测试目录
        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "ok"
        assert result["errors"] == []
        assert result["summary"]["total_errors"] == 0

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_invalid_api_key(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 API Key 无效"""
        mock_api_key.return_value = "short"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("SEMANTUNE_API_KEY 无效或太短" in e for e in result["errors"])
        assert result["summary"]["total_errors"] > 0

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'invalid_url')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_invalid_base_url(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 BASE_URL 格式无效"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("BASE_URL 格式无效" in e for e in result["errors"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', '')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_empty_model(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 MODEL 配置为空"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("MODEL 配置为空" in e for e in result["errors"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_invalid_default_limit(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 default_limit 无效"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 0}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("default_limit 必须大于 0" in e for e in result["errors"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_missing_weight_config(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试缺少权重配置"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0
            # 缺少 in_playlist, time_decay_days, min_decay
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("缺少必需的权重配置" in e for e in result["errors"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_invalid_api_config(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 API 配置无效"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 0,
            "max_tokens": 0,
            "temperature": 3.0  # 超出范围
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("timeout 必须大于 0" in e for e in result["errors"])
        assert any("max_tokens 必须大于 0" in e for e in result["errors"])
        assert any("temperature 必须在 0-2 之间" in e for e in result["errors"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', [])
    def test_validate_config_empty_cors_origins(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 CORS_ORIGINS 为空"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "ok"
        assert any("CORS_ORIGINS 为空" in w for w in result["warnings"])
        assert result["summary"]["total_warnings"] > 0

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_empty_allowed_labels(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 ALLOWED_LABELS 为空"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {}

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("ALLOWED_LABELS 配置为空" in e for e in result["errors"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_high_default_limit_warning(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 default_limit 过高产生警告"""
        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 150}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "ok"
        assert any("default_limit 大于 100" in w for w in result["warnings"])
        assert result["summary"]["total_warnings"] > 0

    @patch('src.core.config_validator.get_api_key', side_effect=ValueError('Invalid API key format'))
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    def test_validate_config_api_key_value_error(
        self,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 API Key 配置错误（ValueError）"""
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        Path('/tmp/test').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/logs').mkdir(parents=True, exist_ok=True)
        Path('/tmp/test/exports').mkdir(parents=True, exist_ok=True)

        result = validate_config()

        assert result["status"] == "error"
        assert any("API Key 配置错误" in e for e in result["errors"])
        assert any("Invalid API key format" in e for e in result["errors"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/nonexistent/dir/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    @patch('src.core.config_validator.Path')
    def test_validate_config_nav_db_parent_not_exists(
        self,
        mock_path,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试 Navidrome 数据库目录不存在"""
        # 模拟 Path 行为
        nav_path = Mock()
        nav_path.parent.exists.return_value = False
        sem_path = Mock()
        sem_path.parent.exists.return_value = True
        log_path = Mock()
        log_path.exists.return_value = True
        export_path = Mock()
        export_path.exists.return_value = True
        
        def path_side_effect(p):
            if 'navidrome' in p:
                return nav_path
            elif 'semantic' in p:
                return sem_path
            elif 'logs' in p:
                return log_path
            elif 'export' in p:
                return export_path
            return Mock()
        
        mock_path.side_effect = path_side_effect

        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        result = validate_config()

        assert result["status"] == "ok"
        assert any("Navidrome 数据库目录不存在" in w for w in result["warnings"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/nonexistent/dir/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    @patch('src.core.config_validator.Path')
    def test_validate_config_sem_db_parent_not_exists(
        self,
        mock_path,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试语义数据库目录不存在"""
        # 模拟 Path 行为
        nav_path = Mock()
        nav_path.parent.exists.return_value = True
        sem_path = Mock()
        sem_path.parent.exists.return_value = False
        log_path = Mock()
        log_path.exists.return_value = True
        export_path = Mock()
        export_path.exists.return_value = True
        
        def path_side_effect(p):
            if 'navidrome' in p:
                return nav_path
            elif 'semantic' in p:
                return sem_path
            elif 'logs' in p:
                return log_path
            elif 'export' in p:
                return export_path
            return Mock()
        
        mock_path.side_effect = path_side_effect

        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        result = validate_config()

        assert result["status"] == "ok"
        assert any("语义数据库目录不存在" in w for w in result["warnings"])

    @patch('src.core.config_validator.get_api_key')
    @patch('src.core.config_validator.NAV_DB', '/tmp/test/navidrome.db')
    @patch('src.core.config_validator.SEM_DB', '/tmp/test/semantic.db')
    @patch('src.core.config_validator.LOG_DIR', '/tmp/test/logs')
    @patch('src.core.config_validator.EXPORT_DIR', '/tmp/test/exports')
    @patch('src.core.config_validator.BASE_URL', 'https://api.example.com/v1')
    @patch('src.core.config_validator.MODEL', 'test-model')
    @patch('src.core.config_validator.get_recommend_config')
    @patch('src.core.config_validator.get_user_profile_config')
    @patch('src.core.config_validator.get_tagging_api_config')
    @patch('src.core.config_validator.get_allowed_labels')
    @patch('src.core.config_validator.CORS_ORIGINS', ['http://localhost:5173'])
    @patch('pathlib.Path.exists', return_value=False)
    @patch('pathlib.Path.mkdir')
    def test_validate_config_mkdir_permission_error(
        self,
        mock_mkdir,
        mock_exists,
        mock_allowed_labels,
        mock_api_config,
        mock_user_profile_config,
        mock_recommend_config,
        mock_api_key
    ):
        """测试目录创建失败（权限错误）"""
        mock_mkdir.side_effect = PermissionError("Permission denied")

        mock_api_key.return_value = "valid_api_key_1234567890"
        mock_recommend_config.return_value = {"default_limit": 20}
        mock_user_profile_config.return_value = {
            "play_count": 1.0,
            "starred": 2.0,
            "in_playlist": 1.5,
            "time_decay_days": 30,
            "min_decay": 0.1
        }
        mock_api_config.return_value = {
            "timeout": 30,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        mock_allowed_labels.return_value = {
            "mood": {"happy", "sad"},
            "genre": {"pop", "rock"}
        }

        result = validate_config()

        assert result["status"] == "error"
        assert any("无法创建" in e for e in result["errors"])


class TestValidateOnStartup:
    """测试 validate_on_startup 函数"""

    @patch('src.core.config_validator.validate_config')
    def test_validate_on_startup_success(self, mock_validate_config):
        """测试启动验证成功"""
        mock_validate_config.return_value = {
            "status": "ok",
            "errors": [],
            "warnings": []
        }

        # 不应该抛出异常
        validate_on_startup()

    @patch('src.core.config_validator.validate_config')
    @patch('logging.getLogger')
    def test_validate_on_startup_with_warnings(self, mock_get_logger, mock_validate_config):
        """测试启动验证有警告"""
        mock_validate_config.return_value = {
            "status": "ok",
            "errors": [],
            "warnings": ["Test warning"]
        }
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # 不应该抛出异常
        validate_on_startup()

        # 验证警告被记录
        mock_logger.warning.assert_called_once()

    @patch('src.core.config_validator.validate_config')
    def test_validate_on_startup_with_errors(self, mock_validate_config):
        """测试启动验证有错误"""
        mock_validate_config.return_value = {
            "status": "error",
            "errors": ["Test error"],
            "warnings": []
        }

        # 应该抛出异常
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_on_startup()

        assert "配置验证失败" in str(exc_info.value)
