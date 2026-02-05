"""
配置文件 - 数据库路径、API配置等
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据根目录（Docker 部署时可设置环境变量）
DATA_ROOT = Path(os.getenv("SEMANTUNE_DATA_DIR", BASE_DIR / "data"))
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# 加载 .env 文件（显式指定路径）
ENV_PATH = DATA_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# 导入版本号 - 单一来源
import sys
sys.path.insert(0, str(BASE_DIR / "src"))
from __init__ import __version__ as VERSION

# 数据库路径
# Navidrome 数据库（支持独立挂载，优先使用环境变量）
NAVIDROME_DB_PATH = os.getenv("SEMANTUNE_NAVIDROME_DB_PATH")
if NAVIDROME_DB_PATH:
    # Docker 部署使用独立挂载的 Navidrome 数据库
    NAV_DB = NAVIDROME_DB_PATH
else:
    # 本地开发使用 data 目录下的数据库
    NAV_DB = str(DATA_ROOT / "navidrome.db")

# 语义数据库（始终在 data 目录下）
SEM_DB = str(DATA_ROOT / "semantic.db")

# 日志目录
LOG_DIR = str(DATA_ROOT / "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件名配置
LOG_FILES = {
    "api": "api.log",
    "tagging": "tagging.log",
    "tagging_preview": "tagging_preview.log",
    "recommend": "recommend.log",
    "query": "query.log",
    "profile": "profile.log",
    "export": "export.log",
    "analyze": "analyze.log",
    "main": "main.log",
}

# 导出目录
EXPORT_DIR = str(DATA_ROOT / "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# LLM API 配置（支持任何 OpenAI 兼容的 API） - 改为动态获取或默认值
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"

def get_base_url() -> str:
    """动态获取 Base URL"""
    return os.getenv("SEMANTUNE_BASE_URL", DEFAULT_BASE_URL)

def get_model() -> str:
    """动态获取模型名称"""
    return os.getenv("SEMANTUNE_MODEL", DEFAULT_MODEL)


def get_api_key() -> str:
    """
    获取 API Key，延迟验证以避免模块导入时抛出异常
    
    每次调用时重新加载 .env 文件，确保获取最新的配置
    
    Returns:
        API Key 字符串
        
    Raises:
        ValueError: 当 API_KEY 未设置时抛出
    """
    reload_env()
    api_key = os.getenv("SEMANTUNE_API_KEY")
    if not api_key:
        raise ValueError(
            "SEMANTUNE_API_KEY 环境变量未设置。请设置环境变量或创建 .env 文件。\n"
            "示例: export SEMANTUNE_API_KEY='your-api-key-here'"
        )
    return api_key


def reload_env():
    """
    重新加载 .env 文件中的环境变量
    
    当配置更新后调用此函数以使新配置生效
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)


# API 提供商类型（用于选择提示词格式）
# 可选值: "openai", "nvidia", "anthropic", "custom"
API_PROVIDER = "nvidia"  # 默认使用 NVIDIA 格式


# ==================== YAML 配置加载 ====================

def _load_yaml_config(config_file: str) -> Dict[str, Any]:
    """
    从 YAML 文件加载配置
    
    Args:
        config_file: 配置文件名（相对于数据目录）
        
    Returns:
        配置字典
    """
    # 优先从数据目录读取，然后从项目 config 目录读取
    config_path = DATA_ROOT / "config" / config_file
    if not config_path.exists():
        config_path = BASE_DIR / "config" / config_file
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _save_yaml_config(config_file: str, config: Dict[str, Any]) -> None:
    """
    保存配置到 YAML 文件
    
    Args:
        config_file: 配置文件名（相对于数据目录）
        config: 配置字典
    """
    config_dir = DATA_ROOT / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / config_file
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ==================== 推荐配置 ====================

def get_recommend_config() -> Dict[str, Any]:
    """
    获取推荐配置
    
    Returns:
        推荐配置字典
    """
    config = _load_yaml_config("recommend_config.yaml")
    return config.get("recommend", {})


def get_user_profile_config() -> Dict[str, Any]:
    """
    获取用户画像权重配置
    
    Returns:
        用户画像配置字典
    """
    config = _load_yaml_config("recommend_config.yaml")
    return config.get("user_profile", {})


def get_algorithm_config() -> Dict[str, Any]:
    """
    获取推荐算法配置
    
    Returns:
        算法配置字典
    """
    config = _load_yaml_config("recommend_config.yaml")
    return config.get("algorithm", {})


def update_recommend_config(config: Dict[str, Any]) -> None:
    """
    更新推荐配置
    
    Args:
        config: 新的推荐配置
    """
    # 读取现有配置
    full_config = _load_yaml_config("recommend_config.yaml")
    
    # 更新推荐配置
    full_config["recommend"] = config
    
    # 保存
    _save_yaml_config("recommend_config.yaml", full_config)


def update_user_profile_config(config: Dict[str, Any]) -> None:
    """
    更新用户画像权重配置
    
    Args:
        config: 新的用户画像配置
    """
    # 读取现有配置
    full_config = _load_yaml_config("recommend_config.yaml")
    
    # 更新用户画像配置
    full_config["user_profile"] = config
    
    # 保存
    _save_yaml_config("recommend_config.yaml", full_config)


def update_algorithm_config(config: Dict[str, Any]) -> None:
    """
    更新推荐算法配置
    
    Args:
        config: 新的算法配置
    """
    # 读取现有配置
    full_config = _load_yaml_config("recommend_config.yaml")
    
    # 更新算法配置
    full_config["algorithm"] = config
    
    # 保存
    _save_yaml_config("recommend_config.yaml", full_config)


# ==================== 兼容性：保持旧接口 ====================

# 为了向后兼容，提供全局变量（从 YAML 加载）
_RECOMMEND_CONFIG_CACHE = None
_WEIGHT_CONFIG_CACHE = None
_ALGORITHM_CONFIG_CACHE = None


def RECOMMEND_CONFIG() -> Dict[str, Any]:
    """获取推荐配置（兼容旧代码）"""
    global _RECOMMEND_CONFIG_CACHE
    if _RECOMMEND_CONFIG_CACHE is None:
        _RECOMMEND_CONFIG_CACHE = get_recommend_config()
    return _RECOMMEND_CONFIG_CACHE


def WEIGHT_CONFIG() -> Dict[str, Any]:
    """获取用户画像权重配置（兼容旧代码）"""
    global _WEIGHT_CONFIG_CACHE
    if _WEIGHT_CONFIG_CACHE is None:
        _WEIGHT_CONFIG_CACHE = get_user_profile_config()
    return _WEIGHT_CONFIG_CACHE


def ALGORITHM_CONFIG() -> Dict[str, Any]:
    """获取算法配置（兼容旧代码）"""
    global _ALGORITHM_CONFIG_CACHE
    if _ALGORITHM_CONFIG_CACHE is None:
        _ALGORITHM_CONFIG_CACHE = get_algorithm_config()
    return _ALGORITHM_CONFIG_CACHE


# CORS 配置
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
).split(",")
