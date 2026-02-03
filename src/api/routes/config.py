"""
配置管理接口路由
"""
from fastapi import APIRouter

from src.core.response import ApiResponse
from src.api.routes.config_api import (
    get_api_config,
    update_api_config,
    reset_api_config,
    ApiConfig,
    ApiConfigResponse
)
from src.api.routes.config_yaml import (
    get_recommend_config_api,
    update_recommend_config_api,
    get_tagging_config_api,
    update_tagging_config_api,
    get_all_config_api,
    RecommendConfigRequest,
    UserProfileConfigRequest,
    AlgorithmConfigRequest,
    TaggingApiConfigRequest
)

router = APIRouter()


# ==================== API 配置接口 ====================

@router.get("/api", response_model=ApiResponse[ApiConfigResponse])
async def get_api_config_route():
    """获取当前 API 配置"""
    return await get_api_config()


@router.post("/api")
async def update_api_config_route(config: ApiConfig):
    """更新 API 配置"""
    return await update_api_config(config)


@router.delete("/api")
async def reset_api_config_route():
    """重置 API 配置"""
    return await reset_api_config()


# ==================== 推荐配置接口 ====================

@router.get("/recommend")
async def get_recommend_config_route():
    """获取推荐配置"""
    return await get_recommend_config_api()


@router.put("/recommend")
async def update_recommend_config_route(
    recommend: RecommendConfigRequest = None,
    user_profile: UserProfileConfigRequest = None,
    algorithm: AlgorithmConfigRequest = None
):
    """更新推荐配置"""
    return await update_recommend_config_api(recommend, user_profile, algorithm)


# ==================== 标签配置接口 ====================

@router.get("/tagging")
async def get_tagging_config_route():
    """获取标签配置"""
    return await get_tagging_config_api()


@router.put("/tagging")
async def update_tagging_config_route(
    api_config: TaggingApiConfigRequest = None
):
    """更新标签配置"""
    return await update_tagging_config_api(api_config)


# ==================== 全部配置接口 ====================

@router.get("/all")
async def get_all_config_route():
    """获取所有配置"""
    return await get_all_config_api()
