#!/usr/bin/env python3
"""
Phase 1 核心链路验证 - 选择 baseline 能回答的问题测试
"""

import sys
from pathlib import Path

NSTF_MODEL_DIR = Path("/data1/rongjiej/NSTF_MODEL")
sys.path.insert(0, str(NSTF_MODEL_DIR))

import pickle
import json

def load_nstf_graph(video_name: str, dataset: str):
    path = NSTF_MODEL_DIR / "data" / "nstf_graphs" / dataset / f"{video_name}_nstf.pkl"
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_memory_graph(video_name: str, dataset: str):
    path = NSTF_MODEL_DIR / "data" / "memory_graphs" / dataset / f"{video_name}.pkl"
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_questions(video_name: str, dataset: str):
    ann_path = NSTF_MODEL_DIR / "data" / "annotations" / f"{dataset}.json"
    with open(ann_path, 'r') as f:
        data = json.load(f)
    video_data = data.get(video_name, {})
    if isinstance(video_data, dict):
        return video_data.get('qa_list', [])
    return video_data

def get_episodic_content(memory_graph, clip_id: int) -> list:
    if not hasattr(memory_graph, 'text_nodes_by_clip'):
        return []
    if clip_id not in memory_graph.text_nodes_by_clip:
        return []
    contents = []
    node_ids = memory_graph.text_nodes_by_clip[clip_id]
    for nid in node_ids:
        node = memory_graph.nodes.get(nid)
        if node:
            meta = getattr(node, 'metadata', {})
            node_contents = meta.get('contents', [])
            contents.extend(node_contents)
    return contents

def search_keyword_in_baseline(memory_graph, keyword: str) -> list:
    """在 baseline 中搜索关键词，返回找到的 clip_ids"""
    found_clips = []
    for clip_id in memory_graph.text_nodes_by_clip.keys():
        node_ids = memory_graph.text_nodes_by_clip[clip_id]
        for nid in node_ids:
            node = memory_graph.nodes.get(nid)
            if node:
                meta = getattr(node, 'metadata', {})
                contents = meta.get('contents', [])
                for c in contents:
                    if keyword.lower() in c.lower():
                        found_clips.append(clip_id)
                        break
    return list(set(found_clips))

def main():
    video_name = "kitchen_03"
    dataset = "robot"
    
    print("=" * 70)
    print("Phase 1 核心链路验证 - 选择 baseline 能回答的问题")
    print("=" * 70)
    
    # 加载图谱
    print("\n📥 加载图谱...")
    nstf_graph = load_nstf_graph(video_name, dataset)
    memory_graph = load_memory_graph(video_name, dataset)
    
    # 加载问题
    questions = load_questions(video_name, dataset)
    print(f"\n📝 共 {len(questions)} 个问题")
    
    # 显示所有问题并检查哪些能在 baseline 中找到答案
    print("\n" + "=" * 70)
    print("分析所有问题的可回答性")
    print("=" * 70)
    
    answerable_questions = []
    
    for i, q in enumerate(questions, 1):
        if isinstance(q, dict):
            question = q.get('question', '')
            answer = str(q.get('answer', ''))
        else:
            continue
        
        # 从答案中提取关键词
        answer_words = [w.strip('.,!?') for w in answer.split() if len(w) > 3]
        
        # 检查哪些关键词能在 baseline 中找到
        found_keywords = []
        for word in answer_words:
            clips = search_keyword_in_baseline(memory_graph, word)
            if clips:
                found_keywords.append((word, len(clips)))
        
        coverage = len(found_keywords) / len(answer_words) if answer_words else 0
        
        print(f"\n问题 {i}: {question[:80]}...")
        print(f"  答案: {answer}")
        print(f"  覆盖率: {coverage:.0%} ({len(found_keywords)}/{len(answer_words)} 关键词)")
        if found_keywords:
            print(f"  找到: {found_keywords[:5]}")
        
        if coverage >= 0.3:  # 至少 30% 覆盖率
            answerable_questions.append({
                'question': question,
                'answer': answer,
                'coverage': coverage,
                'found_keywords': found_keywords
            })
    
    print("\n" + "=" * 70)
    print(f"可回答的问题: {len(answerable_questions)} / {len(questions)}")
    print("=" * 70)
    
    # 对可回答的问题进行核心链路测试
    if not answerable_questions:
        print("❌ 没有找到可回答的问题")
        return
    
    # 选择覆盖率最高的问题
    best_q = max(answerable_questions, key=lambda x: x['coverage'])
    
    print(f"\n🧪 测试覆盖率最高的问题:")
    print(f"   问题: {best_q['question']}")
    print(f"   答案: {best_q['answer']}")
    print(f"   覆盖率: {best_q['coverage']:.0%}")
    
    # 测试 NSTF 检索
    print("\n" + "=" * 70)
    print("NSTF 检索测试")
    print("=" * 70)
    
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    
    # 对于每个找到的关键词，检查是否在 NSTF 的 episodic_links 中
    for keyword, _ in best_q['found_keywords'][:5]:
        # 1. 先找 baseline 中哪些 clips 有这个关键词
        baseline_clips = search_keyword_in_baseline(memory_graph, keyword)
        
        # 2. 检查这些 clips 是否被 NSTF 的 episodic_links 覆盖
        nstf_covered = []
        for proc_id, proc in proc_nodes.items():
            links = proc.get('episodic_links', [])
            linked_clips = [l.get('clip_id') for l in links]
            covered = [c for c in baseline_clips if c in linked_clips]
            if covered:
                nstf_covered.append((proc_id, covered))
        
        print(f"\n🔍 关键词: '{keyword}'")
        print(f"   Baseline clips: {baseline_clips[:10]}")
        if nstf_covered:
            print(f"   ✅ NSTF 覆盖:")
            for proc_id, clips in nstf_covered:
                goal = proc_nodes[proc_id].get('goal', '')[:50]
                print(f"      {proc_id} ({goal}...): clips {clips}")
        else:
            print(f"   ❌ NSTF 未覆盖")
    
    # 总结
    print("\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    
    # 计算 NSTF 对 baseline 的覆盖率
    all_linked_clips = set()
    for proc in proc_nodes.values():
        for link in proc.get('episodic_links', []):
            clip_id = link.get('clip_id')
            if isinstance(clip_id, int):
                all_linked_clips.add(clip_id)
    
    total_clips = len(memory_graph.text_nodes_by_clip)
    coverage = len(all_linked_clips) / total_clips * 100
    
    print(f"NSTF episodic_links 覆盖的 clips: {len(all_linked_clips)} / {total_clips} ({coverage:.1f}%)")
    print(f"Procedures 数量: {len(proc_nodes)}")
    print(f"平均 links/procedure: {len(all_linked_clips) / len(proc_nodes):.1f}")

if __name__ == "__main__":
    main()
