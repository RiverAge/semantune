"""
统一的 API 响应模型
"""

from typing import Generic, List, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一的 API 响应格式"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")
    message: Optional[str] = Field(None, description="提示消息")

    @classmethod
    def success_response(cls, data: T = None, message: str = None) -> "ApiResponse[T]":
        """创建成功响应"""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(cls, message: str, error_type: str = None, details: Dict[str, Any] = None) -> "ApiResponse[T]":
        """创建错误响应"""
        error_info = {"message": message}
        if error_type:
            error_info["type"] = error_type
        if details:
            error_info["details"] = details
        return cls(success=False, error=error_info)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
