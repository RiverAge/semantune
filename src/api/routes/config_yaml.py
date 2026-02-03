"""
YAML配置管理 - 推荐配置和标签配置
"""
import logging
import os
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from src.core.response import ApiResponse
from src.utils.logger import setup_logger

# 从环境变量读取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logger = setup_logger("api", level=log_level, console_level=log_level)


# ==================== 推荐配置请求模型 ====================

class RecommendConfigRequest(BaseModel):
    """推荐配置请求模型"""
    default_limit: int = Field(default=30, ge=1, le=100, description="默认推荐数量")
    recent_filter_count: int = Field(default=100, ge=0, description="过滤最近听过的 N 首歌")
    diversity_max_per_artist: int = Field(default=1, ge=1, description="每个歌手最多推荐 N 首")
    diversity_max_per_album: int = Field(default=1, ge=1, description="每张专辑最多推荐 N 首")
    exploration_ratio: float = Field(default=0.25, ge=0.0, le=1.0, description="探索型歌曲占比")
    tag_weights: Dict[str, float] = Field(
        default={"mood": 2.0, "energy": 1.5, "genre": 1.2, "region": 0.8},
        description="标签权重"
    )


class UserProfileConfigRequest(BaseModel):
    """用户画像权重配置请求模型"""
    play_count: float = Field(default=1.0, ge=0.0, description="每次播放的基础权重")
    starred: float = Field(default=10.0, ge=0.0, description="收藏的固定加分")
    in_playlist: float = Field(default=8.0, ge=0.0, description="每个歌单的加分")
    time_decay_days: int = Field(default=90, ge=1, description="时间衰减周期（天）")
    min_decay: float = Field(default=0.3, ge=0.0, le=1.0, description="最小衰减系数")


class AlgorithmConfigRequest(BaseModel):
    """推荐算法配置请求模型"""
    exploitation_pool_multiplier: int = Field(default=3, ge=1, description="利用型候选池倍数")
    exploration_pool_start: float = Field(default=0.25, ge=0.0, le=1.0, description="探索型池起始位置")
    exploration_pool_end: float = Field(default=0.5, ge=0.0, le=1.0, description="探索型池结束位置")
    randomness: float = Field(default=0.0, ge=0.0, le=1.0, description="随机扰动系数")


# ==================== 标签配置请求模型 ====================

class TaggingApiConfigRequest(BaseModel):
    """标签生成 API 配置请求模型"""
    timeout: int = Field(default=60, ge=1, description="API 请求超时时间（秒）")
    max_tokens: int = Field(default=1024, ge=1, description="API 响应最大 token 数")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="API 温度参数")
    retry_delay: int = Field(default=1, ge=0, description="失败重试延迟（秒）")
    max_retries: int = Field(default=3, ge=0, description="最大重试次数")
    retry_backoff: int = Field(default=2, ge=1, description="重试退避倍数")


# ==================== 推荐配置接口 ====================

async def get_recommend_config_api():
    """
    获取推荐配置

    返回推荐系统的配置信息
    """
    try:
        from config.settings import get_recommend_config, get_user_profile_config, get_algorithm_config

        return ApiResponse.success_response(data={
            "recommend": get_recommend_config(),
            "user_profile": get_user_profile_config(),
            "algorithm": get_algorithm_config()
        })
    except Exception as e:
        logger.error(f"获取推荐配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_recommend_config_api(
    recommend: Optional[RecommendConfigRequest] = None,
    user_profile: Optional[UserProfileConfigRequest] = None,
    algorithm: Optional[AlgorithmConfigRequest] = None
):
    """
    更新推荐配置

    可以单独更新推荐配置、用户画像配置或算法配置
    """
    try:
        from config.settings import update_recommend_config, update_user_profile_config, update_algorithm_config

        if recommend:
            update_recommend_config(recommend.model_dump())
            logger.info("推荐配置已更新")

        if user_profile:
            update_user_profile_config(user_profile.model_dump())
            logger.info("用户画像配置已更新")

        if algorithm:
            update_algorithm_config(algorithm.model_dump())
            logger.info("算法配置已更新")

        return ApiResponse.success_response(data={
            "message": "配置已更新"
        })
    except Exception as e:
        logger.error(f"更新推荐配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 标签配置接口 ====================

async def get_tagging_config_api():
    """
    获取标签配置

    返回标签生成系统的 API 配置信息
    注意：标签白名单（mood、energy、scene、region、subculture、genre）现在通过后台配置文件 config/tagging_config.yaml 管理
    """
    try:
        from config.constants import get_tagging_api_config

        return ApiResponse.success_response(data={
            "api_config": get_tagging_api_config()
        })
    except Exception as e:
        logger.error(f"获取标签配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_tagging_config_api(
    api_config: Optional[TaggingApiConfigRequest] = None
):
    """
    更新标签配置

    只更新 API 配置
    注意：标签白名单（mood、energy、scene、region、subculture、genre）现在通过后台配置文件 config/tagging_config.yaml 管理
    """
    try:
        from config.constants import update_tagging_api_config

        if api_config:
            update_tagging_api_config(api_config.model_dump())
            logger.info("标签 API 配置已更新")

        return ApiResponse.success_response(data={
            "message": "配置已更新"
        })
    except Exception as e:
        logger.error(f"更新标签配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 全部配置接口 ====================

async def get_all_config_api():
    """
    获取所有配置

    返回所有系统的配置信息
    注意：标签白名单（mood、energy、scene、region、subculture、genre）现在通过后台配置文件 config/tagging_config.yaml 管理
    """
    try:
        from config.settings import get_recommend_config, get_user_profile_config, get_algorithm_config
        from config.constants import get_tagging_api_config

        return ApiResponse.success_response(data={
            "recommend": get_recommend_config(),
            "user_profile": get_user_profile_config(),
            "algorithm": get_algorithm_config(),
            "api_config": get_tagging_api_config()
        })
    except Exception as e:
        logger.error(f"获取全部配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
