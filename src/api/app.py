"""
FastAPI 主应用文件
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import recommend, query, tagging, analyze
from src.utils.logger import setup_logger

logger = setup_logger("api", "api.log", level=logging.INFO)

# 创建 FastAPI 应用
app = FastAPI(
    title="Navidrome 语义音乐推荐系统 API",
    description="基于 LLM 语义标签的个性化音乐推荐系统",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的域名
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
        "version": "1.0.0",
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
