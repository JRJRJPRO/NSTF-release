#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试脚本：检查检索分数分布

用法:
  cd /data1/rongjiej/NSTF_MODEL
  python scripts/debug/check_retrieval_scores.py
"""

import os
import sys
from pathlib import Path

# 设置路径
NSTF_MODEL_DIR = Path(__file__).parent.parent.parent.resolve()
os.chdir(NSTF_MODEL_DIR)
sys.path.insert(0, str(NSTF_MODEL_DIR))

from env_setup import setup_all
setup_all()

from mmagent.retrieve import retrieve_from_videograph
from mmagent.utils.general import load_video_graph


def check_scores(mem_path: str, queries: list, threshold: float = 0.3, before_clip: int = None):
    """检查给定查询的检索分数"""
    print(f"加载图谱: {mem_path}")
    mem_node = load_video_graph(mem_path)
    mem_node.refresh_equivalences()
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"Threshold: {threshold}, before_clip: {before_clip}")
        
        top_clips, clip_scores, nodes = retrieve_from_videograph(
            mem_node, query, topk=10, mode='max', threshold=0, before_clip=before_clip
        )
        
        if not clip_scores:
            print("❌ 没有任何分数返回！")
            continue
        
        # 打印所有分数
        sorted_scores = sorted(clip_scores.items(), key=lambda x: x[1], reverse=True)
        print(f"\n所有 Clip 分数 (共 {len(sorted_scores)} 个):")
        for clip_id, score in sorted_scores[:10]:
            # 检查是否同时满足 threshold 和 before_clip 条件
            pass_threshold = score >= threshold
            pass_before = (before_clip is None) or (clip_id <= before_clip)
            status = "✓" if (pass_threshold and pass_before) else "✗"
            extra = ""
            if not pass_before:
                extra = f" (clip_id > before_clip={before_clip})"
            print(f"  {status} CLIP_{clip_id}: {score:.4f}{extra}")
        
        # 统计 - 同时满足两个条件
        if before_clip is not None:
            above_threshold = sum(1 for clip_id, score in sorted_scores 
                                  if score >= threshold and clip_id <= before_clip)
            print(f"\n统计: {above_threshold}/{len(sorted_scores)} 个 clip 同时满足 score >= {threshold} 且 clip_id <= {before_clip}")
        else:
            above_threshold = sum(1 for _, score in sorted_scores if score >= threshold)
            print(f"\n统计: {above_threshold}/{len(sorted_scores)} 个 clip 分数 >= {threshold}")
        
        if sorted_scores:
            max_score = sorted_scores[0][1]
            print(f"最高分: {max_score:.4f}")


if __name__ == '__main__':
    # 测试 living_room_06
    mem_path = "data/memory_graphs/robot/living_room_06.pkl"
    
    # Q01 的查询 (before_clip=0)
    q01_queries = [
        "Drinks ordered by the three people in the scenario.",
        "What drinks did each of the three people choose?",
    ]
    
    # Q04 的查询 (before_clip=31)
    q04_queries = [
        "What fruits does Lily like to eat?",
        "What is the character id of Lily?",
        "What fruits does <character_0> like to eat?",
    ]
    
    print("="*60)
    print("Q01: before_clip=0 (只能访问 CLIP_0)")
    print("="*60)
    check_scores(mem_path, q01_queries, threshold=0.3, before_clip=0)
    
    print("\n\n")
    print("="*60)
    print("Q04: before_clip=31 (可以访问 CLIP_0 到 CLIP_31)")
    print("="*60)
    check_scores(mem_path, q04_queries, threshold=0.3, before_clip=31)
    
    print("\n\n")
    print("="*60)
    print("对比：无 before_clip 限制")
    print("="*60)
    check_scores(mem_path, q01_queries + q04_queries, threshold=0.3, before_clip=None)
