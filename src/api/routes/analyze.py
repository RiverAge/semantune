"""
分析接口路由
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from src.core.database import sem_db_context
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

logger = setup_logger("api", level=logging.INFO)

router = APIRouter()


class DistributionResponse(BaseModel):
    """分布分析响应模型"""
    field: str
    field_name: str
    distribution: List[Dict[str, Any]]


class CombinationResponse(BaseModel):
    """组合分析响应模型"""
    combinations: List[Dict[str, Any]]


class QualityResponse(BaseModel):
    """质量分析响应模型"""
    total_songs: int
    average_confidence: float
    low_confidence_count: int
    low_confidence_percentage: float
    none_stats: Dict[str, Dict[str, Any]]


class RegionGenreResponse(BaseModel):
    """地区流派分析响应模型"""
    regions: Dict[str, List[Dict[str, Any]]]


@router.get("/distribution/{field}")
async def get_distribution(field: str):
    """
    获取指定字段的分布分析

    可用字段：mood, energy, genre, region, scene, subculture

    - **field**: 字段名称
    """
    try:
        with sem_db_context() as sem_conn:
            analyze_service = ServiceFactory.create_analyze_service(sem_conn)
            result = analyze_service.get_distribution(field)

            logger.info(f"获取 {field} 分布分析，共 {len(result['distribution'])} 个标签")

            return DistributionResponse(
                field=result['field'],
                field_name=result['field_name'],
                distribution=result['distribution']
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分布分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/combinations")
async def get_combinations():
    """
    获取最常见的 Mood + Energy 组合
    """
    try:
        with sem_db_context() as sem_conn:
            analyze_service = ServiceFactory.create_analyze_service(sem_conn)
            result = analyze_service.get_combinations()

            logger.info(f"获取组合分析，共 {len(result['combinations'])} 个组合")

            return CombinationResponse(combinations=result['combinations'])

    except Exception as e:
        logger.error(f"组合分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/region-genre")
async def get_region_genre():
    """
    获取各地区的流派分布
    """
    try:
        with sem_db_context() as sem_conn:
            analyze_service = ServiceFactory.create_analyze_service(sem_conn)
            result = analyze_service.get_region_genre_distribution()

            logger.info(f"获取地区流派分析，共 {len(result['regions'])} 个地区")

            return RegionGenreResponse(regions=result['regions'])

    except Exception as e:
        logger.error(f"地区流派分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality")
async def get_quality():
    """
    获取数据质量分析
    """
    try:
        with sem_db_context() as sem_conn:
            analyze_service = ServiceFactory.create_analyze_service(sem_conn)
            result = analyze_service.get_quality_stats()

            logger.info("获取数据质量分析")

            return QualityResponse(
                total_songs=result['total_songs'],
                average_confidence=result['average_confidence'],
                low_confidence_count=result['low_confidence_count'],
                low_confidence_percentage=result['low_confidence_percentage'],
                none_stats=result['none_stats']
            )

    except Exception as e:
        logger.error(f"数据质量分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_overview():
    """
    获取数据概览
    """
    try:
        with sem_db_context() as sem_conn:
            analyze_service = ServiceFactory.create_analyze_service(sem_conn)
            result = analyze_service.get_overview()

            logger.info("获取数据概览")

            return result

    except Exception as e:
        logger.error(f"获取数据概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
