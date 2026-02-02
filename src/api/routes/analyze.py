"""
分析接口路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from src.utils.analyze import analyze_distribution, analyze_combinations, analyze_by_region, analyze_quality
from src.core.database import connect_sem_db
from src.utils.logger import setup_logger

logger = setup_logger("api_analyze", "api.log", level=logging.INFO)

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
        valid_fields = ['mood', 'energy', 'genre', 'region', 'scene', 'subculture']
        if field not in valid_fields:
            raise HTTPException(status_code=400, detail=f"无效的字段，可用字段: {', '.join(valid_fields)}")
        
        sem_conn = connect_sem_db()
        cursor = sem_conn.execute(f"""
            SELECT {field}, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as percentage
            FROM music_semantic
            GROUP BY {field}
            ORDER BY count DESC
        """)
        
        distribution = []
        for row in cursor:
            distribution.append({
                "label": row[0] if row[0] else "(空值)",
                "count": row[1],
                "percentage": row[2]
            })
        
        sem_conn.close()
        
        logger.info(f"获取 {field} 分布分析，共 {len(distribution)} 个标签")
        
        return DistributionResponse(
            field=field,
            field_name=field.capitalize(),
            distribution=distribution
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分布分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/combinations")
async def get_combinations():
    """
    获取最常见的 Mood + Energy 组合
    """
    try:
        sem_conn = connect_sem_db()
        cursor = sem_conn.execute("""
            SELECT mood, energy, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM music_semantic), 2) as pct
            FROM music_semantic
            GROUP BY mood, energy
            ORDER BY count DESC
            LIMIT 15
        """)
        
        combinations = []
        for row in cursor:
            combinations.append({
                "mood": row[0],
                "energy": row[1],
                "count": row[2],
                "percentage": row[3]
            })
        
        sem_conn.close()
        
        logger.info(f"获取组合分析，共 {len(combinations)} 个组合")
        
        return CombinationResponse(combinations=combinations)
        
    except Exception as e:
        logger.error(f"组合分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/region-genre")
async def get_region_genre():
    """
    获取各地区的流派分布
    """
    try:
        sem_conn = connect_sem_db()
        
        # 获取所有地区
        regions_cursor = sem_conn.execute("SELECT DISTINCT region FROM music_semantic WHERE region != 'None'")
        regions = [row[0] for row in regions_cursor.fetchall()]
        
        result = {}
        for region in regions:
            cursor = sem_conn.execute("""
                SELECT genre, COUNT(*) as count
                FROM music_semantic
                WHERE region = ? AND genre != 'None'
                GROUP BY genre
                ORDER BY count DESC
                LIMIT 5
            """, (region,))
            
            genres = []
            for row in cursor:
                genres.append({
                    "genre": row[0],
                    "count": row[1]
                })
            
            result[region] = genres
        
        sem_conn.close()
        
        logger.info(f"获取地区流派分析，共 {len(result)} 个地区")
        
        return RegionGenreResponse(regions=result)
        
    except Exception as e:
        logger.error(f"地区流派分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality")
async def get_quality():
    """
    获取数据质量分析
    """
    try:
        sem_conn = connect_sem_db()
        
        # 总数
        total = sem_conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]
        
        # 平均置信度
        avg_confidence = sem_conn.execute("SELECT AVG(confidence) FROM music_semantic").fetchone()[0]
        avg_confidence = round(avg_confidence, 2) if avg_confidence else 0.0
        
        # 低置信度歌曲
        low_confidence = sem_conn.execute("SELECT COUNT(*) FROM music_semantic WHERE confidence < 0.5").fetchone()[0]
        low_confidence_pct = round(low_confidence * 100.0 / total, 2) if total > 0 else 0.0
        
        # None 值统计
        none_stats = {}
        for field in ['mood', 'energy', 'scene', 'region', 'subculture', 'genre']:
            none_count = sem_conn.execute(f"SELECT COUNT(*) FROM music_semantic WHERE {field} = 'None'").fetchone()[0]
            none_pct = round(none_count * 100.0 / total, 2) if total > 0 else 0.0
            none_stats[field] = {
                "count": none_count,
                "percentage": none_pct
            }
        
        sem_conn.close()
        
        logger.info("获取数据质量分析")
        
        return QualityResponse(
            total_songs=total,
            average_confidence=avg_confidence,
            low_confidence_count=low_confidence,
            low_confidence_percentage=low_confidence_pct,
            none_stats=none_stats
        )
        
    except Exception as e:
        logger.error(f"质量分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_summary():
    """
    获取数据概览
    """
    try:
        sem_conn = connect_sem_db()
        
        # 总数
        total = sem_conn.execute("SELECT COUNT(*) FROM music_semantic").fetchone()[0]
        
        # 各字段唯一值数量
        unique_counts = {}
        for field in ['mood', 'energy', 'genre', 'region', 'scene', 'subculture']:
            count = sem_conn.execute(f"SELECT COUNT(DISTINCT {field}) FROM music_semantic WHERE {field} != 'None'").fetchone()[0]
            unique_counts[field] = count
        
        # 最新更新时间
        latest = sem_conn.execute("SELECT MAX(created_at) FROM music_semantic").fetchone()[0]
        
        sem_conn.close()
        
        logger.info("获取数据概览")
        
        return {
            "total_songs": total,
            "unique_labels": unique_counts,
            "latest_update": latest
        }
        
    except Exception as e:
        logger.error(f"获取数据概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
