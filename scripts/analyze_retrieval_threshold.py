#!/usr/bin/env python3
"""
分析 Retrieval Threshold 对NSTF系统性能的影响

目的：
1. 评估不同threshold下的检索质量
2. 分析threshold与召回率、准确率的权衡关系
3. 为论文中的threshold选择提供数据支撑
"""

import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity

# 设置项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 添加BytedanceM3Agent到路径
bytedance_root = project_root.parent / "BytedanceM3Agent"
sys.path.insert(0, str(bytedance_root))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(bytedance_root / ".env")

from mmagent.utils.chat_api import get_embedding_with_retry

def load_nstf_graph(video_name, dataset='robot'):
    """加载NSTF图谱"""
    nstf_path = project_root / f"data/nstf_graphs/{dataset}/{video_name}_nstf.pkl"
    if not nstf_path.exists():
        raise FileNotFoundError(f"NSTF graph not found: {nstf_path}")
    
    with open(nstf_path, 'rb') as f:
        graph = pickle.load(f)
    return graph

def load_baseline_graph(video_name, dataset='robot'):
    """加载Baseline Memory Graph"""
    baseline_path = bytedance_root / f"data/memory_graphs/{dataset}/{video_name}.pkl"
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline graph not found: {baseline_path}")
    
    with open(baseline_path, 'rb') as f:
        graph = pickle.load(f)
    return graph

def load_questions(video_name, dataset='robot'):
    """加载测试问题"""
    # 从BytedanceM3Agent的annotations文件加载问题
    annotations_path = bytedance_root / f"data/annotations/{dataset}.json"
    
    if not annotations_path.exists():
        print(f"⚠️ Annotations file not found: {annotations_path}")
        return []
    
    questions = []
    try:
        with open(annotations_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if video_name not in data:
            print(f"⚠️ Video {video_name} not found in annotations")
            return []
        
        video_data = data[video_name]
        for qa in video_data.get('qa_list', []):
            questions.append({
                'id': qa.get('question_id', 'unknown'),
                'question': qa.get('question', ''),
                'answer': qa.get('answer', ''),
                'type': 'Procedural' if any('Procedure' in t or 'Task' in t for t in qa.get('type', [])) 
                        else 'Constrained' if any('Constraint' in t for t in qa.get('type', []))
                        else 'Factual'
            })
    except Exception as e:
        print(f"⚠️ Error loading questions from {annotations_path}: {e}")
        import traceback
        traceback.print_exc()
    
    return questions

def compute_retrieval_metrics(nstf_graph, baseline_graph, questions, thresholds):
    """
    计算不同threshold下的检索指标
    
    指标：
    1. Recall@K: 召回率 - 在Top-K结果中相关内容的比例
    2. Precision@K: 准确率 - Top-K结果中相关内容的比例
    3. MRR: Mean Reciprocal Rank - 第一个相关结果的平均排名倒数
    4. Coverage: 覆盖率 - 能检索到至少1个结果的查询比例
    """
    
    results = {
        'threshold_analysis': {},
        'question_breakdown': []
    }
    
    print(f"\n{'='*80}")
    print(f"检索质量分析 - {len(questions)} 个问题")
    print(f"{'='*80}")
    
    for threshold in thresholds:
        print(f"\n🔍 Threshold = {threshold}")
        
        metrics = {
            'retrieval_counts': [],  # 每个query检索到的结果数
            'relevant_counts': [],   # 每个query检索到的相关结果数
            'top1_relevant': [],     # Top-1是否相关
            'top3_relevant': [],     # Top-3中相关的数量
            'top5_relevant': [],     # Top-5中相关的数量
            'mrr_scores': [],        # MRR得分
            'zero_recall': 0,        # 0个结果的查询数
        }
        
        for q_data in questions:
            question = q_data['question']
            q_type = q_data['type']
            
            # 1. 获取query embedding
            query_emb, _ = get_embedding_with_retry("text-embedding-3-large", question)
            query_emb = np.array(query_emb).reshape(1, -1)
            
            # 2. 计算与所有Procedure的相似度 (goal + step双层索引)
            procedure_scores = []
            for proc_id, proc_node in nstf_graph.get('procedure_nodes', {}).items():
                embeddings = proc_node.get('embeddings', {})
                
                # 使用论文中的公式: score = α * sim(goal) + (1-α) * sim(step)
                alpha = 0.3  # 论文默认值
                
                goal_emb = embeddings.get('goal_emb')
                step_emb = embeddings.get('step_emb')
                
                if goal_emb is not None and step_emb is not None:
                    goal_sim = cosine_similarity(query_emb, np.array(goal_emb).reshape(1, -1))[0][0]
                    step_sim = cosine_similarity(query_emb, np.array(step_emb).reshape(1, -1))[0][0]
                    
                    score = alpha * goal_sim + (1 - alpha) * step_sim
                    procedure_scores.append({
                        'proc_id': proc_id,
                        'score': score,
                        'goal': proc_node.get('goal', ''),
                        'type': proc_node.get('proc_type', 'unknown')
                    })
            
            # 3. 排序并应用threshold
            procedure_scores.sort(key=lambda x: x['score'], reverse=True)
            retrieved = [p for p in procedure_scores if p['score'] >= threshold]
            
            # 4. 评估相关性 (简化版: 基于类型匹配)
            # 在实际应用中，可以用LLM或人工标注
            relevant_types = {
                'Procedural': ['task', 'habit'],
                'Factual': ['trait', 'social'],
                'Constrained': ['task']
            }
            
            expected_types = relevant_types.get(q_type, [])
            relevant = [p for p in retrieved if p['type'] in expected_types or q_type == 'Unknown']
            
            # 5. 计算指标
            num_retrieved = len(retrieved)
            num_relevant = len(relevant)
            
            metrics['retrieval_counts'].append(num_retrieved)
            metrics['relevant_counts'].append(num_relevant)
            
            if num_retrieved == 0:
                metrics['zero_recall'] += 1
                metrics['top1_relevant'].append(0)
                metrics['top3_relevant'].append(0)
                metrics['top5_relevant'].append(0)
                metrics['mrr_scores'].append(0)
            else:
                # Top-K metrics
                metrics['top1_relevant'].append(1 if len([p for p in retrieved[:1] if p['type'] in expected_types]) > 0 else 0)
                metrics['top3_relevant'].append(len([p for p in retrieved[:3] if p['type'] in expected_types]))
                metrics['top5_relevant'].append(len([p for p in retrieved[:5] if p['type'] in expected_types]))
                
                # MRR
                first_relevant_idx = next((i for i, p in enumerate(retrieved) if p['type'] in expected_types), -1)
                mrr = 1 / (first_relevant_idx + 1) if first_relevant_idx >= 0 else 0
                metrics['mrr_scores'].append(mrr)
        
        # 6. 汇总统计
        num_questions = len(questions)
        avg_retrieved = np.mean(metrics['retrieval_counts']) if metrics['retrieval_counts'] else 0
        avg_relevant = np.mean(metrics['relevant_counts']) if metrics['relevant_counts'] else 0
        
        recall_at_1 = np.mean(metrics['top1_relevant']) if metrics['top1_relevant'] else 0
        recall_at_3 = np.mean([min(x/3, 1.0) for x in metrics['top3_relevant']]) if metrics['top3_relevant'] else 0
        recall_at_5 = np.mean([min(x/5, 1.0) for x in metrics['top5_relevant']]) if metrics['top5_relevant'] else 0
        
        precision = avg_relevant / avg_retrieved if avg_retrieved > 0 else 0
        mrr = np.mean(metrics['mrr_scores']) if metrics['mrr_scores'] else 0
        coverage = 1 - (metrics['zero_recall'] / num_questions)
        
        results['threshold_analysis'][threshold] = {
            'avg_retrieved': round(avg_retrieved, 2),
            'avg_relevant': round(avg_relevant, 2),
            'recall@1': round(recall_at_1, 3),
            'recall@3': round(recall_at_3, 3),
            'recall@5': round(recall_at_5, 3),
            'precision': round(precision, 3),
            'mrr': round(mrr, 3),
            'coverage': round(coverage, 3),
            'zero_recall_count': metrics['zero_recall']
        }
        
        print(f"  平均检索数: {avg_retrieved:.2f}")
        print(f"  平均相关数: {avg_relevant:.2f}")
        print(f"  Recall@1: {recall_at_1:.3f}")
        print(f"  Recall@3: {recall_at_3:.3f}")
        print(f"  Recall@5: {recall_at_5:.3f}")
        print(f"  Precision: {precision:.3f}")
        print(f"  MRR: {mrr:.3f}")
        print(f"  Coverage: {coverage:.3f}")
        print(f"  零召回查询数: {metrics['zero_recall']}/{num_questions}")
    
    return results

def analyze_embedding_distribution(nstf_graph, baseline_graph):
    """分析embedding的分布特征"""
    
    print(f"\n{'='*80}")
    print("Embedding 分布分析")
    print(f"{'='*80}")
    
    # 收集所有procedure embeddings
    goal_embs = []
    step_embs = []
    
    for proc_id, proc_node in nstf_graph.get('procedure_nodes', {}).items():
        embeddings = proc_node.get('embeddings', {})
        if 'goal_emb' in embeddings:
            goal_embs.append(np.array(embeddings['goal_emb']))
        if 'step_emb' in embeddings:
            step_embs.append(np.array(embeddings['step_emb']))
    
    if len(goal_embs) == 0:
        print("⚠️ No procedure embeddings found")
        return {}
    
    goal_embs = np.array(goal_embs)
    step_embs = np.array(step_embs)
    
    # 计算内部相似度分布
    goal_sim = cosine_similarity(goal_embs)
    step_sim = cosine_similarity(step_embs)
    
    # 只取上三角（排除自身和重复）
    goal_upper = goal_sim[np.triu_indices_from(goal_sim, k=1)]
    step_upper = step_sim[np.triu_indices_from(step_sim, k=1)]
    
    stats = {
        'goal_embeddings': {
            'count': len(goal_embs),
            'dimension': goal_embs.shape[1],
            'norm_mean': float(np.linalg.norm(goal_embs, axis=1).mean()),
            'norm_std': float(np.linalg.norm(goal_embs, axis=1).std()),
            'internal_similarity': {
                'min': float(goal_upper.min()),
                'max': float(goal_upper.max()),
                'mean': float(goal_upper.mean()),
                'std': float(goal_upper.std()),
                'p50': float(np.percentile(goal_upper, 50)),
                'p75': float(np.percentile(goal_upper, 75)),
                'p90': float(np.percentile(goal_upper, 90)),
                'p95': float(np.percentile(goal_upper, 95)),
            }
        },
        'step_embeddings': {
            'count': len(step_embs),
            'dimension': step_embs.shape[1],
            'norm_mean': float(np.linalg.norm(step_embs, axis=1).mean()),
            'norm_std': float(np.linalg.norm(step_embs, axis=1).std()),
            'internal_similarity': {
                'min': float(step_upper.min()),
                'max': float(step_upper.max()),
                'mean': float(step_upper.mean()),
                'std': float(step_upper.std()),
                'p50': float(np.percentile(step_upper, 50)),
                'p75': float(np.percentile(step_upper, 75)),
                'p90': float(np.percentile(step_upper, 90)),
                'p95': float(np.percentile(step_upper, 95)),
            }
        }
    }
    
    print(f"\n📊 Goal Embeddings:")
    print(f"  数量: {stats['goal_embeddings']['count']}")
    print(f"  维度: {stats['goal_embeddings']['dimension']}")
    print(f"  L2范数: {stats['goal_embeddings']['norm_mean']:.4f} ± {stats['goal_embeddings']['norm_std']:.4f}")
    print(f"  内部相似度分布:")
    for k, v in stats['goal_embeddings']['internal_similarity'].items():
        print(f"    {k}: {v:.4f}")
    
    print(f"\n📊 Step Embeddings:")
    print(f"  数量: {stats['step_embeddings']['count']}")
    print(f"  维度: {stats['step_embeddings']['dimension']}")
    print(f"  L2范数: {stats['step_embeddings']['norm_mean']:.4f} ± {stats['step_embeddings']['norm_std']:.4f}")
    print(f"  内部相似度分布:")
    for k, v in stats['step_embeddings']['internal_similarity'].items():
        print(f"    {k}: {v:.4f}")
    
    return stats

def main():
    # 配置
    DATASET = 'robot'
    TEST_VIDEOS = ['kitchen_03', 'kitchen_22', 'kitchen_15']  # 使用有测试结果的视频
    THRESHOLDS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    
    print(f"🔬 Retrieval Threshold 影响分析")
    print(f"Dataset: {DATASET}")
    print(f"测试视频: {TEST_VIDEOS}")
    print(f"Threshold范围: {min(THRESHOLDS)} ~ {max(THRESHOLDS)}")
    
    all_results = {}
    
    for video_name in TEST_VIDEOS:
        print(f"\n{'#'*80}")
        print(f"视频: {video_name}")
        print(f"{'#'*80}")
        
        try:
            # 加载数据
            nstf_graph = load_nstf_graph(video_name, DATASET)
            baseline_graph = load_baseline_graph(video_name, DATASET)
            questions = load_questions(video_name, DATASET)
            
            if len(questions) == 0:
                print(f"⚠️ No questions found for {video_name}, skipping...")
                continue
            
            print(f"✅ 加载成功:")
            print(f"  - NSTF Procedures: {len(nstf_graph.get('procedure_nodes', {}))}")
            print(f"  - 测试问题: {len(questions)}")
            
            # 分析embedding分布
            emb_stats = analyze_embedding_distribution(nstf_graph, baseline_graph)
            
            # 计算检索指标
            metrics = compute_retrieval_metrics(nstf_graph, baseline_graph, questions, THRESHOLDS)
            
            all_results[video_name] = {
                'embedding_stats': emb_stats,
                'retrieval_metrics': metrics
            }
            
        except Exception as e:
            print(f"❌ Error processing {video_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # 保存结果
    output_dir = project_root / "analysis_results"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"threshold_analysis_{DATASET}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✅ 分析完成！结果已保存至: {output_file}")
    print(f"{'='*80}")
    
    # 汇总跨视频的建议
    print(f"\n📌 总结与建议:")
    print(f"\n1. 当前系统使用的threshold: 0.05 (control.py)")
    print(f"2. 论文方法章节提到的threshold: θ (未明确具体值)")
    print(f"3. 建议的threshold选择依据:")
    print(f"   - 若优先召回率(Recall): 选择较低threshold (0.05 - 0.15)")
    print(f"   - 若优先准确率(Precision): 选择较高threshold (0.25 - 0.35)")
    print(f"   - 平衡点: 观察MRR和Coverage的trade-off")
    print(f"\n请查看详细数据文件获取每个threshold的具体指标。")

if __name__ == "__main__":
    main()
