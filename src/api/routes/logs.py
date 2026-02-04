"""
日志查看 API 路由
"""
import logging
import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.settings import LOG_DIR, LOG_FILES
from src.core.response import ApiResponse
from src.utils.logger import setup_logger

logger = setup_logger("api")


router = APIRouter()


class LogFileInfo(BaseModel):
    """日志文件信息"""
    name: str = Field(..., description="日志文件名")
    path: str = Field(..., description="日志文件完整路径")
    size: int = Field(..., description="文件大小（字节）")
    lines: int = Field(..., description="文件行数")


class LogContentRequest(BaseModel):
    """日志内容请求"""
    tail: Optional[int] = Field(default=100, ge=1, le=10000, description="读取最后 N 行")
    head: Optional[int] = Field(default=None, ge=1, le=10000, description="读取前 N 行（优先级高于 tail）")
    filter_level: Optional[str] = Field(default=None, description="过滤日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）")


class LogLine(BaseModel):
    """单行日志"""
    line_number: int = Field(..., description="行号")
    timestamp: Optional[str] = Field(default=None, description="时间戳")
    level: Optional[str] = Field(default=None, description="日志级别")
    module: Optional[str] = Field(default=None, description="模块名称")
    message: str = Field(..., description="日志消息")


class LogContentResponse(BaseModel):
    """日志内容响应"""
    file: str = Field(..., description="日志文件名")
    total_lines: int = Field(..., description="总行数")
    lines: List[LogLine] = Field(..., description="日志行列表")
    filtered: bool = Field(default=False, description="是否进行了过滤")


def get_log_file_info(log_file: str) -> LogFileInfo:
    """
    获取日志文件信息
    
    Args:
        log_file: 日志文件名
        
    Returns:
        日志文件信息
    """
    # 安全检查：确保文件名只包含字母、数字、下划线和点
    if not all(c.isalnum() or c in '._' for c in log_file):
        raise HTTPException(status_code=400, detail="无效的日志文件名")
    
    # 检查文件是否在配置的日志列表中
    if log_file not in LOG_FILES.values():
        known_files = ", ".join(set(LOG_FILES.values()))
        raise HTTPException(
            status_code=400, 
            detail=f"未知的日志文件。可用文件: {known_files}"
        )
    
    # 构建完整路径
    log_path = Path(LOG_DIR) / log_file
    
    # 检查文件是否存在
    if not log_path.exists():
        raise HTTPException(status_code=404, detail=f"日志文件不存在: {log_file}")
    
    # 检查路径是否在日志目录内（防止路径遍历攻击）
    try:
        log_path.resolve().relative_to(Path(LOG_DIR).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="拒绝访问：路径不在日志目录内")
    
    # 获取文件信息
    size = log_path.stat().st_size
    
    # 计算行数
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = sum(1 for _ in f)
    except Exception as e:
        lines = 0
    
    return LogFileInfo(
        name=log_file,
        path=str(log_path),
        size=size,
        lines=lines
    )


def parse_log_line(line: str, line_number: int) -> LogLine:
    """
    解析单行日志
    
    Args:
        line: 日志行内容
        line_number: 行号
        
    Returns:
        解析后的日志行对象
    """
    # 日志格式: 2026-02-02 14:56:52 - api - INFO - 消息
    parts = line.split(" - ", maxsplit=3)
    
    if len(parts) >= 4:
        timestamp = parts[0].strip()
        module = parts[1].strip()
        level = parts[2].strip()
        message = parts[3].strip()
    else:
        timestamp = None
        module = None
        level = None
        message = line.strip()
    
    return LogLine(
        line_number=line_number,
        timestamp=timestamp,
        level=level,
        module=module,
        message=message
    )


def filter_log_by_level(lines: List[str], level: str) -> List[str]:
    """
    按日志级别过滤
    
    Args:
        lines: 日志行列表
        level: 日志级别
        
    Returns:
        过滤后的行列表
    """
    filtered = []
    level_upper = level.upper()
    
    for line in lines:
        # 检查行中是否包含该级别
        if f"- {level_upper} -" in line:
            filtered.append(line)
    
    return filtered


@router.get("", response_model=ApiResponse[List[LogFileInfo]])
async def list_logs():
    """
    列出所有可用的日志文件
    
    返回系统中所有可用的日志文件及其基本信息
    """
    try:
        logs = []
        
        for log_name in set(LOG_FILES.values()):
            try:
                log_info = get_log_file_info(log_name)
                logs.append(log_info)
            except HTTPException:
                # 文件不存在，跳过
                continue
            except Exception as e:
                logger.warning(f"无法获取日志文件 {log_name} 的信息: {e}")
        
        # 按文件名排序
        logs.sort(key=lambda x: x.name)
        
        return ApiResponse.success_response(data=logs)
    
    except Exception as e:
        logger.error(f"列出日志文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{log_file}", response_model=ApiResponse[LogContentResponse])
async def get_log_content(
    log_file: str,
    tail: int = 100,
    head: Optional[int] = None,
    filter_level: Optional[str] = None
):
    """
    获取日志文件内容
    
    参数:
    - log_file: 日志文件名
    - tail: 读取最后 N 行（默认 100）
    - head: 读取前 N 行（如果指定，优先级高于 tail）
    - filter_level: 按日志级别过滤（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    
    返回解析后的日志内容
    """
    try:
        # 获取文件信息
        log_info = get_log_file_info(log_file)
        log_path = Path(log_info.path)
        
        # 读取文件内容
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取日志文件失败: {e}")
        
        # 过滤（如果指定）
        if filter_level:
            all_lines = filter_log_by_level(all_lines, filter_level)
        
        # 选择要读取的行
        if head:
            lines = all_lines[:head]
            start_line = 1
        else:
            lines = all_lines[-tail:]
            start_line = max(1, log_info.lines - len(lines) + 1) if not filter_level else 1
        
        # 解析日志行
        parsed_lines = []
        for idx, line in enumerate(lines, start=start_line):
            parsed_lines.append(parse_log_line(line.strip(), idx))
        
        return ApiResponse.success_response(data=LogContentResponse(
            file=log_file,
            total_lines=log_info.lines,
            lines=parsed_lines,
            filtered=bool(filter_level)
        ))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取日志文件 {log_file} 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{log_file}/size", response_model=ApiResponse[LogFileInfo])
async def get_log_file_info_api(log_file: str):
    """
    获取日志文件信息
    
    返回指定日志文件的基本信息（大小、行数等）
    """
    try:
        log_info = get_log_file_info(log_file)
        return ApiResponse.success_response(data=log_info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日志文件信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
