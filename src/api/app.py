"""
FastAPI 主应用文件
"""
import logging
import os
import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from src.api.routes import recommend, query, tagging, analyze, config, logs
from src.utils.logger import setup_logger
from config.settings import CORS_ORIGINS, VERSION, NAV_DB, SEM_DB
from src.core.exceptions import (
    semantune_exception_handler,
    http_exception_handler,
    general_exception_handler,
    request_validation_exception_handler,
    SemantuneException
)
from src.core.config_validator import validate_on_startup

# 从环境变量读取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

# 打印日志级别信息
print(f"[API] LOG_LEVEL 环境变量: {LOG_LEVEL}")
print(f"[API] 实际日志级别: {logging.getLevelName(log_level)}")

logger = setup_logger("api", level=log_level, console_level=log_level)

# 创建 FastAPI 应用
app = FastAPI(
    title="Navidrome 语义音乐推荐系统 API",
    description="基于 LLM 语义标签的个性化音乐推荐系统",
    version=VERSION
)

# 注册全局异常处理器
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SemantuneException, semantune_exception_handler)
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
app.include_router(config.router, prefix="/api/v1/config", tags=["配置管理"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["日志查看"])


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
    """
    健康检查
    
    检查以下内容：
    - API 服务状态
    - Navidrome 数据库连接
    - 语义数据库连接
    - 数据库文件是否存在
    """
    health_status = {
        "status": "healthy",
        "version": VERSION,
        "checks": {}
    }
    
    # 检查 Navidrome 数据库
    try:
        nav_db_path = Path(NAV_DB)
        if nav_db_path.exists():
            conn = sqlite3.connect(NAV_DB)
            conn.execute("SELECT 1")
            conn.close()
            health_status["checks"]["navidrome_db"] = {
                "status": "ok",
                "path": str(nav_db_path)
            }
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["navidrome_db"] = {
                "status": "error",
                "message": f"数据库文件不存在: {NAV_DB}"
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["navidrome_db"] = {
            "status": "error",
            "message": str(e)
        }
    
    # 检查语义数据库
    try:
        sem_db_path = Path(SEM_DB)
        if sem_db_path.exists():
            conn = sqlite3.connect(SEM_DB)
            conn.execute("SELECT 1")
            conn.close()
            health_status["checks"]["semantic_db"] = {
                "status": "ok",
                "path": str(sem_db_path)
            }
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["semantic_db"] = {
                "status": "error",
                "message": f"数据库文件不存在: {SEM_DB}"
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["semantic_db"] = {
            "status": "error",
            "message": str(e)
        }
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 API 服务启动")
    
    # 验证配置
    try:
        validate_on_startup()
        logger.info("✅ 配置验证通过")
    except Exception as e:
        logger.error(f"❌ 配置验证失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 API 服务关闭")
