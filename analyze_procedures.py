#!/usr/bin/env python
"""分析 NSTF 图谱中的 Procedure 与问题的匹配情况"""

import pickle
import sys
sys.path.insert(0, '/data1/rongjiej/NSTF_MODEL')

from sentence_transformers import SentenceTransformer
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def main():
    nstf_path = "/data1/rongjiej/NSTF_MODEL/data/nstf_graphs/robot/kitchen_03_nstf_incremental.pkl"
    
    # 要分析的问题
    questions = [
        "Where does the robot get the seasoning bottle from?",  # Q10
        "Where did the robot throw the expired ingredients?",   # Q03
        "How to get the seasoning bottle",
        "seasoning bottle cabinet",
        "expired ingredients trash bin dust bin",
        "throw away expired food",
    ]
    
    print("Loading NSTF graph...")
    with open(nstf_path, 'rb') as f:
        nstf_graph = pickle.load(f)
    
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    
    print(f"\n{'='*60}")
    print("所有 Procedure 的 Goal 和 Context:")
    print('='*60)
    
    for proc_id, proc in proc_nodes.items():
        goal = proc.get('goal', 'N/A')
        context = proc.get('context', '')[:80]
        steps = proc.get('steps', [])
        episodic = proc.get('episodic_links', [])
        
        # 检查是否包含关键词
        keywords = ['season', 'bottle', 'cabinet', 'trash', 'dust', 'bin', 'expired', 'throw']
        text_to_check = f"{goal} {context}".lower()
        matches = [k for k in keywords if k in text_to_check]
        
        print(f"\n{proc_id}:")
        print(f"  Goal: {goal}")
        print(f"  Context: {context}...")
        print(f"  Steps: {len(steps)}, Episodic links: {len(episodic)}")
        if matches:
            print(f"  *** 关键词匹配: {matches} ***")
    
    # 加载 embedding 模型计算相似度
    print(f"\n{'='*60}")
    print("计算 Query 与 Procedure 的相似度:")
    print('='*60)
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 获取所有 procedure 的 embedding
    proc_texts = []
    proc_ids = []
    for proc_id, proc in proc_nodes.items():
        goal = proc.get('goal', '')
        context = proc.get('context', '')
        combined = f"{goal}. {context}"
        proc_texts.append(combined)
        proc_ids.append(proc_id)
    
    proc_embeddings = model.encode(proc_texts)
    
    for query in questions:
        print(f"\nQuery: {query}")
        query_emb = model.encode([query])[0]
        
        sims = []
        for i, proc_emb in enumerate(proc_embeddings):
            sim = cosine_similarity(query_emb, proc_emb)
            sims.append((proc_ids[i], sim, proc_texts[i][:60]))
        
        sims.sort(key=lambda x: x[1], reverse=True)
        
        print("  Top 5 matches:")
        for pid, sim, text in sims[:5]:
            print(f"    {sim:.3f} - {pid}: {text}...")

if __name__ == '__main__':
    main()
