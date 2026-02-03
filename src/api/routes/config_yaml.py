"""
YAML配置管理 - 推荐配置和标签配置
"""
import logging
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from src.core.response import ApiResponse
from src.utils.logger import setup_logger

logger = setup_logger("api", level=logging.INFO)


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

class AllowedLabelsRequest(BaseModel):
    """标签白名单请求模型"""
    mood: List[str] = Field(default=[], description="情绪标签列表")
    energy: List[str] = Field(default=[], description="能量标签列表")
    scene: List[str] = Field(default=[], description="场景标签列表")
    region: List[str] = Field(default=[], description="地区标签列表")
    subculture: List[str] = Field(default=[], description="亚文化标签列表")
    genre: List[str] = Field(default=[], description="流派标签列表")


class ScenePresetsRequest(BaseModel):
    """场景预设请求模型"""
    presets: Dict[str, Dict[str, List[str]]] = Field(default={}, description="场景预设字典")


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
    
    返回标签生成系统的配置信息
    注意：提示词模板会根据标签白名单自动生成
    """
    try:
        from config.constants import get_allowed_labels, get_scene_presets, get_tagging_api_config
        
        return ApiResponse.success_response(data={
            "allowed_labels": get_allowed_labels(),
            "scene_presets": get_scene_presets(),
            "api_config": get_tagging_api_config()
        })
    except Exception as e:
        logger.error(f"获取标签配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_tagging_config_api(
    allowed_labels: Optional[AllowedLabelsRequest] = None,
    scene_presets: Optional[ScenePresetsRequest] = None,
    api_config: Optional[TaggingApiConfigRequest] = None
):
    """
    更新标签配置
    
    可以单独更新标签白名单、场景预设或 API 配置
    注意：提示词模板会根据标签白名单自动生成，无需手动配置
    """
    try:
        from config.constants import (
            update_allowed_labels, update_scene_presets,
            update_tagging_api_config
        )
        
        if allowed_labels:
            update_allowed_labels(allowed_labels.model_dump())
            logger.info("标签白名单已更新")
        
        if scene_presets:
            update_scene_presets(scene_presets.presets)
            logger.info("场景预设已更新")
        
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
    注意：提示词模板会根据标签白名单自动生成
    """
    try:
        from config.settings import get_recommend_config, get_user_profile_config, get_algorithm_config
        from config.constants import get_allowed_labels, get_scene_presets, get_tagging_api_config
        
        return ApiResponse.success_response(data={
            "recommend": get_recommend_config(),
            "user_profile": get_user_profile_config(),
            "algorithm": get_algorithm_config(),
            "allowed_labels": get_allowed_labels(),
            "scene_presets": get_scene_presets(),
            "api_config": get_tagging_api_config()
        })
    except Exception as e:
        logger.error(f"获取全部配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
