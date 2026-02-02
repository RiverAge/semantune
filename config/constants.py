"""
常量定义 - 标签白名单等
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
<|控制台_id|><|start_header_id|>assistant<|end_header_id|>
"""
