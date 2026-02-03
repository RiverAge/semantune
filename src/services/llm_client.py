"""
LLM API 客户端模块 - 封装 LLM API 调用逻辑
"""

import logging
import re
import json
import time
import requests
from typing import Optional, Dict, Any, Tuple

from config.settings import get_api_key, BASE_URL, MODEL
from config.constants import get_prompt_template, get_tagging_api_config
from src.utils.logger import setup_logger

logger = setup_logger("llm_client", level=logging.DEBUG)


class LLMClient:
    """LLM API 客户端"""

    def _safe_extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从 LLM 响应中提取 JSON

        Args:
            text: LLM 返回的原始文本

        Returns:
            解析后的 JSON 字典，如果解析失败则返回 None
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
        except (json.JSONDecodeError, ValueError, AttributeError):
            return None

    def call_llm_api(self, title: str, artist: str, album: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        调用 LLM API 生成标签

        Args:
            title: 歌曲标题
            artist: 歌手名称
            album: 专辑名称

        Returns:
            Tuple[Optional[Dict[str, Any]], str]:
                - 解析后的标签字典
                - 原始 API 响应内容
        """
        prompt_template = get_prompt_template()
        prompt = prompt_template.format(title=title, artist=artist, album=album)

        api_config = get_tagging_api_config()

        headers = {"Authorization": f"Bearer {get_api_key()}", "Content-Type": "application/json"}
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": api_config.get("temperature", 0.1),
            "max_tokens": api_config.get("max_tokens", 1024)
        }

        max_retries = api_config.get("max_retries", 3)
        retry_delay = api_config.get("retry_delay", 1)
        retry_backoff = api_config.get("retry_backoff", 2)

        # Debug: 输出发送给 LLM 的请求
        logger.debug(f"=== 发送给 LLM 的请求 ===")
        logger.debug(f"歌曲信息: {artist} - {title} ({album})")
        logger.debug(f"API URL: {BASE_URL}")
        logger.debug(f"请求头: {headers}")
        logger.debug(f"请求体: {json.dumps(payload, ensure_ascii=False, indent=2)}")

        for attempt in range(max_retries):
            try:
                r = requests.post(BASE_URL, headers=headers, json=payload, timeout=api_config.get("timeout", 60))
                r.raise_for_status()
                content = r.json()['choices'][0]['message']['content']
                
                # Debug: 输出 LLM 的回复
                logger.debug(f"=== LLM 的回复 ===")
                logger.debug(f"状态码: {r.status_code}")
                logger.debug(f"原始响应内容: {content}")
                
                parsed_json = self._safe_extract_json(content)
                logger.debug(f"解析后的 JSON: {json.dumps(parsed_json, ensure_ascii=False, indent=2) if parsed_json else '解析失败'}")
                
                return parsed_json, content
            except requests.exceptions.RequestException as e:
                logger.debug(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    delay = retry_delay * (retry_backoff ** attempt)
                    time.sleep(delay)
                else:
                    raise

        return None, ""
