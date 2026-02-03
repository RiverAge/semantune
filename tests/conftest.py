"""
pytest 配置文件 - 共享 fixtures 和测试配置
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars():
    """模拟环境变量"""
    original_env = os.environ.copy()
    
    test_env = {
        "SEMANTUNE_API_KEY": "test_api_key_1234567890",
        "SEMANTUNE_BASE_URL": "https://api.example.com/v1",
        "SEMANTUNE_MODEL": "test-model",
        "NAV_DB_PATH": "/tmp/test/navidrome.db",
        "SEM_DB_PATH": "/tmp/test/semantic.db",
        "LOG_DIR": "/tmp/test/logs",
        "EXPORT_DIR": "/tmp/test/exports",
    }
    
    os.environ.update(test_env)
    yield test_env
    
    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_nav_repo():
    """模拟 NavidromeRepository"""
    repo = Mock()
    repo.get_all_songs = Mock(return_value=[
        {
            "id": "song1",
            "title": "Test Song 1",
            "artist": "Test Artist",
            "album": "Test Album"
        },
        {
            "id": "song2",
            "title": "Test Song 2",
            "artist": "Test Artist",
            "album": "Test Album"
        }
    ])
    repo.get_total_count = Mock(return_value=10)
    return repo


@pytest.fixture
def mock_sem_repo():
    """模拟 SemanticRepository"""
    repo = Mock()
    repo.get_total_count = Mock(return_value=5)
    repo.save_song_tags = Mock()
    repo.sem_conn = Mock()
    repo.sem_conn.execute = Mock(return_value=Mock(
        fetchall=Mock(return_value=[("song1",), ("song2",)])
    ))
    return repo


@pytest.fixture
def mock_llm_client():
    """模拟 LLMClient"""
    client = Mock()
    client.call_llm_api = Mock(return_value=(
        {
            "mood": "happy",
            "genre": "pop",
            "energy": "high",
            "confidence": 0.85
        },
        "Mock LLM response"
    ))
    return client


@pytest.fixture
def sample_songs():
    """示例歌曲数据"""
    return [
        {
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "album": "A Night at the Opera"
        },
        {
            "title": "Hotel California",
            "artist": "Eagles",
            "album": "Hotel California"
        },
        {
            "title": "Stairway to Heaven",
            "artist": "Led Zeppelin",
            "album": "Led Zeppelin IV"
        }
    ]


@pytest.fixture
def sample_tags():
    """示例标签数据"""
    return {
        "mood": "epic",
        "genre": "rock",
        "energy": "high",
        "tempo": "medium",
        "confidence": 0.92
    }


@pytest.fixture
def mock_config():
    """模拟配置"""
    return {
        "default_limit": 20,
        "diversity_weight": 0.3,
        "similarity_weight": 0.7,
        "play_count": 1.0,
        "starred": 2.0,
        "in_playlist": 1.5,
        "time_decay_days": 30,
        "min_decay": 0.1
    }


@pytest.fixture
def mock_api_response():
    """模拟 API 响应"""
    return {
        "status": "ok",
        "errors": [],
        "warnings": [],
        "summary": {
            "total_errors": 0,
            "total_warnings": 0
        }
    }


@pytest.fixture
def mock_database(temp_dir):
    """模拟数据库连接"""
    db_path = temp_dir / "test.db"
    
    # 创建模拟连接
    conn = Mock()
    conn.execute = Mock()
    conn.commit = Mock()
    conn.close = Mock()
    
    return {
        "path": db_path,
        "connection": conn
    }


@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_http_client():
    """模拟 HTTP 客户端"""
    client = Mock()
    
    # 模拟成功的响应
    success_response = Mock()
    success_response.status_code = 200
    success_response.json = Mock(return_value={
        "choices": [
            {
                "message": {
                    "content": '{"mood": "happy", "genre": "pop"}'
                }
            }
        ]
    })
    
    # 模拟失败的响应
    error_response = Mock()
    error_response.status_code = 500
    error_response.text = "Internal Server Error"
    
    client.get = Mock(return_value=success_response)
    client.post = Mock(return_value=success_response)
    
    return client


@pytest.fixture(autouse=True)
def reset_singletons():
    """在每个测试后重置单例"""
    yield
    # 这里可以添加重置单例的逻辑
    pass
