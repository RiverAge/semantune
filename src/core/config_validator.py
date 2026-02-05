"""
配置验证模块 - 验证环境变量和配置项
"""

import os
import sqlite3
from typing import List, Dict, Any
from pathlib import Path

from config.settings import (
    NAV_DB, SEM_DB, LOG_DIR, EXPORT_DIR,
    BASE_URL, MODEL, get_api_key,
    get_recommend_config, get_user_profile_config,
    CORS_ORIGINS
)
from config.constants import get_allowed_labels, get_tagging_api_config


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


def validate_config() -> Dict[str, Any]:
    """
    验证所有配置项
    
    Returns:
        验证结果字典，包含 status 和 errors
        
    Raises:
        ConfigValidationError: 当配置验证失败时
    """
    errors = []
    warnings = []
    
    # 1. 验证 API Key（不阻止启动，仅警告）
    try:
        api_key = get_api_key()
        if not api_key or len(api_key) < 10:
            warnings.append("SEMANTUNE_API_KEY 未设置或无效。请在应用启动后通过前端设置页面配置。")
    except ValueError as e:
        warnings.append(f"API Key 配置错误: {str(e)}。请在应用启动后通过前端设置页面配置。")
    
    # 2. 验证数据库路径
    nav_db_path = Path(NAV_DB)
    sem_db_path = Path(SEM_DB)
    
    if not nav_db_path.exists():
        errors.append(f"""
Navidrome 数据库文件不存在: {NAV_DB}

请按以下步骤挂载 Navidrome 数据库：

1. 找到你的 Navidrome 数据库文件（通常在以下位置）:
   - Docker: <navidrome_container>/data/navidrome.db
   - 直接安装: /var/lib/navidrome/data/navidrome.db

2. 启动容器时挂载数据库目录:
   docker run -d --name semantune -p 8000:8000 \\
     -v $(pwd)/semantune-data:/app/data \\
     -v /path/to/your/navidrome:/app/navidrome:ro \\
     ghcr.io/riverage/semantune:latest

3. 确保挂载目录中包含 navidrome.db 文件

常见的 Navidrome 数据库位置:
   - Docker Compose: ./navidrome-data/navidrome.db
   - Arch Linux: /var/lib/navidrome/navidrome.db
   - macOS: ~/Music/navidrome/navidrome.db
""")
    elif not nav_db_path.is_file():
        errors.append(f"Navidrome 路径不是有效文件: {NAV_DB}")
    else:
        try:
            import sqlite3
            conn = sqlite3.connect(str(nav_db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            if not cursor.fetchone():
                errors.append(f"Navidrome 数据库为空或无有效表: {NAV_DB}")
            conn.close()
        except sqlite3.Error as e:
            errors.append(f"Navidrome 数据库无法访问或损坏: {e}")
    
    if not sem_db_path.parent.exists():
        sem_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 3. 验证目录
    for dir_path, dir_name in [(LOG_DIR, "日志目录"), (EXPORT_DIR, "导出目录")]:
        path = Path(dir_path)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"无法创建 {dir_name} {dir_path}: {str(e)}")
    
    # 4. 验证 API 配置
    if not BASE_URL.startswith(("http://", "https://")):
        errors.append(f"BASE_URL 格式无效: {BASE_URL}")
    
    if not MODEL:
        errors.append("MODEL 配置为空")
    
    # 5. 验证推荐配置
    recommend_config = get_recommend_config()
    if recommend_config.get("default_limit", 0) <= 0:
        errors.append("RECOMMEND_CONFIG.default_limit 必须大于 0")
    
    if recommend_config.get("default_limit", 0) > 100:
        warnings.append("RECOMMEND_CONFIG.default_limit 大于 100，可能影响性能")
    
    # 6. 验证权重配置
    weight_config = get_user_profile_config()
    required_weights = ["play_count", "starred", "in_playlist", "time_decay_days", "min_decay"]
    for weight in required_weights:
        if weight not in weight_config:
            errors.append(f"WEIGHT_CONFIG 缺少必需的权重配置: {weight}")
    
    # 7. 验证 API 配置
    api_config = get_tagging_api_config()
    if api_config.get("timeout", 0) <= 0:
        errors.append("API_CONFIG.timeout 必须大于 0")
    
    if api_config.get("max_tokens", 0) <= 0:
        errors.append("API_CONFIG.max_tokens 必须大于 0")
    
    if not (0 <= api_config.get("temperature", 0) <= 2):
        errors.append("API_CONFIG.temperature 必须在 0-2 之间")
    
    # 8. 验证 CORS 配置
    if not CORS_ORIGINS:
        warnings.append("CORS_ORIGINS 为空，可能影响前端访问")
    
    # 9. 验证标签配置
    allowed_labels = get_allowed_labels()
    if not allowed_labels:
        errors.append("ALLOWED_LABELS 配置为空")
    
    # 构建结果
    result = {
        "status": "ok" if not errors else "error",
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "total_errors": len(errors),
            "total_warnings": len(warnings)
        }
    }
    
    return result


def validate_on_startup() -> None:
    """
    应用启动时验证配置
    
    Raises:
        ConfigValidationError: 当存在严重配置错误时
    """
    validation_result = validate_config()
    
    if validation_result["errors"]:
        error_msg = "配置验证失败:\n" + "\n".join(f"  - {e}" for e in validation_result["errors"])
        raise ConfigValidationError(error_msg)
    
    if validation_result["warnings"]:
        import logging
        logger = logging.getLogger("config")
        logger.warning("配置验证警告:\n" + "\n".join(f"  - {w}" for w in validation_result["warnings"]))
