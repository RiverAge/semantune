#!/usr/bin/env python3
"""输出当前LLM使用的完整Prompt"""

import yaml

with open('config/tagging_config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

prompt = config['prompt_template']

# 生成一个示例
example_prompt = prompt.format(
    title='七里香',
    artist='周杰伦',
    album='七里香',
    lyrics='N/A'
)

print("=" * 80)
print("当前LLM使用的完整Prompt")
print("=" * 80)
print()
print(example_prompt)
print()
print("=" * 80)
