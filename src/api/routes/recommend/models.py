"""
推荐接口请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class RecommendRequest(BaseModel):
    """推荐请求模型"""
    user_id: Optional[str] = None  # 用户ID，不传则自动选择第一个用户
    limit: int = Field(default=30, ge=1, le=100, description="推荐数量，范围1-100")
    filter_recent: bool = True  # 是否过滤最近听过的歌曲
    diversity: bool = True  # 是否启用多样性控制


class RecommendResponse(BaseModel):
    """推荐响应模型"""
    user_id: str
    recommendations: List[dict]
    stats: dict
