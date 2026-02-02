# -*- coding: utf-8 -*-
"""
检索系统调试工具集

用法:
    python scripts/debug/retrieval_debug.py --mode scores
    python scripts/debug/retrieval_debug.py --mode accuracy --results experiments/efficiency/results/baseline_results.jsonl
    python scripts/debug/retrieval_debug.py --mode search --query "What are wiped by the dishcloth?"

可用模式:
    scores   - 分析检索分数分布，测试不同阈值的效果
    accuracy - 分析结果文件的准确率和空搜索情况
    search   - 测试单个查询的检索结果
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 设置环境
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from env_setup import setup_all
setup_all()

from mmagent.retrieve import search, retrieve_from_videograph
from mmagent.utils.general import load_video_graph


def analyze_scores(mem_path: str, query: str):
    """分析检索分数分布"""
    print(f"=== 检索分数分析 ===")
    print(f"图谱: {mem_path}")
    print(f"查询: '{query}'")
    
    mem_node = load_video_graph(mem_path)
    mem_node.refresh_equivalences()
    
    print(f"\n图谱信息:")
    print(f"  nodes数量: {len(mem_node.nodes)}")
    print(f"  clips数量: {len(mem_node.text_nodes_by_clip)}")
    
    # 底层检索
    top_clips, clip_scores, nodes = retrieve_from_videograph(
        mem_node, query, topk=100, threshold=0, before_clip=None
    )
    
    sorted_scores = sorted(clip_scores.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n分数分布 (前15):")
    for clip_id, score in sorted_scores[:15]:
        marker = "✓" if score >= 0.5 else "✗"
        print(f"  {marker} CLIP_{clip_id}: {score:.4f}")
    
    print(f"\n阈值过滤统计:")
    for th in [0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        count = sum(1 for s in clip_scores.values() if s >= th)
        pct = count / len(clip_scores) * 100 if clip_scores else 0
        print(f"  threshold={th}: {count:3d} clips ({pct:.1f}%)")


def analyze_accuracy(results_file: str):
    """分析结果文件的准确率"""
    print(f"=== 准确率分析 ===")
    print(f"结果文件: {results_file}")
    
    results = [json.loads(line) for line in open(results_file)]
    
    total = len(results)
    correct = sum(1 for r in results if r.get("gpt_eval"))
    
    # 统计空搜索
    empty_search_count = 0
    for r in results:
        for c in r.get('conversations', []):
            if c['role'] == 'user' and 'Searched knowledge: {}' in c['content']:
                empty_search_count += 1
                break
    
    # 轮次分布
    round_dist = {}
    for r in results:
        rounds = r.get('num_rounds', 0)
        round_dist[rounds] = round_dist.get(rounds, 0) + 1
    
    print(f"\n基本统计:")
    print(f"  总问题数: {total}")
    print(f"  正确数: {correct}")
    print(f"  准确率: {correct/total*100:.1f}%")
    print(f"  有空搜索结果: {empty_search_count} ({empty_search_count/total*100:.1f}%)")
    
    print(f"\n轮次分布:")
    for r in sorted(round_dist.keys()):
        print(f"  {r}轮: {round_dist[r]}题 ({round_dist[r]/total*100:.1f}%)")
    
    # 错误案例
    print(f"\n=== 前3个错误案例 ===")
    wrong_cases = [r for r in results if not r.get("gpt_eval")][:3]
    for i, case in enumerate(wrong_cases):
        print(f"\n--- 案例 {i+1} ---")
        print(f"问题: {case['question']}")
        print(f"标准答案: {case['answer']}")
        print(f"模型回答: {case.get('response', 'N/A')[:200]}")
        print(f"轮次: {case.get('num_rounds', 'N/A')}")


def test_search(mem_path: str, query: str, threshold: float = 0.5, topk: int = 2):
    """测试单个查询"""
    print(f"=== 搜索测试 ===")
    print(f"图谱: {mem_path}")
    print(f"查询: '{query}'")
    print(f"参数: threshold={threshold}, topk={topk}")
    
    mem_node = load_video_graph(mem_path)
    mem_node.refresh_equivalences()
    
    memories, clips, scores = search(
        mem_node, query, [],
        threshold=threshold,
        topk=topk,
        before_clip=None
    )
    
    print(f"\n结果: {len(memories)} 个 clip")
    for clip_name, contents in memories.items():
        print(f"\n{clip_name}:")
        for content in contents[:3]:
            print(f"  - {content[:100]}...")
        if len(contents) > 3:
            print(f"  ... 还有 {len(contents)-3} 条")


def main():
    parser = argparse.ArgumentParser(description="检索系统调试工具")
    parser.add_argument("--mode", choices=["scores", "accuracy", "search"], 
                       default="scores", help="调试模式")
    parser.add_argument("--mem-path", type=str, 
                       default="data/memory_graphs/robot/kitchen_03.pkl",
                       help="图谱文件路径")
    parser.add_argument("--query", type=str,
                       default="What are wiped by the dishcloth?",
                       help="测试查询")
    parser.add_argument("--results", type=str,
                       help="结果文件路径 (accuracy模式)")
    parser.add_argument("--threshold", type=float, default=0.5,
                       help="检索阈值 (search模式)")
    parser.add_argument("--topk", type=int, default=2,
                       help="返回数量 (search模式)")
    
    args = parser.parse_args()
    
    # 处理相对路径
    if not os.path.isabs(args.mem_path):
        args.mem_path = str(project_root / args.mem_path)
    
    if args.mode == "scores":
        analyze_scores(args.mem_path, args.query)
    elif args.mode == "accuracy":
        if not args.results:
            print("错误: accuracy 模式需要指定 --results 参数")
            sys.exit(1)
        if not os.path.isabs(args.results):
            args.results = str(project_root / args.results)
        analyze_accuracy(args.results)
    elif args.mode == "search":
        test_search(args.mem_path, args.query, args.threshold, args.topk)


if __name__ == "__main__":
    main()
