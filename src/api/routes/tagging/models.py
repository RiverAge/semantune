"""
标签生成接口请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class TagRequest(BaseModel):
    """标签生成请求模型"""
    title: str = Field(..., min_length=1, max_length=200, description="歌曲标题")
    artist: str = Field(..., min_length=1, max_length=100, description="歌手名称")
    album: str = Field(default="", max_length=200, description="专辑名称")


class TagResponse(BaseModel):
    """标签生成响应模型"""
    title: str
    artist: str
    album: str
    tags: dict
    raw_response: str


class BatchTagRequest(BaseModel):
    """批量标签生成请求模型"""
    songs: List[dict] = Field(..., min_items=1, max_items=50, description="歌曲列表，最多50首")


class TagProgressResponse(BaseModel):
    """标签生成进度响应模型"""
    total: int
    processed: int
    remaining: int
    status: str
