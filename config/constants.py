"""
常量定义 - 标签白名单、魔法数字等
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Set, List

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 时间常量（秒）
SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60

# 数据库相关常量
DB_INDEXES = [
    # music_semantic 表索引
    "CREATE INDEX IF NOT EXISTS idx_music_semantic_mood ON music_semantic(mood)",
    "CREATE INDEX IF NOT EXISTS idx_music_semantic_energy ON music_semantic(energy)",
    "CREATE INDEX IF NOT EXISTS idx_music_semantic_genre ON music_semantic(genre)",
    "CREATE INDEX IF NOT EXISTS idx_music_semantic_region ON music_semantic(region)",
    "CREATE INDEX IF NOT EXISTS idx_music_semantic_scene ON music_semantic(scene)",
    "CREATE INDEX IF NOT EXISTS idx_music_semantic_confidence ON music_semantic(confidence)",
    "CREATE INDEX IF NOT EXISTS idx_music_semantic_updated_at ON music_semantic(updated_at)",
]

# 缓存配置
CACHE_CONFIG = {
    "user_profile_ttl": 300,  # 5分钟
    "distribution_ttl": 600,  # 10分钟
    "quality_stats_ttl": 600,  # 10分钟
    "enabled": True,
}


# ==================== YAML 配置加载 ====================

def _load_yaml_config(config_file: str) -> Dict[str, Any]:
    """
    从 YAML 文件加载配置
    
    Args:
        config_file: 配置文件名（相对于 config 目录）
        
    Returns:
        配置字典
    """
    config_path = BASE_DIR / "config" / config_file
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _save_yaml_config(config_file: str, config: Dict[str, Any]) -> None:
    """
    保存配置到 YAML 文件
    
    Args:
        config_file: 配置文件名（相对于 config 目录）
        config: 配置字典
    """
    config_path = BASE_DIR / "config" / config_file
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ==================== 标签配置 ====================

def get_allowed_labels() -> Dict[str, Set[str]]:
    """
    获取标签白名单
    
    Returns:
        标签白名字典
    """
    config = _load_yaml_config("tagging_config.yaml")
    labels = config.get("allowed_labels", {})
    
    # 转换为 set
    return {k: set(v) for k, v in labels.items()}


def get_scene_presets() -> Dict[str, Dict[str, List[str]]]:
    """
    获取场景预设
    
    Returns:
        场景预设字典
    """
    config = _load_yaml_config("tagging_config.yaml")
    return config.get("scene_presets", {})


def get_prompt_template() -> str:
    """
    获取 LLM 提示词模板（从标签白名单动态生成）
    
    Returns:
        提示词模板字符串
    """
    allowed_labels = get_allowed_labels()
    
    # 生成标签列表字符串
    labels_text = ""
    for key, values in allowed_labels.items():
        sorted_values = sorted(values)
        labels_text += f"- {key}: {', '.join(sorted_values)}\n"
    
    # 动态生成提示词模板
    template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a robotic music classification engine. You MUST output ONLY valid JSON.
You MUST choose labels ONLY from the provided lists. DO NOT create new labels.

ALLOWED LABELS:
""" + labels_text + """Rules:
1. 'Groovy' is a Mood, NOT an Energy level. Energy must be Low, Medium, or High.
2. 'genre' must be a single word from the list. (e.g., Use 'Pop' for Pop/R&B).
3. 'scene' must be exactly from the list. Use 'None' if unsure.
4. No conversational filler. Just the JSON object.

Example Output:
{
  "mood": "Epic",
  "energy": "High",
  "scene": "None",
  "region": "Chinese",
  "subculture": "None",
  "genre": "Rock",
  "confidence": 0.95
}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Classify:
Title: {title}
Artist: {artist}
Album: {album}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    return template


def get_tagging_api_config() -> Dict[str, Any]:
    """
    获取标签生成 API 配置
    
    Returns:
        API 配置字典
    """
    config = _load_yaml_config("tagging_config.yaml")
    return config.get("api", {})


def update_allowed_labels(labels: Dict[str, List[str]]) -> None:
    """
    更新标签白名单
    
    Args:
        labels: 新的标签白名单
    """
    # 读取现有配置
    full_config = _load_yaml_config("tagging_config.yaml")
    
    # 更新标签白名单
    full_config["allowed_labels"] = labels
    
    # 保存
    _save_yaml_config("tagging_config.yaml", full_config)


def update_scene_presets(presets: Dict[str, Dict[str, List[str]]]) -> None:
    """
    更新场景预设
    
    Args:
        presets: 新的场景预设
    """
    # 读取现有配置
    full_config = _load_yaml_config("tagging_config.yaml")
    
    # 更新场景预设
    full_config["scene_presets"] = presets
    
    # 保存
    _save_yaml_config("tagging_config.yaml", full_config)


def update_prompt_template(template: str) -> None:
    """
    更新提示词模板
    
    Args:
        template: 新的提示词模板
    """
    # 读取现有配置
    full_config = _load_yaml_config("tagging_config.yaml")
    
    # 更新提示词模板
    full_config["prompt_template"] = template
    
    # 保存
    _save_yaml_config("tagging_config.yaml", full_config)


def update_tagging_api_config(config: Dict[str, Any]) -> None:
    """
    更新标签生成 API 配置
    
    Args:
        config: 新的 API 配置
    """
    # 读取现有配置
    full_config = _load_yaml_config("tagging_config.yaml")
    
    # 更新 API 配置
    full_config["api"] = config
    
    # 保存
    _save_yaml_config("tagging_config.yaml", full_config)


# ==================== 兼容性：保持旧接口 ====================

# 为了向后兼容，提供全局变量（从 YAML 加载）
_ALLOWED_LABELS_CACHE = None
_SCENE_PRESETS_CACHE = None
_PROMPT_TEMPLATE_CACHE = None


def ALLOWED_LABELS() -> Dict[str, Set[str]]:
    """获取标签白名单（兼容旧代码）"""
    global _ALLOWED_LABELS_CACHE
    if _ALLOWED_LABELS_CACHE is None:
        _ALLOWED_LABELS_CACHE = get_allowed_labels()
    return _ALLOWED_LABELS_CACHE


def SCENE_PRESETS() -> Dict[str, Dict[str, List[str]]]:
    """获取场景预设（兼容旧代码）"""
    global _SCENE_PRESETS_CACHE
    if _SCENE_PRESETS_CACHE is None:
        _SCENE_PRESETS_CACHE = get_scene_presets()
    return _SCENE_PRESETS_CACHE


def PROMPT_TEMPLATE() -> str:
    """获取提示词模板（兼容旧代码）"""
    global _PROMPT_TEMPLATE_CACHE
    if _PROMPT_TEMPLATE_CACHE is None:
        _PROMPT_TEMPLATE_CACHE = get_prompt_template()
    return _PROMPT_TEMPLATE_CACHE
