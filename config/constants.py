"""
常量定义 - 标签白名单、魔法数字等
"""

# 标签白名单
ALLOWED_LABELS = {
    "mood": {"Energetic", "Epic", "Emotional", "Sad", "Chill", "Dark", "Happy", "Peaceful", "Romantic", "Dreamy", "Upbeat", "Groovy"},
    "energy": {"Low", "Medium", "High"},
    "scene": {"Workout", "Study", "Night", "Driving", "Gaming", "Sleep", "Morning", "None"},
    "region": {"Chinese", "Western", "Japanese", "Korean"},
    "subculture": {"None", "Anime", "Game", "Vocaloid", "Idol"},
    "genre": {"Pop", "Indie", "Rock", "Electronic", "Hip-Hop", "Classical", "Folk", "J-Rock", "Metal"}
}

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
    # annotation 表索引
    "CREATE INDEX IF NOT EXISTS idx_annotation_user_id ON annotation(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_annotation_item_id ON annotation(item_id)",
    "CREATE INDEX IF NOT EXISTS idx_annotation_user_item ON annotation(user_id, item_id)",
]

# 缓存配置
CACHE_CONFIG = {
    "user_profile_ttl": 300,  # 5分钟
    "distribution_ttl": 600,  # 10分钟
    "quality_stats_ttl": 600,  # 10分钟
    "enabled": True,
}

# 场景预设定义
SCENE_PRESETS = {
    "深夜": {"mood": ["Peaceful", "Sad", "Dreamy", "Chill"], "energy": ["Low"]},
    "运动": {"mood": ["Energetic", "Epic"], "energy": ["High"]},
    "学习": {"mood": ["Peaceful", "Chill"], "energy": ["Low", "Medium"]},
    "开车": {"mood": ["Energetic", "Upbeat", "Groovy"], "energy": ["Medium", "High"]},
    "放松": {"mood": ["Peaceful", "Dreamy", "Chill"], "energy": ["Low"]},
    "派对": {"mood": ["Happy", "Energetic", "Upbeat"], "energy": ["High"]},
    "伤心": {"mood": ["Sad", "Emotional"], "energy": ["Low", "Medium"]},
    "励志": {"mood": ["Epic", "Energetic"], "energy": ["High"]},
}

# 生成标签列表字符串（从 ALLOWED_LABELS 动态生成）
_LABELS_TEXT = ""
for key, values in ALLOWED_LABELS.items():
    sorted_values = sorted(values)
    _LABELS_TEXT += f"- {key}: {', '.join(sorted_values)}\n"

# LLM 提示词模板（从 ALLOWED_LABELS 动态生成）
PROMPT_TEMPLATE = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a robotic music classification engine. You MUST output ONLY valid JSON.
You MUST choose labels ONLY from the provided lists. DO NOT create new labels.

ALLOWED LABELS:
""" + _LABELS_TEXT + """Rules:
1. 'Groovy' is a Mood, NOT an Energy level. Energy must be Low, Medium, or High.
2. 'genre' must be a single word from the list. (e.g., Use 'Pop' for Pop/R&B).
3. 'scene' must be exactly from the list. Use 'None' if unsure.
4. No conversational filler. Just the JSON object.

Example Output:
{{
  "mood": "Epic",
  "energy": "High",
  "scene": "None",
  "region": "Chinese",
  "subculture": "None",
  "genre": "Rock",
  "confidence": 0.95
}}
<|eot_id|><|start_header_id|>user<|end_header_id|>
Classify:
Title: {title}
Artist: {artist}
Album: {album}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
