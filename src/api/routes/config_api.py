"""
API配置管理 - .env文件相关配置
"""
import logging
from pathlib import Path
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from src.core.response import ApiResponse
from src.utils.logger import setup_logger

logger = setup_logger("api", level=logging.INFO)


class ApiConfig(BaseModel):
    """API 配置模型"""
    api_key: str = Field(..., min_length=1, description="API Key")
    base_url: Optional[str] = Field(None, description="API Base URL")
    model: Optional[str] = Field(None, description="模型名称")


class ApiConfigResponse(BaseModel):
    """API 配置响应模型"""
    api_key: str  # 脱敏显示
    base_url: str
    model: str
    is_configured: bool


def get_env_file_path() -> Path:
    """获取 .env 文件路径"""
    from config.settings import BASE_DIR
    return BASE_DIR / ".env"


def mask_api_key(api_key: str) -> str:
    """脱敏 API Key，只显示前4位和后4位"""
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"


def update_env_file(key: str, value: str) -> None:
    """
    更新 .env 文件中的配置项
    
    Args:
        key: 环境变量名
        value: 环境变量值
    """
    env_path = get_env_file_path()
    
    # 如果 .env 文件不存在，创建它
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n")
        logger.info(f"创建 .env 文件并设置 {key}")
        return
    
    # 读取现有内容
    content = env_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # 查找并更新或添加配置项
    updated = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        elif stripped.startswith(f"{key} "):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        new_lines.append(f"{key}={value}")
    
    # 写回文件
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    logger.info(f"更新 .env 文件中的 {key}")


async def get_api_config():
    """
    获取当前 API 配置
    
    返回 API 配置信息，API Key 会脱敏显示
    """
    try:
        from config.settings import get_api_key, BASE_URL, MODEL
        
        api_key = get_api_key()
        
        return ApiResponse.success_response(data={
            "api_key": mask_api_key(api_key),
            "base_url": BASE_URL,
            "model": MODEL,
            "is_configured": bool(api_key)
        })
    
    except ValueError as e:
        # API Key 未配置
        return ApiResponse.success_response(data={
            "api_key": "",
            "base_url": "https://integrate.api.nvidia.com/v1/chat/completions",
            "model": "meta/llama-3.3-70b-instruct",
            "is_configured": False
        })
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def update_api_config(config: ApiConfig):
    """
    更新 API 配置
    
    - **api_key**: API Key
    - **base_url**: API Base URL（可选）
    - **model**: 模型名称（可选）
    
    配置会保存到 .env 文件中
    """
    try:
        # 更新 API Key
        update_env_file("SEMANTUNE_API_KEY", config.api_key)
        
        # 如果提供了 base_url，也更新
        if config.base_url:
            update_env_file("SEMANTUNE_BASE_URL", config.base_url)
        
        # 如果提供了 model，也更新
        if config.model:
            update_env_file("SEMANTUNE_MODEL", config.model)
        
        # 重新加载环境变量以使新配置生效
        from config.settings import reload_env
        reload_env()
        
        logger.info("API 配置已更新并重新加载")
        
        return ApiResponse.success_response(data={
            "message": "配置已保存",
            "api_key": mask_api_key(config.api_key)
        })
    
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def reset_api_config():
    """
    重置 API 配置
    
    清除 .env 文件中的 API Key 配置
    """
    try:
        env_path = get_env_file_path()
        
        if not env_path.exists():
            return ApiResponse.success_response(data={
                "message": "配置文件不存在，无需重置"
            })
        
        # 读取现有内容
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        # 移除 SEMANTUNE_API_KEY 行
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if not (stripped.startswith("SEMANTUNE_API_KEY=") or 
                    stripped.startswith("SEMANTUNE_API_KEY ")):
                new_lines.append(line)
        
        # 写回文件
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        
        logger.info("API 配置已重置")
        
        return ApiResponse.success_response(data={
            "message": "配置已重置"
        })
    
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
