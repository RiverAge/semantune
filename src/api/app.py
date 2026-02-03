"""
FastAPI 主应用文件
"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from src.api.routes import recommend, query, tagging, analyze
from src.utils.logger import setup_logger
from config.settings import CORS_ORIGINS, VERSION
from src.core.exceptions import (
    semantune_exception_handler,
    http_exception_handler,
    general_exception_handler,
    SemantuneException
)

logger = setup_logger("api", level=logging.INFO)

# 创建 FastAPI 应用
app = FastAPI(
    title="Navidrome 语义音乐推荐系统 API",
    description="基于 LLM 语义标签的个性化音乐推荐系统",
    version=VERSION
)

# 注册全局异常处理器
app.add_exception_handler(SemantuneException, semantune_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 配置 CORS - 从环境变量读取允许的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 从环境变量读取，默认允许本地开发端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(recommend.router, prefix="/api/v1/recommend", tags=["推荐"])
app.include_router(query.router, prefix="/api/v1/query", tags=["查询"])
app.include_router(tagging.router, prefix="/api/v1/tagging", tags=["标签生成"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["分析"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Navidrome 语义音乐推荐系统 API",
        "version": VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 API 服务启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 API 服务关闭")
