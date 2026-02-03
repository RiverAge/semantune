"""
全局异常处理模块 - 统一的异常类和处理器
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class SemantuneException(Exception):
    """基础异常类"""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(SemantuneException):
    """数据库异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class NotFoundException(SemantuneException):
    """资源未找到异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ValidationException(SemantuneException):
    """验证异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class APIException(SemantuneException):
    """API 调用异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


async def semantune_exception_handler(request: Request, exc: SemantuneException) -> JSONResponse:
    """
    Semantune 异常处理器
    
    Args:
        request: FastAPI 请求对象
        exc: Semantune 异常实例
        
    Returns:
        JSONResponse: 格式化的错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details
            },
            "path": str(request.url)
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 异常处理器
    
    Args:
        request: FastAPI 请求对象
        exc: HTTP 异常实例
        
    Returns:
        JSONResponse: 格式化的错误响应
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.detail,
                "type": "HTTPException",
                "details": {}
            },
            "path": str(request.url)
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器 - 捕获所有未处理的异常
    
    Args:
        request: FastAPI 请求对象
        exc: 异常实例
        
    Returns:
        JSONResponse: 格式化的错误响应
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "服务器内部错误",
                "type": "InternalServerError",
                "details": {
                    "exception_type": exc.__class__.__name__,
                    "exception_message": str(exc)
                }
            },
            "path": str(request.url)
        }
    )
