"""
标签生成预览模块 - 预览 LLM API 和标签生成结果
"""

import json
import time
import sys
import logging
from typing import Optional, Dict, Any, Tuple

from config.settings import get_api_key, BASE_URL, MODEL, API_PROVIDER, API_CONFIG
from config.constants import ALLOWED_LABELS, PROMPT_TEMPLATE
from src.utils.common import setup_windows_encoding
from src.utils.logger import setup_logger
import requests

# 设置 Windows 控制台编码
setup_windows_encoding()

# 设置日志
logger = setup_logger('tagging_preview', 'tagging_preview.log', level=logging.DEBUG)


def safe_extract_json(text: str) -> Optional[Dict[str, Any]]:
    """提取 JSON，支持处理截断补齐和 Markdown"""
    try:
        # 移除 markdown 代码块
        clean_text = text.replace("```json", "").replace("```", "").strip()
        # 寻找 JSON 对象
        import re
        matches = re.findall(r"\{.*\}", clean_text, re.S)
        if matches:
            return json.loads(matches[-1])  # 取最后一个，应对 Reasoning 模型

        # 针对截断的保底尝试
        if clean_text.startswith("{") and not clean_text.endswith("}"):
            fixed = clean_text + '"}'
            return json.loads(fixed)
    except (json.JSONDecodeError, ValueError, AttributeError):
        return None


def preview_single_song(title: str, artist: str, album: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """预览单首歌的标签生成"""
    logger.info("=" * 60)
    logger.info(f"预览歌曲: {artist} - {title}")
    logger.info(f"专辑: {album}")
    logger.info("=" * 60)
    
    # 生成提示词
    prompt_template = PROMPT_TEMPLATE
    prompt = prompt_template.format(title=title, artist=artist, album=album)
    
    logger.debug(f"📝 提示词预览:")
    logger.debug("-" * 60)
    logger.debug(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    logger.debug("-" * 60)
    
    # 调用 API
    logger.info(f"🔄 正在调用 API...")
    logger.info(f"   提供商: {API_PROVIDER}")
    logger.info(f"   模型: {MODEL}")
    logger.info(f"   端点: {BASE_URL}")
    
    max_retries = API_CONFIG["max_retries"]
    retry_delay = API_CONFIG["retry_delay"]
    retry_backoff = API_CONFIG["retry_backoff"]

    for attempt in range(max_retries):
        try:
            headers = {"Authorization": f"Bearer {get_api_key()}", "Content-Type": "application/json"}
            payload = {
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": API_CONFIG["temperature"],
                "max_tokens": API_CONFIG["max_tokens"]
            }
            
            r = requests.post(BASE_URL, headers=headers, json=payload, timeout=API_CONFIG["timeout"])
            r.raise_for_status()
            
            content = r.json()['choices'][0]['message']['content']
            result = safe_extract_json(content)
        
            if result:
                logger.info(f"✅ 成功获取标签:")
                logger.info(f"   Mood: {result.get('mood', 'N/A')}")
                logger.info(f"   Energy: {result.get('energy', 'N/A')}")
                logger.info(f"   Scene: {result.get('scene', 'N/A')}")
                logger.info(f"   Region: {result.get('region', 'N/A')}")
                logger.info(f"   Subculture: {result.get('subculture', 'N/A')}")
                logger.info(f"   Genre: {result.get('genre', 'N/A')}")
                logger.info(f"   Confidence: {result.get('confidence', 'N/A')}")
                
                # 验证标签是否在白名单中
                logger.info(f"🔍 标签验证:")
                all_valid = True
                for key, value in result.items():
                    if key == 'confidence':
                        continue
                    if key in ALLOWED_LABELS:
                        if value in ALLOWED_LABELS[key]:
                            logger.info(f"   ✅ {key}: {value} (有效)")
                        else:
                            logger.warning(f"   ❌ {key}: {value} (无效! 应为: {', '.join(sorted(ALLOWED_LABELS[key]))})")
                            all_valid = False
                    else:
                        logger.warning(f"   ⚠️  {key}: {value} (未知字段)")
                
                return result, all_valid
            else:
                logger.error(f"❌ 无法解析 JSON 响应")
                logger.debug(f"原始响应: {content[:500]}")
                return None, False
                 
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                # 计算退避延迟时间
                delay = retry_delay * (retry_backoff ** attempt)
                logger.warning(f"⚠️  API 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                logger.warning(f"   {delay}秒后重试...")
                time.sleep(delay)
            else:
                logger.error(f"❌ API 请求失败，已达到最大重试次数 ({max_retries}): {e}")
                return None, False
        except Exception as e:
            logger.error(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return None, False


def preview_batch_songs(test_cases):
    """批量预览多首歌"""
    logger.info("=" * 60)
    logger.info(f"批量预览模式 - 共 {len(test_cases)} 首歌")
    logger.info("=" * 60)
    
    success_count = 0
    valid_count = 0
    
    for idx, (title, artist, album) in enumerate(test_cases, 1):
        logger.info(f"[{idx}/{len(test_cases)}]")
        result, is_valid = preview_single_song(title, artist, album)
        
        if result:
            success_count += 1
            if is_valid:
                valid_count += 1
    
    # 统计结果
    logger.info("=" * 60)
    logger.info(f"预览结果汇总")
    logger.info("=" * 60)
    logger.info(f"总预览数: {len(test_cases)}")
    logger.info(f"成功响应: {success_count} ({success_count/len(test_cases)*100:.1f}%)")
    logger.info(f"标签有效: {valid_count} ({valid_count/len(test_cases)*100:.1f}%)")
    logger.info("=" * 60)


def main() -> None:
    """主函数"""
    logger.info("=" * 60)
    logger.info("🎵 LLM 标签生成预览工具")
    logger.info("=" * 60)
    
    # 显示当前配置
    logger.info(f"当前配置:")
    logger.info(f"  API 提供商: {API_PROVIDER}")
    logger.info(f"  模型: {MODEL}")
    logger.info(f"  端点: {BASE_URL}")
    logger.info(f"  API Key: {API_KEY[:20]}...{API_KEY[-4:]}")
    
    # 预设测试用例
    test_cases = [
        ("Bohemian Rhapsody", "Queen", "A Night at the Opera"),
        ("Shape of You", "Ed Sheeran", "÷ (Divide)"),
        ("夜曲", "周杰伦", "十一月的萧邦"),
        ("Lose Yourself", "Eminem", "8 Mile"),
        ("Hotel California", "Eagles", "Hotel California"),
    ]
    
    print(f"\n请选择预览模式:")
    print(f"  1. 单首歌预览")
    print(f"  2. 批量预览 (预设 {len(test_cases)} 首歌)")
    print(f"  3. 自定义批量预览")
    print(f"  0. 退出")
    
    choice = input(f"\n请选择 (0-3): ").strip()
    
    if choice == "0":
        logger.info("再见！")
        return
    
    elif choice == "1":
        print(f"\n请输入歌曲信息:")
        title = input(f"  歌名: ").strip()
        artist = input(f"  歌手: ").strip()
        album = input(f"  专辑 (可选): ").strip() or "Unknown"
        
        if title and artist:
            preview_single_song(title, artist, album)
        else:
            logger.error(f"歌名和歌手不能为空")
    
    elif choice == "2":
        preview_batch_songs(test_cases)
    
    elif choice == "3":
        print(f"\n请输入预览歌曲 (格式: 歌名,歌手,专辑)，每行一首，空行结束:")
        custom_cases = []
        while True:
            line = input(f"  > ").strip()
            if not line:
                break
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 2:
                title = parts[0]
                artist = parts[1]
                album = parts[2] if len(parts) > 2 else "Unknown"
                custom_cases.append((title, artist, album))
            else:
                logger.warning(f"格式错误，已跳过")
        
        if custom_cases:
            preview_batch_songs(custom_cases)
        else:
            logger.error(f"没有输入有效的预览歌曲")
    
    else:
        logger.error(f"无效选择")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("已退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
