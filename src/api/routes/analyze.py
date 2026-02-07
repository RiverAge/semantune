"""
分析接口路由
"""
import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from config.constants import get_allowed_labels
from src.core.database import sem_db_context
from src.core.response import ApiResponse
from src.core.exceptions import SemantuneException
from src.services.service_factory import ServiceFactory
from src.utils.logger import setup_logger

# 从环境变量读取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logger = setup_logger("api", level=log_level, console_level=log_level)

router = APIRouter()

# 有效的字段列表
def get_valid_fields() -> List[str]:
    """获取有效的字段列表"""
    return list(get_allowed_labels().keys())

VALID_FIELDS = get_valid_fields()


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

    可用字段：mood, energy, genre, style, scene, region, culture, language

    - **field**: 字段名称
    """
    # 输入验证
    if field not in VALID_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"无效的字段 '{field}'，可用字段: {', '.join(VALID_FIELDS)}"
        )
    
    try:
        with sem_db_context() as sem_conn:
            analyze_service = ServiceFactory.create_analyze_service(sem_conn)
            result = analyze_service.get_distribution(field)

            logger.debug(f"获取 {field} 分布分析，共 {len(result['distribution'])} 个标签")

            return ApiResponse.success_response(
                data=DistributionResponse(
                    field=result['field'],
                    field_name=result['field_name'],
                    distribution=result['distribution']
                )
            )

    except SemantuneException as e:
        raise
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

            logger.debug(f"获取组合分析，共 {len(result['combinations'])} 个组合")

            return ApiResponse.success_response(
                data=CombinationResponse(combinations=result['combinations'])
            )

    except SemantuneException as e:
        raise
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

            logger.debug(f"获取地区流派分析，共 {len(result['regions'])} 个地区")

            return ApiResponse.success_response(
                data=RegionGenreResponse(regions=result['regions'])
            )

    except SemantuneException as e:
        raise
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


@router.get("/health")
async def get_health():
    """
    获取系统健康度概览
    包含标签覆盖率、重复项数量等综合指标
    """
    try:
        from src.core.database import nav_db_context

        # 从Navidrome获取总歌曲数
        with nav_db_context() as nav_conn:
            total_songs = nav_conn.execute("SELECT COUNT(*) FROM media_file").fetchone()[0]

        with sem_db_context() as sem_conn:
            # 已标签歌曲数
            tagged_songs = sem_conn.execute(
                "SELECT COUNT(*) FROM music_semantic WHERE mood IS NOT NULL AND mood != 'None'"
            ).fetchone()[0]

            # 标签覆盖率
            tag_coverage = (tagged_songs / total_songs * 100) if total_songs > 0 else 0

            # 获取平均置信度
            avg_confidence = sem_conn.execute(
                "SELECT AVG(CAST(confidence AS REAL)) FROM music_semantic WHERE confidence IS NOT NULL"
            ).fetchone()[0] or 0

        # 获取重复项数量
        with nav_db_context() as nav_conn:
            duplicate_service = ServiceFactory.create_duplicate_detection_service(nav_conn)
            duplicate_result = duplicate_service.detect_all_duplicates()
            duplicate_count = duplicate_result['summary']['total_issues']

        # 计算健康度分数
        # 基础分 100
        # 标签覆盖率权重 40%
        # 平均置信度权重 30%
        # 重复项影响权重 30%
        health_score = 100
        health_score -= (1 - min(tag_coverage / 100, 1)) * 40
        health_score -= (1 - avg_confidence) * 30
        health_score -= min(duplicate_count / 10, 1) * 30
        health_score = max(0, min(100, health_score))

        # 确定健康级别
        if health_score >= 90:
            health_level = 'excellent'
        elif health_score >= 70:
            health_level = 'good'
        elif health_score >= 50:
            health_level = 'warning'
        else:
            health_level = 'error'

        logger.info(f"获取系统健康度: 分数={health_score:.1f}, 级别={health_level}")

        return {
            "success": True,
            "data": {
                "health_score": round(health_score, 1),
                "health_level": health_level,
                "total_songs": total_songs,
                "tagged_songs": tagged_songs,
                "tag_coverage": round(tag_coverage, 1),
                "average_confidence": round(avg_confidence, 2),
                "duplicate_count": duplicate_count,
                "issues": {
                    "duplicate_songs": duplicate_result['summary']['duplicate_song_groups'],
                    "duplicate_albums": duplicate_result['summary']['duplicate_album_groups'],
                    "duplicate_songs_in_album": duplicate_result['summary']['duplicate_songs_in_album_groups']
                }
            }
        }

    except Exception as e:
        logger.error(f"获取系统健康度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_overview():
    """
    获取数据概览（前端专用）
    """
    try:
        from src.core.database import nav_db_context

        # 从Navidrome获取总歌曲数
        with nav_db_context() as nav_conn:
            total_songs = nav_conn.execute("SELECT COUNT(*) FROM media_file").fetchone()[0]

        with sem_db_context() as sem_conn:
            # 已标签歌曲数
            tagged_songs = sem_conn.execute("SELECT COUNT(*) FROM music_semantic WHERE mood IS NOT NULL AND mood != 'None'").fetchone()[0]

            # 未标签歌曲数
            untagged_songs = total_songs - tagged_songs

            # 标签覆盖率
            tag_coverage = (tagged_songs / total_songs * 100) if total_songs > 0 else 0
            
            # 情绪分布
            mood_dist = sem_conn.execute("""
                SELECT mood, COUNT(*) as count
                FROM music_semantic
                WHERE mood IS NOT NULL AND mood != 'None'
                GROUP BY mood
            """).fetchall()
            mood_distribution = {row[0]: row[1] for row in mood_dist}
            
            # 能量分布
            energy_dist = sem_conn.execute("""
                SELECT energy, COUNT(*) as count
                FROM music_semantic
                WHERE energy IS NOT NULL AND energy != 'None'
                GROUP BY energy
            """).fetchall()
            energy_distribution = {row[0]: row[1] for row in energy_dist}
            
            # 流派分布
            genre_dist = sem_conn.execute("""
                SELECT genre, COUNT(*) as count
                FROM music_semantic
                WHERE genre IS NOT NULL AND genre != 'None'
                GROUP BY genre
            """).fetchall()
            genre_distribution = {row[0]: row[1] for row in genre_dist}
            
            # 地区分布
            region_dist = sem_conn.execute("""
                SELECT region, COUNT(*) as count
                FROM music_semantic
                WHERE region IS NOT NULL AND region != 'None'
                GROUP BY region
            """).fetchall()
            region_distribution = {row[0]: row[1] for row in region_dist}
            
            logger.info("获取整体统计数据")
        
        return {
            "success": True,
            "data": {
                "total_songs": total_songs,
                "tagged_songs": tagged_songs,
                "untagged_songs": untagged_songs,
                "tag_coverage": tag_coverage,
                "mood_distribution": mood_distribution,
                "energy_distribution": energy_distribution,
                "genre_distribution": genre_distribution,
                "region_distribution": region_distribution
            }
        }

    except Exception as e:
        logger.error(f"获取数据概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
