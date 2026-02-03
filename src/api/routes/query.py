"""
查询接口路由
"""
import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from config.constants import get_allowed_labels
from src.core.database import dbs_context
from src.core.response import ApiResponse
from src.core.exceptions import SemantuneException
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

# 从环境变量读取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logger = setup_logger("api", level=log_level, console_level=log_level)

router = APIRouter()


class QueryByMoodRequest(BaseModel):
    """按情绪查询请求模型"""
    mood: str = Field(..., min_length=1, max_length=50, description="情绪标签")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


class QueryByTagsRequest(BaseModel):
    """按标签组合查询请求模型"""
    mood: Optional[str] = Field(None, max_length=50, description="情绪标签")
    energy: Optional[str] = Field(None, max_length=50, description="能量标签")
    genre: Optional[str] = Field(None, max_length=50, description="流派标签")
    region: Optional[str] = Field(None, max_length=50, description="地区标签")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


class QuerySceneRequest(BaseModel):
    """场景查询请求模型"""
    scene: str = Field(..., min_length=1, max_length=50, description="场景标签")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


class RandomRequest(BaseModel):
    """随机推荐请求模型"""
    limit: int = Field(default=20, ge=1, le=100, description="返回数量，范围1-100")


@router.post("/mood")
async def query_by_mood_api(request: QueryByMoodRequest):
    """
    按情绪查询歌曲

    - **mood**: 情绪标签（如：Energetic, Peaceful, Sad 等）
    - **limit**: 返回数量，默认20
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            query_service = ServiceFactory.create_query_service(nav_conn, sem_conn)
            songs = query_service.query_by_mood(request.mood, request.limit)

            logger.debug(f"按情绪 {request.mood} 查询，返回 {len(songs)} 首歌曲")
            return ApiResponse.success_response(
                data={"songs": songs, "count": len(songs)}
            )

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"按情绪查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tags")
async def query_by_tags_api(request: QueryByTagsRequest):
    """
    按标签组合查询歌曲

    - **mood**: 情绪标签（可选）
    - **energy**: 能量标签（可选）
    - **genre**: 流派标签（可选）
    - **region**: 地区标签（可选）
    - **limit**: 返回数量，默认20
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            query_service = ServiceFactory.create_query_service(nav_conn, sem_conn)
            songs = query_service.query_by_tags(
                mood=request.mood,
                energy=request.energy,
                genre=request.genre,
                region=request.region,
                limit=request.limit
            )

            logger.debug(f"按标签组合查询，返回 {len(songs)} 首歌曲")
            return ApiResponse.success_response(
                data={"songs": songs, "count": len(songs)}
            )

    except SemantuneException as e:
        raise
    except Exception as e:
        logger.error(f"按标签组合查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scene")
async def query_scene_api(request: QuerySceneRequest):
    """
    按预设场景查询歌曲

    可用场景：深夜、运动、学习、开车、放松、派对、伤心、励志

    - **scene**: 场景名称
    - **limit**: 返回数量，默认20
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            query_service = ServiceFactory.create_query_service(nav_conn, sem_conn)
            songs = query_service.query_by_scene_preset(request.scene, request.limit)

            logger.info(f"按场景 {request.scene} 查询，返回 {len(songs)} 首歌曲")
            return {"songs": songs, "count": len(songs)}

    except Exception as e:
        logger.error(f"按场景查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/random")
async def random_api(request: RandomRequest):
    """
    随机推荐歌曲

    - **limit**: 返回数量，默认20
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            query_service = ServiceFactory.create_query_service(nav_conn, sem_conn)
            # 使用场景查询中的随机特性
            songs = query_service.query_by_tags(limit=request.limit)

            logger.info(f"随机推荐，返回 {len(songs)} 首歌曲")
            return {"songs": songs, "count": len(songs)}

    except Exception as e:
        logger.error(f"随机推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/labels")
async def get_labels():
    """
    获取所有可用的标签列表
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            query_service = ServiceFactory.create_query_service(nav_conn, sem_conn)

            return {
                "mood": query_service.get_available_moods(),
                "energy": query_service.get_available_energies(),
                "genre": query_service.get_available_genres(),
                "region": query_service.get_available_regions(),
                "scenes": query_service.get_available_scenes()
            }

    except Exception as e:
        logger.error(f"获取标签列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def query_songs(
    mood: Optional[str] = None,
    energy: Optional[str] = None,
    genre: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 50
):
    """
    按标签组合查询歌曲（前端专用）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            query_service = ServiceFactory.create_query_service(nav_conn, sem_conn)
            songs = query_service.query_by_tags(
                mood=mood,
                energy=energy,
                genre=genre,
                region=region,
                limit=limit
            )

            logger.info(f"查询歌曲: {len(songs)} 首")

            return {"success": True, "data": songs}

    except Exception as e:
        logger.error(f"查询歌曲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options")
async def get_query_options():
    """
    获取查询选项（前端专用）
    """
    try:
        with dbs_context() as (nav_conn, sem_conn):
            query_service = ServiceFactory.create_query_service(nav_conn, sem_conn)

            return {
                "success": True,
                "data": {
                    "moods": query_service.get_available_moods(),
                    "energies": query_service.get_available_energies(),
                    "genres": query_service.get_available_genres(),
                    "regions": query_service.get_available_regions()
                }
            }

    except Exception as e:
        logger.error(f"获取查询选项失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
