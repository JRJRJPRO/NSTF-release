#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点分数分布分析脚本

分析节点级别检索的分数分布，为确定最优 threshold 提供依据。
"""

import os
import sys
import json
import random
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mmagent.utils.general import load_video_graph
from mmagent.retrieve import back_translate
from mmagent.utils.chat_api import parallel_get_embedding


def analyze_node_scores(
    video_graph,
    query: str,
    include_semantic: bool = False,
) -> dict:
    """
    分析单个查询的节点分数分布
    
    Returns:
        {
            'query': str,
            'num_nodes': int,
            'scores': List[float],
            'max_score': float,
            'mean_score': float,
            'percentiles': dict,
        }
    """
    # 1. 查询预处理
    queries = back_translate(video_graph, [query])
    if len(queries) > 100:
        queries = random.sample(queries, 100)
    
    # 2. 计算查询 embedding
    model = "text-embedding-3-large"
    query_embeddings = parallel_get_embedding(model, queries)[0]
    query_embeddings = np.array(query_embeddings)
    
    # 归一化
    norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    query_embeddings = query_embeddings / norms
    
    # 3. 遍历所有文本节点，计算相似度
    scores = []
    for node_id, node in video_graph.nodes.items():
        if not hasattr(node, 'embedding') or node.embedding is None:
            continue
        if node.type in ['img', 'voice']:
            continue
        if not include_semantic and node.type == 'semantic':
            continue
        
        node_embedding = np.array(node.embedding)
        if node_embedding.ndim == 1:
            node_embedding = node_embedding.reshape(1, -1)
        
        node_norms = np.linalg.norm(node_embedding, axis=1, keepdims=True)
        node_norms[node_norms == 0] = 1
        node_embedding = node_embedding / node_norms
        
        similarities = np.dot(query_embeddings, node_embedding.T)
        score = float(np.max(similarities))
        scores.append(score)
    
    scores = sorted(scores, reverse=True)
    
    return {
        'query': query,
        'num_nodes': len(scores),
        'scores': scores,
        'max_score': max(scores) if scores else 0,
        'mean_score': np.mean(scores) if scores else 0,
        'percentiles': {
            'p99': np.percentile(scores, 99) if scores else 0,
            'p95': np.percentile(scores, 95) if scores else 0,
            'p90': np.percentile(scores, 90) if scores else 0,
            'p75': np.percentile(scores, 75) if scores else 0,
            'p50': np.percentile(scores, 50) if scores else 0,
        }
    }


def run_analysis(
    dataset: str = 'robot',
    num_questions: int = 50,
    include_semantic: bool = False,
    output_file: str = None,
):
    """
    运行节点分数分布分析
    """
    # 加载数据
    data_dir = PROJECT_ROOT / 'data'
    annotations_file = data_dir / 'annotations' / f'{dataset}.json'
    
    with open(annotations_file, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # 收集所有问题
    all_questions = []
    for video_name, video_data in annotations.items():
        mem_path = video_data.get('mem_path')
        if not mem_path:
            mem_path = f'data/memory_graphs/{dataset}/{video_name}.pkl'
        if not os.path.isabs(mem_path):
            mem_path = str(PROJECT_ROOT / mem_path)
        
        for qa in video_data.get('qa_list', []):
            all_questions.append({
                'video': video_name,
                'question': qa['question'],
                'mem_path': mem_path,
            })
    
    # 随机采样
    if len(all_questions) > num_questions:
        questions = random.sample(all_questions, num_questions)
    else:
        questions = all_questions
    
    print(f"分析 {len(questions)} 个问题的节点分数分布...")
    print(f"include_semantic: {include_semantic}")
    print()
    
    # 分析
    all_scores = []
    all_max_scores = []
    graph_cache = {}
    
    for i, q in enumerate(questions):
        print(f"[{i+1}/{len(questions)}] {q['question'][:60]}...")
        
        # 加载图谱
        mem_path = q['mem_path']
        if mem_path not in graph_cache:
            graph_cache[mem_path] = load_video_graph(mem_path)
            graph_cache[mem_path].refresh_equivalences()
        video_graph = graph_cache[mem_path]
        
        # 分析
        result = analyze_node_scores(video_graph, q['question'], include_semantic)
        
        all_scores.extend(result['scores'])
        all_max_scores.append(result['max_score'])
        
        print(f"  max={result['max_score']:.4f}, mean={result['mean_score']:.4f}, nodes={result['num_nodes']}")
    
    # 汇总统计
    print("\n" + "=" * 60)
    print("汇总统计")
    print("=" * 60)
    
    print(f"\n所有节点分数分布 (n={len(all_scores)}):")
    for p in [99, 95, 90, 75, 50, 25, 10, 5, 1]:
        print(f"  P{p}: {np.percentile(all_scores, p):.4f}")
    
    print(f"\n每个查询的最高分分布 (n={len(all_max_scores)}):")
    for p in [99, 95, 90, 75, 50, 25, 10, 5, 1]:
        print(f"  P{p}: {np.percentile(all_max_scores, p):.4f}")
    
    # 建议 threshold
    print("\n" + "=" * 60)
    print("Threshold 建议")
    print("=" * 60)
    
    # 不同 threshold 下的效果
    thresholds = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    print("\n不同 threshold 下的效果:")
    print(f"{'Threshold':<12} {'平均返回节点数':<18} {'空结果比例':<15}")
    print("-" * 45)
    
    for th in thresholds:
        counts = []
        empty = 0
        
        # 模拟每个查询的结果
        idx = 0
        for q_result_scores in [result['scores'] for result in [
            analyze_node_scores(graph_cache[q['mem_path']], q['question'], include_semantic)
            for q in questions[:20]  # 只用前20个加速
        ]]:
            above_threshold = [s for s in q_result_scores if s >= th]
            counts.append(len(above_threshold))
            if len(above_threshold) == 0:
                empty += 1
        
        avg_count = np.mean(counts)
        empty_ratio = empty / len(counts)
        print(f"{th:<12.2f} {avg_count:<18.1f} {empty_ratio*100:<15.1f}%")
    
    # 保存结果
    if output_file:
        output = {
            'dataset': dataset,
            'num_questions': len(questions),
            'include_semantic': include_semantic,
            'all_scores_percentiles': {
                f'p{p}': float(np.percentile(all_scores, p))
                for p in [99, 95, 90, 75, 50, 25, 10, 5, 1]
            },
            'max_scores_percentiles': {
                f'p{p}': float(np.percentile(all_max_scores, p))
                for p in [99, 95, 90, 75, 50, 25, 10, 5, 1]
            },
            'recommended_threshold': float(np.percentile(all_max_scores, 10)),
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='节点分数分布分析')
    parser.add_argument('--dataset', type=str, default='robot', help='数据集名称')
    parser.add_argument('--num-questions', type=int, default=50, help='分析问题数量')
    parser.add_argument('--include-semantic', action='store_true', help='是否包含 semantic 节点')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径')
    
    args = parser.parse_args()
    
    run_analysis(
        dataset=args.dataset,
        num_questions=args.num_questions,
        include_semantic=args.include_semantic,
        output_file=args.output,
    )


if __name__ == '__main__':
    main()
