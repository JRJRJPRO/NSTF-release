#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试：检查节点结构和 embedding 格式
"""

import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mmagent.utils.general import load_video_graph

# 找一个图谱文件
data_dir = PROJECT_ROOT / 'data' / 'memory_graphs' / 'robot'
pkl_files = list(data_dir.glob('*.pkl'))
mem_path = str(pkl_files[0])

print(f"加载图谱: {pkl_files[0].name}")
graph = load_video_graph(mem_path)
graph.refresh_equivalences()

print(f"\n节点总数: {len(graph.nodes)}")

# 统计节点类型
type_counts = {}
has_embedding = 0
no_embedding = 0
embedding_shapes = set()

for node_id, node in graph.nodes.items():
    t = node.type
    type_counts[t] = type_counts.get(t, 0) + 1
    
    if hasattr(node, 'embedding') and node.embedding is not None:
        has_embedding += 1
        import numpy as np
        emb = np.array(node.embedding)
        embedding_shapes.add(emb.shape)
    else:
        no_embedding += 1

print(f"\n节点类型分布:")
for t, c in sorted(type_counts.items()):
    print(f"  {t}: {c}")

print(f"\n有 embedding 的节点: {has_embedding}")
print(f"没有 embedding 的节点: {no_embedding}")
print(f"embedding 形状: {embedding_shapes}")

# 看一个具体的文本节点
print("\n" + "=" * 60)
print("示例节点:")
for node_id, node in list(graph.nodes.items())[:20]:
    if node.type == 'episodic':
        print(f"\nNode ID: {node_id}")
        print(f"  Type: {node.type}")
        print(f"  Has embedding: {hasattr(node, 'embedding') and node.embedding is not None}")
        if hasattr(node, 'embedding') and node.embedding is not None:
            import numpy as np
            emb = np.array(node.embedding)
            print(f"  Embedding shape: {emb.shape}")
            print(f"  Embedding norm: {np.linalg.norm(emb):.4f}")
        print(f"  Metadata keys: {list(node.metadata.keys())}")
        if 'contents' in node.metadata:
            print(f"  Contents: {node.metadata['contents'][:2]}")
        if 'timestamp' in node.metadata:
            print(f"  Timestamp: {node.metadata['timestamp']}")
        break

# 检查 text_nodes_by_clip
print("\n" + "=" * 60)
print("text_nodes_by_clip:")
if hasattr(graph, 'text_nodes_by_clip'):
    print(f"  clip 数量: {len(graph.text_nodes_by_clip)}")
    for clip_id in list(graph.text_nodes_by_clip.keys())[:3]:
        node_ids = graph.text_nodes_by_clip[clip_id]
        print(f"  CLIP_{clip_id}: {len(node_ids)} 个节点")
else:
    print("  没有 text_nodes_by_clip 属性")
