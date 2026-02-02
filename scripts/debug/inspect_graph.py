# -*- coding: utf-8 -*-
"""
图谱结构深度检查 + 模拟问答大模型视角
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from env_setup import setup_all
setup_all()

from mmagent.retrieve import search, retrieve_from_videograph, translate, back_translate
from mmagent.utils.general import load_video_graph

# 检查两个图谱
graphs_to_check = [
    "data/memory_graphs/robot/kitchen_03.pkl",
    "data/memory_graphs/robot/living_room_01.pkl",
]

for graph_path in graphs_to_check:
    full_path = project_root / graph_path
    if not full_path.exists():
        print(f"⚠️ 图谱不存在: {graph_path}")
        continue
    
    print(f"\n{'='*70}")
    print(f"图谱: {graph_path}")
    print(f"{'='*70}")
    
    g = load_video_graph(str(full_path))
    g.refresh_equivalences()
    
    # === 1. 人物映射检查 ===
    print(f"\n【1. 人物映射 (character_mappings)】")
    print(f"总共有 {len(g.character_mappings)} 个角色")
    for char_id, tags in list(g.character_mappings.items())[:5]:
        print(f"  {char_id}: {tags}")
    if len(g.character_mappings) > 5:
        print(f"  ... 还有 {len(g.character_mappings) - 5} 个角色")
    
    # 统计 face 和 voice 数量
    face_count = sum(1 for tags in g.character_mappings.values() for t in tags if t.startswith('face_'))
    voice_count = sum(1 for tags in g.character_mappings.values() for t in tags if t.startswith('voice_'))
    print(f"\n  统计: {face_count} 个 face 节点, {voice_count} 个 voice 节点")
    
    # === 2. 节点类型统计 ===
    print(f"\n【2. 节点类型统计】")
    type_counts = defaultdict(int)
    for node in g.nodes.values():
        type_counts[node.type] += 1
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")
    
    # === 3. 查看一些节点内容示例 ===
    print(f"\n【3. 节点内容示例】")
    
    # 找几个 episodic 节点
    episodic_samples = []
    for node_id, node in g.nodes.items():
        if node.type == 'episodic' and len(episodic_samples) < 3:
            content = node.metadata.get('contents', ['N/A'])[0]
            clip_id = node.metadata.get('timestamp', '?')
            episodic_samples.append((clip_id, content))
    
    print(f"\n  Episodic 节点 (原始内容):")
    for clip_id, content in episodic_samples:
        print(f"    CLIP_{clip_id}: {content[:80]}...")
    
    # 找包含 equivalence 的 semantic 节点
    print(f"\n  Equivalence 节点 (人物等价关系):")
    eq_count = 0
    for node_id, node in g.nodes.items():
        if node.type == 'semantic':
            content = node.metadata.get('contents', [''])[0]
            if 'equivalence' in content.lower() and eq_count < 3:
                print(f"    {content[:100]}")
                eq_count += 1
    if eq_count == 0:
        print(f"    (未找到 equivalence 节点)")
    
    # === 4. 模拟问答大模型视角 ===
    print(f"\n【4. 模拟问答大模型视角】")
    test_query = "What is the person doing in the kitchen?"
    
    print(f"\n  用户问题: '{test_query}'")
    print(f"\n  Step 1: back_translate (人名 → face/voice)")
    translated = back_translate(g, [test_query])
    print(f"    输入: {test_query}")
    print(f"    输出: {translated[:3]}..." if len(translated) > 3 else f"    输出: {translated}")
    
    print(f"\n  Step 2: 检索并看分数")
    top_clips, clip_scores, nodes = retrieve_from_videograph(
        g, test_query, topk=10, threshold=0, before_clip=None
    )
    sorted_scores = sorted(clip_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"    Top-5 clips 分数:")
    for clip_id, score in sorted_scores:
        print(f"      CLIP_{clip_id}: {score:.4f}")
    
    print(f"\n  Step 3: search() 返回结果 (threshold=0, topk=2)")
    memories, _, _ = search(g, test_query, [], threshold=0, topk=2, before_clip=None)
    print(f"    返回给大模型的内容:")
    for clip_name, contents in memories.items():
        print(f"\n    {clip_name}:")
        for c in contents[:3]:
            print(f"      - {c[:70]}...")
        if len(contents) > 3:
            print(f"      ... 还有 {len(contents)-3} 条")

print(f"\n\n{'='*70}")
print("【5. 阈值分析 - 寻找最佳阈值】")
print(f"{'='*70}")

# 用第一个图谱做阈值分析
g = load_video_graph(str(project_root / graphs_to_check[0]))
g.refresh_equivalences()

test_queries = [
    "Where should the spinach be placed?",
    "What are wiped by the dishcloth?",
    "What did the person do after opening the fridge?",
    "Who is cooking in the kitchen?",
    "What vegetables were bought?",
]

print(f"\n对 {len(test_queries)} 个查询测试不同阈值:\n")

# 收集所有查询的分数
all_max_scores = []
all_clip_scores = []

for query in test_queries:
    _, clip_scores, _ = retrieve_from_videograph(g, query, topk=100, threshold=0)
    if clip_scores:
        max_score = max(clip_scores.values())
        all_max_scores.append(max_score)
        all_clip_scores.extend(clip_scores.values())
        print(f"  '{query[:40]}...'")
        print(f"    最高分: {max_score:.4f}, 平均分: {sum(clip_scores.values())/len(clip_scores):.4f}")

print(f"\n汇总统计:")
print(f"  所有查询最高分范围: {min(all_max_scores):.4f} ~ {max(all_max_scores):.4f}")
print(f"  所有查询最高分平均: {sum(all_max_scores)/len(all_max_scores):.4f}")

print(f"\n不同阈值下的命中率 (有多少查询能返回至少1个结果):")
for th in [0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5]:
    hit_count = sum(1 for score in all_max_scores if score >= th)
    print(f"  threshold={th:.2f}: {hit_count}/{len(test_queries)} 查询有结果 ({hit_count/len(test_queries)*100:.0f}%)")

print(f"\n建议阈值分析:")
# 找一个让 80%+ 查询有结果的阈值
for th in [0.45, 0.4, 0.35, 0.3, 0.25, 0.2]:
    hit_rate = sum(1 for score in all_max_scores if score >= th) / len(all_max_scores)
    if hit_rate >= 0.8:
        print(f"  ✓ threshold={th} 可以让 {hit_rate*100:.0f}% 的查询有结果")
        break
