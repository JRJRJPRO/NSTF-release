# -*- coding: utf-8 -*-
"""
Stage 1: 离线相似度测试

验证目标:
1. Procedure 命中率（query能否匹配到相关Procedure）
2. 多粒度匹配分布（goal vs steps 各自的命中比例）
3. 不同threshold下的表现
4. 验证 back_translate 对命中率的影响

不运行完整QA，只测试 query-procedure 相似度
"""

import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

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
    """加载单个NSTF图谱"""
    nstf_path = NSTF_GRAPHS_DIR / dataset / f'{video_name}_nstf.pkl'
    if not nstf_path.exists():
        return None
    with open(nstf_path, 'rb') as f:
        return pickle.load(f)


def load_video_graph_safe(video_name: str, dataset: str):
    """安全加载video graph"""
    mem_path = MEMORY_GRAPHS_DIR / dataset / f'{video_name}.pkl'
    if not mem_path.exists():
        return None
    try:
        graph = load_video_graph(str(mem_path))
        graph.refresh_equivalences()
        return graph
    except Exception as e:
        print(f"  ⚠️ 加载video graph失败: {e}")
        return None


def compute_procedure_embeddings(nstf_graph: Dict, model: str = "text-embedding-3-large") -> Dict:
    """
    计算Procedure的多粒度embedding
    
    返回: {proc_id: {'goal_emb': [...], 'steps_emb': [...], 'goal_text': '...', 'steps_text': '...'}}
    """
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    if not proc_nodes:
        return {}
    
    # 收集所有需要embed的文本
    texts = []
    text_info = []  # (proc_id, text_type)
    
    for proc_id, proc_node in proc_nodes.items():
        # Goal
        goal = proc_node.get('goal', '')
        if goal:
            texts.append(goal)
            text_info.append((proc_id, 'goal', goal))
        
        # Steps combined
        steps = proc_node.get('steps', [])
        if steps:
            step_actions = [s.get('action', '') for s in steps if isinstance(s, dict)]
            combined = '. '.join(step_actions)
            if combined:
                texts.append(combined)
                text_info.append((proc_id, 'steps', combined))
    
    if not texts:
        return {}
    
    # 批量计算embedding
    all_embeddings, _ = parallel_get_embedding(model, texts)
    
    # 组织结果
    result = defaultdict(dict)
    for i, emb in enumerate(all_embeddings):
        proc_id, text_type, text = text_info[i]
        emb_vec = np.array(emb)
        emb_vec = emb_vec / (np.linalg.norm(emb_vec) + 1e-8)
        result[proc_id][f'{text_type}_emb'] = emb_vec
        result[proc_id][f'{text_type}_text'] = text
    
    return dict(result)


def search_procedures_multi_granular(
    query: str,
    proc_embeddings: Dict,
    threshold: float = 0.4,
    model: str = "text-embedding-3-large",
    video_graph = None,
    use_back_translate: bool = False
) -> List[Dict]:
    """
    多粒度Procedure检索
    
    Args:
        query: 查询文本
        proc_embeddings: Procedure的embedding字典
        threshold: 相似度阈值
        video_graph: 用于back_translate（可选）
        use_back_translate: 是否对query做back_translate
    
    Returns:
        匹配结果列表，按相似度排序
    """
    # 准备query变体
    if use_back_translate and video_graph is not None:
        queries = back_translate(video_graph, [query])
        if len(queries) > 20:
            import random
            queries = random.sample(queries, 20)
    else:
        queries = [query]
    
    # 计算query embeddings
    query_embeddings, _ = parallel_get_embedding(model, queries)
    query_vecs = np.array(query_embeddings)
    # 归一化
    norms = np.linalg.norm(query_vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1
    query_vecs = query_vecs / norms
    
    results = []
    
    for proc_id, embeddings in proc_embeddings.items():
        best_sim = -1
        best_match_type = None
        
        # 检查goal匹配
        if 'goal_emb' in embeddings:
            goal_emb = embeddings['goal_emb'].reshape(1, -1)
            sims = np.dot(query_vecs, goal_emb.T)  # (n_queries, 1)
            goal_sim = float(np.max(sims))
            if goal_sim > best_sim:
                best_sim = goal_sim
                best_match_type = 'goal'
        
        # 检查steps匹配
        if 'steps_emb' in embeddings:
            steps_emb = embeddings['steps_emb'].reshape(1, -1)
            sims = np.dot(query_vecs, steps_emb.T)
            steps_sim = float(np.max(sims))
            if steps_sim > best_sim:
                best_sim = steps_sim
                best_match_type = 'steps'
        
        if best_sim >= threshold:
            results.append({
                'proc_id': proc_id,
                'similarity': best_sim,
                'match_type': best_match_type,
                'goal_text': embeddings.get('goal_text', ''),
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results


def analyze_similarity_distribution(
    questions: List[Dict],
    proc_embeddings: Dict,
    video_graph = None,
    thresholds: List[float] = [0.3, 0.35, 0.4, 0.45, 0.5]
) -> Dict:
    """
    分析问题与Procedure的相似度分布
    """
    all_max_sims = []  # 每个问题的最高相似度
    match_type_counts = {'goal': 0, 'steps': 0, 'none': 0}
    
    # 按threshold统计命中率
    hits_by_threshold = {t: 0 for t in thresholds}
    
    for q in questions:
        query = q['question']
        
        # 检索（不使用back_translate，先测基础情况）
        results = search_procedures_multi_granular(
            query, proc_embeddings, 
            threshold=0.0,  # 获取所有结果
            video_graph=video_graph,
            use_back_translate=False
        )
        
        if results:
            max_sim = results[0]['similarity']
            match_type = results[0]['match_type']
            all_max_sims.append(max_sim)
            match_type_counts[match_type] += 1
            
            for t in thresholds:
                if max_sim >= t:
                    hits_by_threshold[t] += 1
        else:
            all_max_sims.append(0)
            match_type_counts['none'] += 1
    
    total = len(questions)
    return {
        'total_questions': total,
        'max_sims': all_max_sims,
        'avg_max_sim': np.mean(all_max_sims) if all_max_sims else 0,
        'median_max_sim': np.median(all_max_sims) if all_max_sims else 0,
        'match_type_distribution': {k: v/max(total,1) for k, v in match_type_counts.items()},
        'hit_rate_by_threshold': {t: hits_by_threshold[t]/max(total,1) for t in thresholds},
    }


def run_stage1_analysis(dataset: str, sample_size: int = None):
    """运行Stage 1分析"""
    print(f"\n{'='*70}")
    print(f"Stage 1: 离线相似度测试 - {dataset.upper()}")
    print(f"{'='*70}")
    
    # 加载annotation
    ann_path = ANNOTATIONS_DIR / f'{dataset}.json'
    with open(ann_path, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # 收集所有有NSTF图谱的视频的问题
    all_questions = []
    videos_analyzed = 0
    
    for video_name in annotations.keys():
        nstf_graph = load_nstf_graph(video_name, dataset)
        if nstf_graph is None:
            continue
        
        video_graph = load_video_graph_safe(video_name, dataset)
        
        # 计算Procedure embeddings
        print(f"  处理: {video_name}...")
        proc_embeddings = compute_procedure_embeddings(nstf_graph)
        
        if not proc_embeddings:
            print(f"    跳过: 无有效Procedure embedding")
            continue
        
        # 收集该视频的问题
        qa_list = annotations[video_name].get('qa_list', [])
        for qa in qa_list:
            all_questions.append({
                'video_name': video_name,
                'question': qa['question'],
                'answer': qa.get('answer', ''),
                'proc_embeddings': proc_embeddings,
                'video_graph': video_graph,
            })
        
        videos_analyzed += 1
    
    print(f"\n  分析了 {videos_analyzed} 个视频，共 {len(all_questions)} 个问题")
    
    if sample_size and len(all_questions) > sample_size:
        import random
        all_questions = random.sample(all_questions, sample_size)
        print(f"  采样 {sample_size} 个问题进行分析")
    
    # 按视频分组分析
    overall_stats = {
        'max_sims': [],
        'match_types': defaultdict(int),
        'hits_by_threshold': defaultdict(int),
    }
    
    thresholds = [0.30, 0.35, 0.40, 0.45, 0.50]
    
    for q in all_questions:
        results = search_procedures_multi_granular(
            q['question'], 
            q['proc_embeddings'],
            threshold=0.0,
            video_graph=q['video_graph'],
            use_back_translate=False
        )
        
        if results:
            max_sim = results[0]['similarity']
            match_type = results[0]['match_type']
            overall_stats['max_sims'].append(max_sim)
            overall_stats['match_types'][match_type] += 1
            
            for t in thresholds:
                if max_sim >= t:
                    overall_stats['hits_by_threshold'][t] += 1
        else:
            overall_stats['max_sims'].append(0)
            overall_stats['match_types']['none'] += 1
    
    # 打印结果
    total = len(all_questions)
    print(f"\n【相似度分布】")
    sims = overall_stats['max_sims']
    print(f"  平均最高相似度: {np.mean(sims):.3f}")
    print(f"  中位数: {np.median(sims):.3f}")
    print(f"  最大值: {np.max(sims):.3f}")
    print(f"  最小值: {np.min(sims):.3f}")
    
    # 分位数
    print(f"\n  分位数分布:")
    for p in [25, 50, 75, 90, 95]:
        print(f"    {p}%: {np.percentile(sims, p):.3f}")
    
    print(f"\n【命中率 (不同threshold)】")
    for t in thresholds:
        hit_rate = overall_stats['hits_by_threshold'][t] / max(total, 1)
        bar = '█' * int(hit_rate * 40)
        print(f"  threshold={t:.2f}: {hit_rate:5.1%} ({overall_stats['hits_by_threshold'][t]:3d}/{total}) {bar}")
    
    print(f"\n【匹配类型分布】")
    for match_type, count in sorted(overall_stats['match_types'].items(), key=lambda x: -x[1]):
        ratio = count / max(total, 1)
        print(f"  {match_type:8s}: {count:3d} ({ratio:5.1%})")
    
    # 建议threshold
    print(f"\n【Threshold建议】")
    # 找到命中率在30-50%之间的threshold
    for t in thresholds:
        hit_rate = overall_stats['hits_by_threshold'][t] / max(total, 1)
        if 0.25 <= hit_rate <= 0.50:
            print(f"  推荐 threshold={t:.2f} (命中率 {hit_rate:.1%})")
            break
    else:
        # 如果没有合适的，选命中率最接近40%的
        best_t = min(thresholds, key=lambda t: abs(overall_stats['hits_by_threshold'][t]/max(total,1) - 0.4))
        hit_rate = overall_stats['hits_by_threshold'][best_t] / max(total, 1)
        print(f"  备选 threshold={best_t:.2f} (命中率 {hit_rate:.1%})")
    
    return overall_stats


def main():
    print("Stage 1: 离线相似度测试")
    print("=" * 70)
    print("目标: 验证多粒度匹配能力，确定合适的threshold")
    
    # 分析两个数据集
    for dataset in ['robot', 'web']:
        try:
            stats = run_stage1_analysis(dataset, sample_size=100)
        except Exception as e:
            print(f"\n⚠️ {dataset} 分析出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Stage 1 完成")
    print("=" * 70)
    print("\n下一步:")
    print("  根据分析结果确定 threshold 参数")
    print("  执行 Stage 2: 小规模端到端测试")


if __name__ == '__main__':
    main()
