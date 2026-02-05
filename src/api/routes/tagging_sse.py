"""
标签生成 SSE (Server-Sent Events) 模块 - 处理实时进度推送
"""

import asyncio
import logging
import os
import sys
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
    logger.info(f"event_generator 开始执行")
    sys.stderr.flush()

    queue = asyncio.Queue()
    sse_clients.append(queue)
    logger.info(f"SSE 客户端连接，当前客户端数: {len(sse_clients)}")
    sys.stderr.flush()

    try:
        logger.info(f"发送初始进度数据: {tagging_progress}")
        yield f"data: {json.dumps(tagging_progress)}\n\n"
        logger.info("发送初始进度数据完成")
        sys.stderr.flush()

        logger.info("发送 hello 心跳包")
        yield ": hello\n\n"
        logger.info("hello 心跳包发送完成")
        sys.stderr.flush()

        last_heartbeat = asyncio.get_event_loop().time()
        iteration = 0

        logger.info("进入主循环...")

        while True:
            try:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=10.0)
                    yield message
                    sys.stderr.flush()

                    if tagging_progress["status"] in ["completed", "failed", "stopped"]:
                        yield "data: [DONE]\n\n"
                        logger.info(f"SSE 任务完成，状态: {tagging_progress['status']}")
                        break
                except asyncio.TimeoutError:
                    iteration += 1
                    current_time = asyncio.get_event_loop().time()

                    logger.debug(f"SSE 心跳检查: iteration={iteration}")

                    if current_time - last_heartbeat >= 5.0:
                        logger.info(f"发送心跳包 {iteration}")
                        yield f": heartbeat {iteration}\n\n"
                        last_heartbeat = current_time
                        sys.stderr.flush()

                    if tagging_progress["status"] in ["completed", "failed"]:
                        yield f"data: {json.dumps(tagging_progress)}\n\n"
                        yield "data: [DONE]\n\n"
                        logger.info(f"SSE 任务完成（检查），状态: {tagging_progress['status']}")
                        break

            except asyncio.CancelledError:
                logger.info("SSE 连接被取消")
                break
            except Exception as e:
                logger.error(f"SSE 生成器内层错误: {e}", exc_info=True)
                break

        logger.info("SSE 主循环结束")

    except asyncio.CancelledError:
        logger.info("SSE 连接被取消 (外层)")
    except Exception as e:
        logger.error(f"SSE 生成器错误 (外层): {e}", exc_info=True)
    finally:
        if queue in sse_clients:
            sse_clients.remove(queue)
        logger.info(f"SSE 客户端断开，剩余: {len(sse_clients)}")
        sys.stderr.flush()


def get_tagging_progress() -> dict:
    """获取当前标签生成进度"""
    return {
        "total": tagging_progress["total"],
        "processed": tagging_progress["processed"],
        "remaining": tagging_progress["total"] - tagging_progress["processed"],
        "status": tagging_progress["status"]
    }


def update_tagging_progress(total: int | None = None, processed: int | None = None, status: str | None = None):
    """更新标签生成进度"""
    if total is not None:
        tagging_progress["total"] = total
    if processed is not None:
        tagging_progress["processed"] = processed
    if status is not None:
        tagging_progress["status"] = status
