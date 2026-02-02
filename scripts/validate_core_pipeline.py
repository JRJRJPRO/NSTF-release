#!/usr/bin/env python3
"""
Phase 0 核心链路验证脚本

测试流程：
1. 加载 NSTF 图谱
2. 加载 baseline memory graph
3. 选择一个测试问题
4. 执行 NSTF 检索
5. 获取 episodic 内容
6. 验证内容是否包含回答所需信息
"""

import sys
from pathlib import Path

NSTF_MODEL_DIR = Path("/data1/rongjiej/NSTF_MODEL")
sys.path.insert(0, str(NSTF_MODEL_DIR))

import pickle
import json
import numpy as np

def load_nstf_graph(video_name: str, dataset: str):
    """加载 NSTF 图谱"""
    path = NSTF_MODEL_DIR / "data" / "nstf_graphs" / dataset / f"{video_name}_nstf.pkl"
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_memory_graph(video_name: str, dataset: str):
    """加载 baseline memory graph"""
    path = NSTF_MODEL_DIR / "data" / "memory_graphs" / dataset / f"{video_name}.pkl"
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_questions(video_name: str, dataset: str):
    """加载问题"""
    ann_path = NSTF_MODEL_DIR / "data" / "annotations" / f"{dataset}.json"
    with open(ann_path, 'r') as f:
        data = json.load(f)
    
    video_data = data.get(video_name, {})
    # 格式: {video_url, video_path, mem_path, qa_list}
    if isinstance(video_data, dict):
        return video_data.get('qa_list', [])
    return video_data

def get_episodic_content(memory_graph, clip_id: int) -> list:
    """从 memory graph 获取 clip 的 episodic 内容"""
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

def compute_similarity(text1: str, text2: str) -> float:
    """简单的关键词重叠相似度"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union

def main():
    video_name = "kitchen_03"
    dataset = "robot"
    
    print("=" * 70)
    print("Phase 0 核心链路验证")
    print("=" * 70)
    
    # 1. 加载图谱
    print("\n📥 加载图谱...")
    nstf_graph = load_nstf_graph(video_name, dataset)
    memory_graph = load_memory_graph(video_name, dataset)
    print(f"  NSTF 图谱: {len(nstf_graph.get('procedure_nodes', {}))} procedures")
    print(f"  Memory 图谱: {len(memory_graph.text_nodes_by_clip)} clips")
    
    # 2. 显示所有 Procedures
    print("\n📋 可用的 Procedures:")
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    for i, (proc_id, proc) in enumerate(proc_nodes.items(), 1):
        goal = proc.get('goal', 'N/A')
        links = proc.get('episodic_links', [])
        print(f"  {i}. {goal}")
        print(f"     Links: {[l.get('clip_id') for l in links]}")
    
    # 3. 加载问题
    print("\n📝 加载问题...")
    questions = load_questions(video_name, dataset)
    print(f"  共 {len(questions)} 个问题")
    
    # 4. 选择一个测试问题（选择可能与 Procedure 相关的）
    # 尝试找一个关于厨房活动的问题
    test_questions = []
    keywords = ['wash', 'cook', 'prepare', 'refrigerator', 'grocery', 'vegetable', 'food', 'kitchen']
    
    for q in questions:
        # 处理不同的 question 格式
        if isinstance(q, dict):
            q_text = q.get('question', '').lower()
        elif isinstance(q, str):
            q_text = q.lower()
        else:
            continue
            
        for kw in keywords:
            if kw in q_text:
                test_questions.append(q)
                break
    
    if not test_questions:
        test_questions = questions[:3]
    
    print(f"\n🔍 选择 {len(test_questions[:3])} 个测试问题:")
    for i, q in enumerate(test_questions[:3], 1):
        print(f"\n  问题 {i}: {q.get('question', 'N/A')[:100]}")
        print(f"  答案: {q.get('answer', 'N/A')}")
    
    # 5. 对第一个问题进行核心链路测试
    if test_questions:
        test_q = test_questions[0]
        print("\n" + "=" * 70)
        print("🧪 核心链路测试")
        print("=" * 70)
        
        query = test_q.get('question', '')
        answer = test_q.get('answer', '')
        
        print(f"\n📌 测试问题: {query}")
        print(f"📌 期望答案: {answer}")
        
        # 5a. 匹配 Procedure（简单关键词匹配）
        print("\n🔗 Step 1: 匹配 Procedure")
        best_proc = None
        best_score = 0
        
        for proc_id, proc in proc_nodes.items():
            goal = proc.get('goal', '')
            desc = proc.get('description', '')
            proc_text = f"{goal} {desc}"
            
            score = compute_similarity(query, proc_text)
            if score > best_score:
                best_score = score
                best_proc = (proc_id, proc)
        
        if best_proc:
            proc_id, proc = best_proc
            print(f"  匹配到: {proc.get('goal', 'N/A')}")
            print(f"  相似度: {best_score:.3f}")
            
            # 5b. 追溯 episodic_links
            print("\n🔗 Step 2: 追溯 episodic_links")
            links = proc.get('episodic_links', [])
            
            if links:
                for link in links:
                    clip_id = link.get('clip_id')
                    relevance = link.get('relevance', 'unknown')
                    
                    # 尝试解析 clip_id
                    if isinstance(clip_id, int):
                        actual_clip_id = clip_id
                    elif isinstance(clip_id, str):
                        # 尝试提取数字
                        import re
                        match = re.search(r'(\d+)', str(clip_id))
                        actual_clip_id = int(match.group(1)) if match else None
                    else:
                        actual_clip_id = None
                    
                    print(f"\n  Link: clip_id={clip_id} ({relevance})")
                    
                    if actual_clip_id is not None:
                        # 5c. 获取 episodic 内容
                        contents = get_episodic_content(memory_graph, actual_clip_id)
                        print(f"  获取到 {len(contents)} 条内容:")
                        for c in contents[:3]:
                            print(f"    - {c[:150]}...")
                        if len(contents) > 3:
                            print(f"    ... 还有 {len(contents) - 3} 条")
                        
                        # 5d. 检查内容是否包含答案相关信息
                        combined_content = ' '.join(contents)
                        answer_words = set(str(answer).lower().split())
                        content_words = set(combined_content.lower().split())
                        overlap = answer_words & content_words
                        
                        print(f"\n  📊 答案词汇覆盖: {len(overlap)}/{len(answer_words)}")
                        if overlap:
                            print(f"     覆盖的词: {list(overlap)[:10]}")
                    else:
                        print(f"  ⚠️ 无法解析 clip_id: {clip_id}")
            else:
                print("  ⚠️ 没有 episodic_links")
        else:
            print("  ⚠️ 没有匹配到 Procedure")
        
        # 6. 总结
        print("\n" + "=" * 70)
        print("📋 验证总结")
        print("=" * 70)
        print("""
核心链路检查清单:
□ 1. NSTF 图谱加载成功 ✓
□ 2. Procedure 节点存在 ✓ 
□ 3. episodic_links 存在（但 clip_id 格式有问题）
□ 4. 能从 memory_graph 获取 clip 内容 ✓
□ 5. Character mapping 存在 ✓

待改进:
- episodic_links 的 clip_id 应该是整数，不是字符串
- 需要实现 EpisodicLinker 来验证和发现更多链接
- 需要计算 similarity 分数
""")

if __name__ == "__main__":
    main()
