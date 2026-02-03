"""
配置文件 - 数据库路径、API配置等
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 项目版本
VERSION = "1.1.0"

# 数据库路径
NAV_DB = str(BASE_DIR / "data" / "navidrome.db")
SEM_DB = str(BASE_DIR / "data" / "semantic.db")

# 日志目录
LOG_DIR = str(BASE_DIR / "logs")
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
EXPORT_DIR = str(BASE_DIR / "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

# LLM API 配置（支持任何 OpenAI 兼容的 API）
BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"  # OpenAI 兼容的 API 端点
MODEL = "meta/llama-3.3-70b-instruct"  # 模型名称


def get_api_key() -> str:
    """
    获取 API Key，延迟验证以避免模块导入时抛出异常
    
    Returns:
        API Key 字符串
        
    Raises:
        ValueError: 当 API_KEY 未设置时抛出
    """
    api_key = os.getenv("SEMANTUNE_API_KEY")
    if not api_key:
        raise ValueError(
            "SEMANTUNE_API_KEY 环境变量未设置。请设置环境变量或创建 .env 文件。\n"
            "示例: export SEMANTUNE_API_KEY='your-api-key-here'"
        )
    return api_key

# API 提供商类型（用于选择提示词格式）
# 可选值: "openai", "nvidia", "anthropic", "custom"
API_PROVIDER = "nvidia"  # 默认使用 NVIDIA 格式

# 推荐配置
RECOMMEND_CONFIG = {
    "default_limit": 30,                # 默认推荐数量
    "recent_filter_count": 100,         # 过滤最近听过的 N 首歌
    "diversity_max_per_artist": 1,      # 每个歌手最多推荐 N 首
    "diversity_max_per_album": 1,       # 每张专辑最多推荐 N 首
    "exploration_ratio": 0.25,          # 探索型歌曲占比（25%）
    "tag_weights": {                    # 标签权重
        "mood": 2.0,                    # 情绪最重要
        "energy": 1.5,                  # 能量次之
        "genre": 1.2,                   # 流派
        "region": 0.8                   # 地区权重较低
    }
}

# 用户画像权重配置
WEIGHT_CONFIG = {
    "play_count": 1.0,      # 每次播放的基础权重
    "starred": 10.0,        # 收藏的固定加分
    "in_playlist": 8.0,     # 每个歌单的加分
    "time_decay_days": 90,  # 时间衰减周期（天）
    "min_decay": 0.3        # 最小衰减系数
}

# API 调用配置
API_CONFIG = {
    "timeout": 60,          # API 请求超时时间（秒）
    "max_tokens": 1024,     # API 响应最大 token 数
    "temperature": 0.1,     # API 温度参数
    "retry_delay": 1,       # 失败重试延迟（秒）
    "max_retries": 3,       # 最大重试次数
    "retry_backoff": 2,     # 重试退避倍数（每次重试延迟时间乘以这个值）
}

# 推荐算法配置
ALGORITHM_CONFIG = {
    "exploitation_pool_multiplier": 3,  # 利用型候选池倍数
    "exploration_pool_start": 0.25,     # 探索型池起始位置（比例）
    "exploration_pool_end": 0.5,        # 探索型池结束位置（比例）
}

# CORS 配置
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
).split(",")
