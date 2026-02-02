#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点检索参数调优脚本

使用实际问答数据模拟 LLM 搜索，分析不同 threshold 和 topk 下的效果。
目标：找到既能保证有结果，又能保证结果质量的参数组合。
"""

import os
import sys
import json
import random
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Any

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mmagent.utils.general import load_video_graph
from mmagent.retrieve import back_translate
from mmagent.utils.chat_api import parallel_get_embedding


def compute_node_scores(video_graph, query: str, include_semantic: bool = False) -> List[Tuple[int, float, int, str]]:
    """
    计算查询与所有节点的相似度分数
    
    Returns:
        List of (node_id, score, clip_id, content)
    """
    # 查询预处理
    queries = back_translate(video_graph, [query])
    if len(queries) > 100:
        queries = random.sample(queries, 100)
    
    # 计算查询 embedding
    model = "text-embedding-3-large"
    query_embeddings = parallel_get_embedding(model, queries)[0]
    query_embeddings = np.array(query_embeddings)
    
    # 归一化
    norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1
    query_embeddings = query_embeddings / norms
    
    # 遍历所有文本节点
    results = []
    for node_id, node in video_graph.nodes.items():
        if node.type in ['img', 'voice']:
            continue
        if not include_semantic and node.type == 'semantic':
            continue
        
        node_emb = getattr(node, 'embeddings', None)
        if node_emb is None:
            continue
        
        # 处理 embedding 格式
        try:
            if isinstance(node_emb, list):
                if len(node_emb) == 0:
                    continue
                if isinstance(node_emb[0], list):
                    vec = np.array(node_emb[0], dtype=float)
                elif isinstance(node_emb[0], (int, float)):
                    vec = np.array(node_emb, dtype=float)
                else:
                    continue
            else:
                vec = np.array(node_emb, dtype=float).flatten()
            
            if vec.size < 64:
                continue
            
            query_dim = query_embeddings.shape[1]
            if vec.size > query_dim:
                vec = vec[:query_dim]
            elif vec.size < query_dim:
                vec = np.pad(vec, (0, query_dim - vec.size))
            
            node_embedding = vec.reshape(1, -1)
            node_norm = np.linalg.norm(node_embedding)
            if node_norm == 0:
                continue
            node_embedding = node_embedding / node_norm
            
            similarities = np.dot(query_embeddings, node_embedding.T)
            score = float(np.max(similarities))
            
            clip_id = node.metadata.get('timestamp', -1)
            content = node.metadata.get('contents', [''])[0]
            
            results.append((node_id, score, clip_id, content))
        except Exception:
            continue
    
    # 按分数排序
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def simulate_search(
    video_graph,
    query: str,
    gt_answer: str,
    threshold: float,
    topk: int,
    include_semantic: bool = False,
) -> Dict[str, Any]:
    """
    模拟一次搜索，评估结果质量
    
    Returns:
        {
            'query': str,
            'gt_answer': str,
            'num_results': int,
            'is_empty': bool,
            'top_scores': List[float],
            'answer_mentioned': bool,  # GT 答案是否在返回内容中被提及
            'clips_covered': List[int],
        }
    """
    from mmagent.retrieve import translate
    
    all_nodes = compute_node_scores(video_graph, query, include_semantic)
    
    # 过滤
    filtered = [(nid, score, clip, content) for nid, score, clip, content in all_nodes if score >= threshold]
    selected = filtered[:topk]
    
    # 检查答案是否被提及
    answer_mentioned = False
    gt_lower = gt_answer.lower()
    
    # 翻译并检查
    contents_translated = []
    for nid, score, clip, content in selected:
        translated = translate(video_graph, [content])[0]
        contents_translated.append(translated)
        if gt_lower in translated.lower() or any(word in translated.lower() for word in gt_lower.split()[:3]):
            answer_mentioned = True
    
    return {
        'query': query,
        'gt_answer': gt_answer,
        'num_results': len(selected),
        'is_empty': len(selected) == 0,
        'top_scores': [s[1] for s in selected[:5]],
        'answer_mentioned': answer_mentioned,
        'clips_covered': list(set(s[2] for s in selected)),
        'contents': contents_translated[:3],  # 只保留前3个用于调试
    }


def analyze_parameters(
    dataset: str = 'robot',
    num_samples: int = 30,
    thresholds: List[float] = None,
    topks: List[int] = None,
):
    """
    分析不同参数组合的效果
    """
    if thresholds is None:
        thresholds = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
    if topks is None:
        topks = [5, 10, 15, 20, 30]
    
    # 加载数据
    data_dir = PROJECT_ROOT / 'data'
    annotations_file = data_dir / 'annotations' / f'{dataset}.json'
    
    with open(annotations_file, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # 收集问题
    all_questions = []
    for video_name, video_data in annotations.items():
        mem_path = video_data.get('mem_path')
        if not mem_path:
            mem_path = f'data/memory_graphs/{dataset}/{video_name}.pkl'
        if not os.path.isabs(mem_path):
            mem_path = str(PROJECT_ROOT / mem_path)
        
        if not os.path.exists(mem_path):
            continue
        
        for qa in video_data.get('qa_list', []):
            all_questions.append({
                'video': video_name,
                'question': qa['question'],
                'answer': qa['answer'],
                'mem_path': mem_path,
            })
    
    # 采样
    if len(all_questions) > num_samples:
        questions = random.sample(all_questions, num_samples)
    else:
        questions = all_questions
    
    print(f"分析 {len(questions)} 个问题的检索效果...")
    print(f"参数范围: threshold={thresholds}, topk={topks}")
    print()
    
    # 缓存图谱
    graph_cache = {}
    
    # 计算所有问题的节点分数
    question_scores = []
    for i, q in enumerate(questions):
        print(f"[{i+1}/{len(questions)}] 计算分数: {q['question'][:50]}...")
        
        mem_path = q['mem_path']
        if mem_path not in graph_cache:
            graph_cache[mem_path] = load_video_graph(mem_path)
            graph_cache[mem_path].refresh_equivalences()
        
        scores = compute_node_scores(graph_cache[mem_path], q['question'])
        question_scores.append({
            'question': q,
            'scores': scores,
            'graph': graph_cache[mem_path],
        })
    
    print("\n" + "=" * 80)
    print("参数组合分析")
    print("=" * 80)
    
    # 分析每个参数组合
    results = []
    for threshold in thresholds:
        for topk in topks:
            empty_count = 0
            answer_found = 0
            avg_results = []
            avg_top_score = []
            
            for qs in question_scores:
                # 模拟搜索
                all_nodes = qs['scores']
                filtered = [(nid, score, clip, content) for nid, score, clip, content in all_nodes if score >= threshold]
                selected = filtered[:topk]
                
                num_results = len(selected)
                avg_results.append(num_results)
                
                if num_results == 0:
                    empty_count += 1
                else:
                    avg_top_score.append(selected[0][1])
                    
                    # 检查答案是否在结果中
                    from mmagent.retrieve import translate
                    gt_lower = qs['question']['answer'].lower()
                    for nid, score, clip, content in selected:
                        translated = translate(qs['graph'], [content])[0].lower()
                        # 简单检查：答案的关键词是否出现
                        keywords = [w for w in gt_lower.split() if len(w) > 3][:3]
                        if any(kw in translated for kw in keywords):
                            answer_found += 1
                            break
            
            result = {
                'threshold': threshold,
                'topk': topk,
                'empty_rate': empty_count / len(question_scores),
                'avg_results': np.mean(avg_results),
                'avg_top_score': np.mean(avg_top_score) if avg_top_score else 0,
                'answer_hit_rate': answer_found / len(question_scores),
            }
            results.append(result)
    
    # 打印结果表格
    print(f"\n{'Threshold':<12} {'TopK':<8} {'空结果率':<12} {'平均返回数':<12} {'平均最高分':<12} {'答案命中率':<12}")
    print("-" * 68)
    
    for r in results:
        print(f"{r['threshold']:<12.2f} {r['topk']:<8} {r['empty_rate']*100:<12.1f}% {r['avg_results']:<12.1f} {r['avg_top_score']:<12.3f} {r['answer_hit_rate']*100:<12.1f}%")
    
    # 推荐参数
    print("\n" + "=" * 80)
    print("参数推荐")
    print("=" * 80)
    
    # 筛选条件：空结果率 < 5%，答案命中率最高
    good_params = [r for r in results if r['empty_rate'] < 0.05]
    if good_params:
        best = max(good_params, key=lambda x: (x['answer_hit_rate'], -x['avg_results']))
        print(f"\n推荐参数 (空结果率<5%, 答案命中率最高):")
        print(f"  threshold = {best['threshold']}")
        print(f"  topk = {best['topk']}")
        print(f"  空结果率: {best['empty_rate']*100:.1f}%")
        print(f"  答案命中率: {best['answer_hit_rate']*100:.1f}%")
        print(f"  平均返回数: {best['avg_results']:.1f}")
    else:
        print("没有找到空结果率<5%的参数组合，建议降低 threshold")
    
    # 返回所有结果供进一步分析
    return results, question_scores


def detailed_examples(question_scores, threshold: float, topk: int, num_examples: int = 5):
    """展示详细示例"""
    from mmagent.retrieve import translate
    
    print(f"\n" + "=" * 80)
    print(f"详细示例 (threshold={threshold}, topk={topk})")
    print("=" * 80)
    
    samples = random.sample(question_scores, min(num_examples, len(question_scores)))
    
    for i, qs in enumerate(samples):
        q = qs['question']
        all_nodes = qs['scores']
        filtered = [(nid, score, clip, content) for nid, score, clip, content in all_nodes if score >= threshold]
        selected = filtered[:topk]
        
        print(f"\n[示例 {i+1}]")
        print(f"问题: {q['question']}")
        print(f"答案: {q['answer']}")
        print(f"返回 {len(selected)} 个节点:")
        
        for j, (nid, score, clip, content) in enumerate(selected[:5]):
            translated = translate(qs['graph'], [content])[0]
            print(f"  {j+1}. [CLIP_{clip}] score={score:.3f}")
            print(f"     {translated[:100]}...")
        
        if len(selected) == 0:
            print("  (空结果)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='节点检索参数调优')
    parser.add_argument('--dataset', type=str, default='robot', help='数据集')
    parser.add_argument('--num-samples', type=int, default=30, help='采样问题数')
    parser.add_argument('--show-examples', action='store_true', help='显示详细示例')
    
    args = parser.parse_args()
    
    results, question_scores = analyze_parameters(
        dataset=args.dataset,
        num_samples=args.num_samples,
    )
    
    if args.show_examples:
        # 使用推荐参数展示示例
        good_params = [r for r in results if r['empty_rate'] < 0.05]
        if good_params:
            best = max(good_params, key=lambda x: x['answer_hit_rate'])
            detailed_examples(question_scores, best['threshold'], best['topk'])


if __name__ == '__main__':
    main()
