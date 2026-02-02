# -*- coding: utf-8 -*-
"""
Stage 2: 小规模端到端测试

目标:
1. 验证完整流程的正确性（检索 → 提取信息 → 构建prompt → 生成回答）
2. 测试调整后的threshold=0.30
3. 测试fallback机制
4. 对比NSTF vs Baseline的回答质量

只选取10个问题进行详细分析
"""

import os
import sys
import json
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import random

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

# 环境设置
from env_setup import setup_all
setup_all()

from mmagent.utils.chat_api import parallel_get_embedding, get_response
from mmagent.retrieve import back_translate
from mmagent.utils.general import load_video_graph

# 数据路径
DATA_DIR = PROJECT_DIR / 'data'
NSTF_GRAPHS_DIR = DATA_DIR / 'nstf_graphs'
ANNOTATIONS_DIR = DATA_DIR / 'annotations'
MEMORY_GRAPHS_DIR = DATA_DIR / 'memory_graphs'

# 新的threshold
THRESHOLD = 0.30
MIN_CONFIDENCE = 0.25  # 低于此值仍然fallback


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
            text_info.append((proc_id, 'goal', goal))
        
        steps = proc_node.get('steps', [])
        if steps:
            step_actions = [s.get('action', '') for s in steps if isinstance(s, dict)]
            combined = '. '.join(step_actions)
            if combined:
                texts.append(combined)
                text_info.append((proc_id, 'steps', combined))
    
    if not texts:
        return {}
    
    all_embeddings, _ = parallel_get_embedding(model, texts)
    
    result = defaultdict(dict)
    for i, emb in enumerate(all_embeddings):
        proc_id, text_type, text = text_info[i]
        emb_vec = np.array(emb)
        emb_vec = emb_vec / (np.linalg.norm(emb_vec) + 1e-8)
        result[proc_id][f'{text_type}_emb'] = emb_vec
        result[proc_id][f'{text_type}_text'] = text
    
    return dict(result)


def search_procedures(
    query: str,
    proc_embeddings: Dict,
    nstf_graph: Dict,
    threshold: float = THRESHOLD,
    max_results: int = 3,
    model: str = "text-embedding-3-large"
) -> Tuple[List[Dict], str]:
    """
    检索相关Procedure
    
    Returns:
        (匹配结果列表, 决策: 'use_nstf' | 'fallback')
    """
    # 计算query embedding
    query_embs, _ = parallel_get_embedding(model, [query])
    query_vec = np.array(query_embs[0])
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    
    results = []
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    
    for proc_id, embeddings in proc_embeddings.items():
        best_sim = -1
        best_match_type = None
        
        for emb_type in ['goal_emb', 'steps_emb']:
            if emb_type in embeddings:
                proc_vec = embeddings[emb_type]
                sim = float(np.dot(query_vec, proc_vec))
                if sim > best_sim:
                    best_sim = sim
                    best_match_type = emb_type.replace('_emb', '')
        
        if best_sim >= threshold:
            proc_node = proc_nodes.get(proc_id, {})
            results.append({
                'proc_id': proc_id,
                'similarity': best_sim,
                'match_type': best_match_type,
                'proc_node': proc_node,
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    results = results[:max_results]
    
    # 决策
    if not results:
        return [], 'fallback'
    if results[0]['similarity'] < MIN_CONFIDENCE:
        return [], 'fallback'
    
    return results, 'use_nstf'


def extract_procedure_info(proc_result: Dict, video_graph) -> Dict:
    """
    从Procedure提取LLM需要的信息
    
    Returns:
        {
            'goal': str,
            'ordered_steps': str,  # "Step 1: ... Step 2: ..."
            'evidence_clips': list,  # 原始clip内容
        }
    """
    proc_node = proc_result['proc_node']
    
    # Goal
    goal = proc_node.get('goal', 'Unknown goal')
    
    # Ordered steps
    steps = proc_node.get('steps', [])
    ordered_steps = []
    for i, step in enumerate(steps):
        if isinstance(step, dict):
            action = step.get('action', '')
            if action:
                ordered_steps.append(f"Step {i+1}: {action}")
    ordered_steps_str = '\n'.join(ordered_steps) if ordered_steps else 'No steps available'
    
    # Evidence clips from episodic_links
    evidence_clips = []
    episodic_links = proc_node.get('episodic_links', [])
    
    if video_graph is not None and episodic_links:
        for link in episodic_links[:5]:  # 最多5个clips
            clip_id = link.get('clip_id')
            if clip_id:
                try:
                    # 从video_graph获取clip内容
                    clip_content = video_graph.get_node_content(clip_id)
                    if clip_content:
                        evidence_clips.append({
                            'clip_id': clip_id,
                            'content': clip_content[:500],  # 截断
                        })
                except:
                    pass
    
    return {
        'goal': goal,
        'ordered_steps': ordered_steps_str,
        'evidence_clips': evidence_clips,
        'similarity': proc_result['similarity'],
        'match_type': proc_result['match_type'],
    }


def build_nstf_prompt(question: str, procedure_infos: List[Dict]) -> str:
    """构建包含Procedure信息的prompt"""
    
    prompt_parts = [
        f"Question: {question}\n",
        "=== Relevant Procedural Knowledge ===\n"
    ]
    
    for i, info in enumerate(procedure_infos):
        prompt_parts.append(f"\n--- Procedure {i+1} (Relevance: {info['similarity']:.2f}) ---")
        prompt_parts.append(f"Goal: {info['goal']}")
        prompt_parts.append(f"\n{info['ordered_steps']}")
        
        if info['evidence_clips']:
            prompt_parts.append("\nSupporting Evidence:")
            for clip in info['evidence_clips'][:3]:
                prompt_parts.append(f"  [{clip['clip_id']}]: {clip['content'][:200]}...")
    
    prompt_parts.append("\n\n=== Instructions ===")
    prompt_parts.append("Based on the procedural knowledge above, answer the question.")
    prompt_parts.append("If the procedure is not relevant to the question, say so and provide a general answer.")
    prompt_parts.append("\nAnswer:")
    
    return '\n'.join(prompt_parts)


def build_baseline_prompt(question: str, video_graph, top_k: int = 5) -> str:
    """构建baseline prompt（使用clip-level检索）"""
    
    # 这里简化处理，实际应该调用baseline的检索逻辑
    # 我们只构建一个简单的prompt
    prompt = f"""Question: {question}

=== Video Content ===
(Clip-level retrieval results would be here in actual baseline)

Answer the question based on the video content above.

Answer:"""
    
    return prompt


def run_single_test(
    question: str,
    answer: str,
    video_name: str,
    dataset: str,
    nstf_graph: Dict,
    proc_embeddings: Dict,
    video_graph,
    verbose: bool = True
) -> Dict:
    """运行单个问题的完整测试"""
    
    result = {
        'question': question,
        'ground_truth': answer,
        'video_name': video_name,
    }
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"Ground Truth: {answer}")
    
    # Step 1: 检索
    proc_results, decision = search_procedures(
        question, proc_embeddings, nstf_graph
    )
    
    result['decision'] = decision
    result['num_procedures_found'] = len(proc_results)
    
    if verbose:
        print(f"\n[检索结果] Decision: {decision}")
        if proc_results:
            for pr in proc_results:
                print(f"  - {pr['proc_id']}: sim={pr['similarity']:.3f}, match={pr['match_type']}")
                print(f"    Goal: {pr['proc_node'].get('goal', '')[:60]}...")
    
    if decision == 'use_nstf':
        # Step 2: 提取信息
        procedure_infos = [extract_procedure_info(pr, video_graph) for pr in proc_results]
        
        # Step 3: 构建prompt
        nstf_prompt = build_nstf_prompt(question, procedure_infos)
        
        if verbose:
            print(f"\n[NSTF Prompt 预览]")
            print(nstf_prompt[:500] + "..." if len(nstf_prompt) > 500 else nstf_prompt)
        
        result['nstf_prompt'] = nstf_prompt
        result['procedure_infos'] = procedure_infos
        
        # Step 4: 调用LLM生成回答（可选，消耗API）
        # try:
        #     nstf_answer = get_chat_response(nstf_prompt)
        #     result['nstf_answer'] = nstf_answer
        # except Exception as e:
        #     result['nstf_answer'] = f"Error: {e}"
        
    else:
        result['fallback_reason'] = 'No relevant procedures found' if not proc_results else 'Low confidence'
        if verbose:
            print(f"\n[Fallback] Reason: {result['fallback_reason']}")
    
    return result


def select_test_questions(dataset: str, n_questions: int = 10) -> List[Dict]:
    """选择测试问题"""
    
    ann_path = ANNOTATIONS_DIR / f'{dataset}.json'
    with open(ann_path, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    candidates = []
    
    for video_name in annotations.keys():
        nstf_graph = load_nstf_graph(video_name, dataset)
        if nstf_graph is None:
            continue
        
        video_graph = load_video_graph_safe(video_name, dataset)
        proc_embeddings = compute_procedure_embeddings(nstf_graph)
        
        if not proc_embeddings:
            continue
        
        qa_list = annotations[video_name].get('qa_list', [])
        for qa in qa_list:
            candidates.append({
                'video_name': video_name,
                'question': qa['question'],
                'answer': qa.get('answer', ''),
                'nstf_graph': nstf_graph,
                'proc_embeddings': proc_embeddings,
                'video_graph': video_graph,
            })
    
    # 采样
    if len(candidates) > n_questions:
        candidates = random.sample(candidates, n_questions)
    
    return candidates


def main():
    print("Stage 2: 小规模端到端测试")
    print("=" * 70)
    print(f"参数: threshold={THRESHOLD}, min_confidence={MIN_CONFIDENCE}")
    
    dataset = 'web'  # 使用Web数据集（命中率更高）
    n_questions = 10
    
    print(f"\n数据集: {dataset}, 测试问题数: {n_questions}")
    
    # 选择测试问题
    test_questions = select_test_questions(dataset, n_questions)
    print(f"收集到 {len(test_questions)} 个测试问题")
    
    # 运行测试
    results = []
    nstf_count = 0
    fallback_count = 0
    
    for q in test_questions:
        result = run_single_test(
            question=q['question'],
            answer=q['answer'],
            video_name=q['video_name'],
            dataset=dataset,
            nstf_graph=q['nstf_graph'],
            proc_embeddings=q['proc_embeddings'],
            video_graph=q['video_graph'],
            verbose=True
        )
        results.append(result)
        
        if result['decision'] == 'use_nstf':
            nstf_count += 1
        else:
            fallback_count += 1
    
    # 汇总
    print("\n" + "=" * 70)
    print("Stage 2 汇总")
    print("=" * 70)
    print(f"总问题数: {len(results)}")
    print(f"使用NSTF: {nstf_count} ({nstf_count/len(results)*100:.1f}%)")
    print(f"回退Baseline: {fallback_count} ({fallback_count/len(results)*100:.1f}%)")
    
    # 分析使用NSTF的case
    nstf_cases = [r for r in results if r['decision'] == 'use_nstf']
    if nstf_cases:
        avg_procedures = np.mean([r['num_procedures_found'] for r in nstf_cases])
        print(f"平均返回Procedure数: {avg_procedures:.1f}")
    
    print("\n" + "=" * 70)
    print("Stage 2 完成")
    print("=" * 70)
    print("\n下一步: 检查上述输出，确认:")
    print("  1. 检索到的Procedure是否与问题相关")
    print("  2. Prompt格式是否合理")
    print("  3. Fallback决策是否正确")
    print("\n如果一切正常，进入 Stage 3: 正式实验")


if __name__ == '__main__':
    main()
