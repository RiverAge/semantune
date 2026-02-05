"""
标签生成 SSE (Server-Sent Events) 模块 - 处理实时进度推送
"""

import asyncio
import logging
import os
from typing import List

from src.utils.logger import setup_logger
import json

# 从环境变量读取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, LOG_LEVEL, logging.INFO)

logger = setup_logger("api", level=log_level, console_level=log_level)

# 全局进度跟踪
tagging_progress = {
    "total": 0,
    "processed": 0,
    "status": "idle"
}

# SSE 客户端队列
sse_clients: List[asyncio.Queue] = []


async def broadcast_progress():
    """向所有 SSE 客户端广播进度"""
    if sse_clients:
        message = f"data: {json.dumps(tagging_progress)}\n\n"
        for queue in sse_clients:
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"发送进度失败: {e}")


async def event_generator():
    """
    SSE 事件生成器

    生成实时进度事件流，包含心跳包保持连接
    """
    queue = asyncio.Queue()
    sse_clients.append(queue)

    try:
        # 发送初始状态
        yield f"data: {json.dumps(tagging_progress)}\n\n"
        yield f"event: connected\ndata: ping\n\n"

        while True:
            try:
                # 使用 asyncio.wait_for 设置超时
                message = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield message

                # 如果任务完成，关闭连接
                if tagging_progress["status"] in ["completed", "failed", "stopped"]:
                    yield "event: done\ndata: [DONE]\n\n"
                    break
            except asyncio.TimeoutError:
                # 发送心跳包保持连接
                yield ": keep-alive\n\n"

    except asyncio.CancelledError:
        logger.debug("SSE 连接被取消")
    except Exception as e:
        logger.error(f"SSE 生成器错误: {e}")
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    finally:
        if queue in sse_clients:
            sse_clients.remove(queue)
            logger.debug(f"SSE 客户端断开，剩余: {len(sse_clients)}")


def get_tagging_progress() -> dict:
    """获取当前标签生成进度"""
    return {
        "total": tagging_progress["total"],
        "processed": tagging_progress["processed"],
        "remaining": tagging_progress["total"] - tagging_progress["processed"],
        "status": tagging_progress["status"]
    }


def update_tagging_progress(total: int = None, processed: int = None, status: str = None):
    """更新标签生成进度"""
    if total is not None:
        tagging_progress["total"] = total
    if processed is not None:
        tagging_progress["processed"] = processed
    if status is not None:
        tagging_progress["status"] = status
