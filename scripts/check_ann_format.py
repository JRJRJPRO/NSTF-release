#!/usr/bin/env python3
"""检查 annotations 格式"""

import json
from pathlib import Path

ann_path = Path("/data1/rongjiej/NSTF_MODEL/data/annotations/robot.json")

with open(ann_path, 'r') as f:
    data = json.load(f)

print(f"顶层类型: {type(data)}")
print(f"顶层 keys 数量: {len(data.keys())}")

# 检查第一个视频的格式
for video_name, questions in list(data.items())[:2]:
    print(f"\n视频: {video_name}")
    print(f"  questions 类型: {type(questions)}")
    if isinstance(questions, list):
        print(f"  questions 数量: {len(questions)}")
        if questions:
            print(f"  第一个问题类型: {type(questions[0])}")
            if isinstance(questions[0], dict):
                print(f"  第一个问题 keys: {questions[0].keys()}")
                print(f"  示例: {questions[0]}")
            elif isinstance(questions[0], str):
                print(f"  第一个问题: {questions[0][:100]}")
    elif isinstance(questions, dict):
        print(f"  questions keys: {list(questions.keys())[:5]}")

# 专门看 kitchen_03
print("\n" + "=" * 50)
print("kitchen_03 详情:")
k03 = data.get('kitchen_03', [])
print(f"类型: {type(k03)}")
print(f"内容: {k03[:2] if isinstance(k03, list) else list(k03.items())[:2]}")
