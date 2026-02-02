# -*- coding: utf-8 -*-
"""
Stage 1b: 测试 back_translate 对命中率的提升

back_translate 会将query中的指代词（如"the person"）替换为实际实体名
这可能帮助提升与Procedure goal的匹配度
"""

import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import random

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

# 环境设置
from env_setup import setup_all
setup_all()

from mmagent.utils.chat_api import parallel_get_embedding
from mmagent.retrieve import back_translate
from mmagent.utils.general import load_video_graph

# 数据路径
DATA_DIR = PROJECT_DIR / 'data'
NSTF_GRAPHS_DIR = DATA_DIR / 'nstf_graphs'
ANNOTATIONS_DIR = DATA_DIR / 'annotations'
MEMORY_GRAPHS_DIR = DATA_DIR / 'memory_graphs'


def load_nstf_graph(video_name: str, dataset: str) -> Optional[Dict]:
    nstf_path = NSTF_GRAPHS_DIR / dataset / f'{video_name}_nstf.pkl'
    if not nstf_path.exists():
        return None
    with open(nstf_path, 'rb') as f:
        return pickle.load(f)


def load_video_graph_safe(video_name: str, dataset: str):
    mem_path = MEMORY_GRAPHS_DIR / dataset / f'{video_name}.pkl'
    if not mem_path.exists():
        return None
    try:
        graph = load_video_graph(str(mem_path))
        graph.refresh_equivalences()
        return graph
    except:
        return None


def compute_max_similarity(
    query: str,
    proc_embeddings: Dict[str, np.ndarray],
    model: str = "text-embedding-3-large"
) -> float:
    """计算query与所有procedure的最高相似度"""
    query_embs, _ = parallel_get_embedding(model, [query])
    query_vec = np.array(query_embs[0])
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    
    max_sim = 0
    for proc_id, emb_dict in proc_embeddings.items():
        for key in ['goal_emb', 'steps_emb']:
            if key in emb_dict:
                proc_vec = emb_dict[key]
                sim = float(np.dot(query_vec, proc_vec))
                max_sim = max(max_sim, sim)
    
    return max_sim


def compute_max_similarity_with_variants(
    queries: List[str],
    proc_embeddings: Dict[str, np.ndarray],
    model: str = "text-embedding-3-large"
) -> float:
    """计算多个query变体与所有procedure的最高相似度"""
    if not queries:
        return 0
    
    query_embs, _ = parallel_get_embedding(model, queries)
    query_vecs = np.array(query_embs)
    norms = np.linalg.norm(query_vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    query_vecs = query_vecs / norms
    
    max_sim = 0
    for proc_id, emb_dict in proc_embeddings.items():
        for key in ['goal_emb', 'steps_emb']:
            if key in emb_dict:
                proc_vec = emb_dict[key].reshape(1, -1)
                sims = np.dot(query_vecs, proc_vec.T)
                max_sim = max(max_sim, float(np.max(sims)))
    
    return max_sim


def compute_procedure_embeddings(nstf_graph: Dict, model: str = "text-embedding-3-large") -> Dict:
    """计算Procedure的多粒度embedding"""
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    if not proc_nodes:
        return {}
    
    texts = []
    text_info = []
    
    for proc_id, proc_node in proc_nodes.items():
        goal = proc_node.get('goal', '')
        if goal:
            texts.append(goal)
            text_info.append((proc_id, 'goal'))
        
        steps = proc_node.get('steps', [])
        if steps:
            step_actions = [s.get('action', '') for s in steps if isinstance(s, dict)]
            combined = '. '.join(step_actions)
            if combined:
                texts.append(combined)
                text_info.append((proc_id, 'steps'))
    
    if not texts:
        return {}
    
    all_embeddings, _ = parallel_get_embedding(model, texts)
    
    result = defaultdict(dict)
    for i, emb in enumerate(all_embeddings):
        proc_id, text_type = text_info[i]
        emb_vec = np.array(emb)
        emb_vec = emb_vec / (np.linalg.norm(emb_vec) + 1e-8)
        result[proc_id][f'{text_type}_emb'] = emb_vec
    
    return dict(result)


def run_backtranslate_comparison(dataset: str, sample_size: int = 30):
    """对比 back_translate 前后的命中率"""
    print(f"\n{'='*70}")
    print(f"Stage 1b: back_translate 效果测试 - {dataset.upper()}")
    print(f"{'='*70}")
    
    # 加载annotation
    ann_path = ANNOTATIONS_DIR / f'{dataset}.json'
    with open(ann_path, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # 收集测试样本
    test_samples = []
    
    for video_name in annotations.keys():
        nstf_graph = load_nstf_graph(video_name, dataset)
        if nstf_graph is None:
            continue
        
        video_graph = load_video_graph_safe(video_name, dataset)
        if video_graph is None:
            continue
        
        proc_embeddings = compute_procedure_embeddings(nstf_graph)
        if not proc_embeddings:
            continue
        
        qa_list = annotations[video_name].get('qa_list', [])
        for qa in qa_list:
            test_samples.append({
                'video_name': video_name,
                'question': qa['question'],
                'video_graph': video_graph,
                'proc_embeddings': proc_embeddings,
            })
    
    print(f"  收集到 {len(test_samples)} 个测试样本")
    
    if len(test_samples) > sample_size:
        test_samples = random.sample(test_samples, sample_size)
        print(f"  采样 {sample_size} 个进行测试")
    
    # 对比测试
    results_original = []
    results_backtrans = []
    improvements = []
    
    thresholds = [0.25, 0.30, 0.35, 0.40]
    
    for i, sample in enumerate(test_samples):
        print(f"  测试 {i+1}/{len(test_samples)}: {sample['question'][:50]}...")
        
        # 原始query
        orig_sim = compute_max_similarity(
            sample['question'],
            sample['proc_embeddings']
        )
        results_original.append(orig_sim)
        
        # back_translate后
        try:
            variants = back_translate(sample['video_graph'], [sample['question']])
            if len(variants) > 15:
                variants = random.sample(variants, 15)
            bt_sim = compute_max_similarity_with_variants(
                variants,
                sample['proc_embeddings']
            )
        except Exception as e:
            print(f"    back_translate失败: {e}")
            bt_sim = orig_sim
        
        results_backtrans.append(bt_sim)
        improvements.append(bt_sim - orig_sim)
    
    # 统计
    print(f"\n【相似度对比】")
    print(f"  原始query平均: {np.mean(results_original):.3f}")
    print(f"  back_trans平均: {np.mean(results_backtrans):.3f}")
    print(f"  平均提升: {np.mean(improvements):.3f} ({np.mean(improvements)/max(np.mean(results_original),0.01)*100:.1f}%)")
    
    print(f"\n【命中率对比 (原始 vs back_translate)】")
    for t in thresholds:
        orig_hits = sum(1 for s in results_original if s >= t)
        bt_hits = sum(1 for s in results_backtrans if s >= t)
        total = len(test_samples)
        orig_rate = orig_hits / total
        bt_rate = bt_hits / total
        delta = bt_rate - orig_rate
        
        print(f"  threshold={t:.2f}: {orig_rate:5.1%} → {bt_rate:5.1%} ({delta:+.1%})")
    
    print(f"\n【提升分布】")
    improved = sum(1 for x in improvements if x > 0.01)
    same = sum(1 for x in improvements if -0.01 <= x <= 0.01)
    worse = sum(1 for x in improvements if x < -0.01)
    print(f"  提升: {improved} ({improved/len(improvements)*100:.1f}%)")
    print(f"  持平: {same} ({same/len(improvements)*100:.1f}%)")
    print(f"  下降: {worse} ({worse/len(improvements)*100:.1f}%)")
    
    return {
        'original': results_original,
        'backtrans': results_backtrans,
        'improvements': improvements,
    }


def main():
    print("Stage 1b: back_translate 效果测试")
    print("=" * 70)
    print("目标: 验证 back_translate 能否提升 query-procedure 匹配度")
    
    for dataset in ['web']:  # 只测试web（数据量较小，API调用更少）
        try:
            run_backtranslate_comparison(dataset, sample_size=20)
        except Exception as e:
            print(f"\n⚠️ {dataset} 分析出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Stage 1b 完成")
    print("=" * 70)


if __name__ == '__main__':
    main()
