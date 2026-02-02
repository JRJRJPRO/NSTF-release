# -*- coding: utf-8 -*-
"""
分析"实体感知检索"的可行性

问题：当搜索词涉及特定 character 时，是否应该返回更多该 character 的信息？
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from env_setup import setup_all
setup_all()

from mmagent.retrieve import search, retrieve_from_videograph, back_translate
from mmagent.utils.general import load_video_graph
from mmagent.memory_processing import parse_video_caption

# 加载一个图谱
graph_path = project_root / "data" / "memory_graphs" / "robot" / "kitchen_03.pkl"
g = load_video_graph(str(graph_path))
g.refresh_equivalences()

print(f"图谱: {graph_path.name}")
print(f"人物映射: {len(g.character_mappings)} 个角色")

# === 分析1: 当前 topk=2 返回多少信息 ===
print(f"\n{'='*70}")
print("【分析1: 当前 topk=2 返回的信息量】")
print(f"{'='*70}")

test_query = "What did the person do in the kitchen?"
memories, _, _ = search(g, test_query, [], threshold=0.3, topk=2)

total_items = sum(len(v) for v in memories.values())
print(f"\n查询: '{test_query}'")
print(f"返回: {len(memories)} 个 clip, 共 {total_items} 条信息")
for clip, contents in memories.items():
    print(f"  {clip}: {len(contents)} 条")

# === 分析2: 如果搜索涉及特定人物会怎样 ===
print(f"\n{'='*70}")
print("【分析2: 人物相关搜索的实体识别】")
print(f"{'='*70}")

# 模拟 LLM 搜索 "Where is character_0"
test_queries = [
    "Where is <character_0>?",
    "What did <character_0> do?",
    "character_0 location",
]

for query in test_queries:
    print(f"\n查询: '{query}'")
    
    # 1. 解析查询中的实体
    entities = parse_video_caption(g, query)
    print(f"  识别到的实体: {entities}")
    
    # 2. back_translate 会把 character → face/voice
    translated = back_translate(g, [query])
    print(f"  back_translate 后: {len(translated)} 个变体")
    if len(translated) <= 3:
        for t in translated:
            print(f"    - {t}")
    else:
        print(f"    - {translated[0]}")
        print(f"    - ... 还有 {len(translated)-1} 个")

# === 分析3: character_0 出现在多少 clip 中 ===
print(f"\n{'='*70}")
print("【分析3: 各角色出现的 clip 数量】")
print(f"{'='*70}")

# 统计每个 character 出现在多少个 clip
char_to_clips = defaultdict(set)

for node_id, node in g.nodes.items():
    if node.type not in ['episodic', 'semantic']:
        continue
    
    content = node.metadata.get('contents', [''])[0]
    clip_id = node.metadata.get('timestamp', -1)
    
    # 找出内容中提到的所有实体
    for tag, char in g.reverse_character_mappings.items():
        if tag in content or f"<{tag}>" in content:
            char_to_clips[char].add(clip_id)

print(f"\n各角色出现的 clip 数:")
for char, clips in sorted(char_to_clips.items(), key=lambda x: -len(x[1]))[:5]:
    print(f"  {char}: {len(clips)} 个 clip")

# 看 character_0 的详细分布
if 'character_0' in char_to_clips:
    char0_clips = sorted(char_to_clips['character_0'])
    print(f"\ncharacter_0 出现的 clip: {char0_clips[:10]}..." if len(char0_clips) > 10 else f"\ncharacter_0 出现的 clip: {char0_clips}")

# === 分析4: topk 增加会带来多少额外信息 ===
print(f"\n{'='*70}")
print("【分析4: 不同 topk 返回的信息量对比】")
print(f"{'='*70}")

test_query = "What is character_0 doing?"
print(f"\n查询: '{test_query}'")

for topk in [2, 5, 10, 20]:
    memories, _, _ = search(g, test_query, [], threshold=0.3, topk=topk)
    total_items = sum(len(v) for v in memories.values())
    print(f"  topk={topk:2d}: {len(memories):2d} clips, {total_items:3d} 条信息")

# === 分析5: 实体感知检索的可行方案 ===
print(f"\n{'='*70}")
print("【分析5: 实体感知检索方案思考】")
print(f"{'='*70}")

print("""
当前检索流程:
  查询 → embedding相似度 → topk clips → 返回这些clip的所有内容

问题: 
  1. topk=2 可能漏掉重要信息
  2. 即使 clip 中有 character_0 的信息，也可能因为分数不够高被过滤

可能的改进方案:

方案A: 增大 topk (简单但粗暴)
  - 把 topk 从 2 改成 5 或 10
  - 优点: 实现简单
  - 缺点: 可能引入更多噪声，LLM上下文变长

方案B: 实体感知检索 (更精准)
  - 如果查询中包含明确实体 (如 character_0)
  - 额外返回该实体出现的所有 clip 摘要
  - 类似: "character_0 appears in: CLIP_2, CLIP_5, CLIP_12..."
  
方案C: 两阶段检索
  1. 先用 embedding 找 top clips (现有逻辑)
  2. 从这些 clips 中提取涉及的实体
  3. 补充返回这些实体的其他关键信息

方案D: 调整返回格式
  - 不只返回 clip 内容，还返回结构化摘要
  - 如: "涉及人物: character_0, character_1"
       "主要事件: cooking, cleaning"
""")

# === 具体对比: topk=2 vs topk=5 ===
print(f"\n{'='*70}")
print("【具体对比: 一个真实问题用 topk=2 vs topk=5】")
print(f"{'='*70}")

query = "What vegetables did the person buy?"
print(f"\n问题: '{query}'")

for topk in [2, 5]:
    print(f"\n--- topk={topk} ---")
    memories, _, scores = search(g, query, [], threshold=0.3, topk=topk)
    
    for clip, contents in memories.items():
        # 只显示前3条
        print(f"\n{clip} ({len(contents)} 条):")
        for c in contents[:3]:
            print(f"  - {c[:70]}...")
        if len(contents) > 3:
            print(f"  ... 还有 {len(contents)-3} 条")
