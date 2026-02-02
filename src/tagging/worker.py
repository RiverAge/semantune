"""
语义标签生成模块 - 使用 LLM 为歌曲打标签
"""

import re
import json
import time
import sys
import requests
import logging
from typing import Optional, Tuple, Dict, Any

from config.settings import NAV_DB, SEM_DB, API_KEY, BASE_URL, MODEL, LOG_DIR, API_PROVIDER, API_CONFIG
from config.constants import ALLOWED_LABELS, PROMPT_TEMPLATE
from src.core.database import connect_nav_db, connect_sem_db
from src.core.schema import init_semantic_db
from src.utils.logger import setup_logger

# 设置日志
logger = setup_logger('tagging', 'semantic_processing.log', level=logging.DEBUG)


def safe_extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    从 LLM 响应中提取 JSON，支持处理截断补齐和 Markdown 代码块
    
    Args:
        text: LLM 返回的原始文本
        
    Returns:
        解析后的 JSON 字典，如果解析失败则返回 None
        
    处理逻辑:
        1. 移除 Markdown 代码块标记 (```json ... ```)
        2. 查找所有 JSON 对象
        3. 取最后一个匹配（应对 Reasoning 模型）
        4. 如果 JSON 被截断，尝试补齐
    """
    try:
        # 移除 markdown 代码块
        clean_text = re.sub(r"```json\s*|\s*```", "", text).strip()
        # 寻找 JSON 对象
        matches = re.findall(r"\{.*\}", clean_text, re.S)
        if matches:
            return json.loads(matches[-1])  # 取最后一个，应对 Reasoning 模型

        # 针对截断的保底尝试
        if clean_text.startswith("{") and not clean_text.endswith("}"):
            fixed = clean_text + '"}'
            return json.loads(fixed)
    except (json.JSONDecodeError, ValueError, AttributeError) as e:
        # 记录具体的错误类型，便于调试
        return None


def nim_classify(title: str, artist: str, album: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    调用 LLM API 为歌曲生成语义标签（带重试机制）
    
    Args:
        title: 歌曲标题
        artist: 歌手名称
        album: 专辑名称
        
    Returns:
        Tuple[Optional[Dict[str, Any]], str]:
            - 解析后的标签字典（包含 mood, energy, scene, region, subculture, genre, confidence）
            - 原始 API 响应内容
            
    Raises:
        requests.HTTPError: API 请求失败且重试次数用尽时抛出
    """
    # 根据配置的提供商生成对应的提示词模板
    prompt_template = PROMPT_TEMPLATE
    prompt = prompt_template.format(
        title=title, artist=artist, album=album
    )

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": API_CONFIG["temperature"],
        "max_tokens": API_CONFIG["max_tokens"]
    }

    max_retries = API_CONFIG["max_retries"]
    retry_delay = API_CONFIG["retry_delay"]
    retry_backoff = API_CONFIG["retry_backoff"]

    for attempt in range(max_retries):
        try:
            r = requests.post(BASE_URL, headers=headers, json=payload, timeout=API_CONFIG["timeout"])
            r.raise_for_status()
            content = r.json()['choices'][0]['message']['content']
            return safe_extract_json(content), content
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                # 计算退避延迟时间
                delay = retry_delay * (retry_backoff ** attempt)
                logger.warning(f"API 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}, {delay}秒后重试...")
                time.sleep(delay)
            else:
                logger.error(f"API 请求失败，已达到最大重试次数 ({max_retries}): {e}")
                raise


def normalize(field: str, value: Any) -> str:
    """
    规范化标签值，确保标签在白名单中
    
    Args:
        field: 标签字段名（如 'mood', 'energy' 等）
        value: 原始标签值
        
    Returns:
        规范化后的标签值，如果不在白名单中则返回 'None'
    """
    if not value:
        return "None"
    val_str = str(value).strip().lower()
    lookup = {v.lower(): v for v in ALLOWED_LABELS[field]}
    return lookup.get(val_str, "None")


def format_time(seconds: float) -> str:
    """
    格式化时间显示为 HH:MM:SS 格式
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的时间字符串，如 "01:23:45"
    """
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    """主函数 - 处理所有未打标签的歌曲"""
    nav = connect_nav_db()
    sem = connect_sem_db()

    # 初始化表结构
    init_semantic_db(sem)

    # 获取进度
    done_ids = {row['file_id'] for row in sem.execute("SELECT file_id FROM music_semantic").fetchall()}
    all_songs = nav.execute("SELECT id, title, artist, album FROM media_file").fetchall()
    todo = [s for s in all_songs if str(s['id']) not in done_ids]

    total = len(todo)
    if total == 0:
        logger.info("✅ All songs processed.")
        return

    logger.info(f"🎵 Processing {total} new songs. (Total in Library: {len(all_songs)})")
    start_time = time.time()
    success = 0

    # 循环处理并记录日志
    for idx, s in enumerate(todo, 1):
        meta = f"{s['artist']} - {s['title']}"
        try:
            t0 = time.time()
            # 获取结果
            res, raw_content = nim_classify(s["title"], s["artist"], s["album"])
            elapsed = time.time() - t0

            if not res:
                raise ValueError("Failed to parse JSON from AI response")

            # 规范化
            mood = normalize("mood", res.get("mood"))
            energy = normalize("energy", res.get("energy"))
            scene = normalize("scene", res.get("scene"))
            region = normalize("region", res.get("region"))
            subculture = normalize("subculture", res.get("subculture"))
            genre = normalize("genre", res.get("genre"))
            conf = float(res.get("confidence", 0.0))

            # 写入数据库
            sem.execute("""
                INSERT OR REPLACE INTO music_semantic (
                    file_id, title, artist, album, mood, energy, scene,
                    region, subculture, genre, confidence, model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(s['id']), s['title'], s['artist'], s['album'],
                  mood, energy, scene, region, subculture, genre,
                  conf, MODEL))
            sem.commit()
            success += 1

            # 详细日志写入
            logger.debug(
                f"[{idx}/{total}] 🎧 {meta} | "
                f"🧠 Raw LLM Content: {raw_content[:200]}... | "
                f"🧾 Stored: {mood}|{energy}|{region}|{subculture}|{genre} (Conf: {conf}) | "
                f"✅ Done in {elapsed:.2f}s"
            )

            # 控制台进度条
            avg_time = (time.time() - start_time) / success
            eta = avg_time * (total - idx)
            disp_meta = (meta[:30] + '..') if len(meta) > 30 else meta
            sys.stdout.write(f"\r进度:[{idx}/{total}] ETA:{format_time(eta)} | {disp_meta:<35}")
            sys.stdout.flush()

        except Exception as e:
            logger.error(f"❌ FAILED: {meta} | Error: {str(e)}")
            time.sleep(API_CONFIG["retry_delay"])

    logger.info(f"🏁 Finished. Processed {success}/{total} songs in {format_time(time.time()-start_time)}")


if __name__ == "__main__":
    main()
