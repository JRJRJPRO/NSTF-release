# -*- coding: utf-8 -*-
"""
快速检查 NSTF 检索问题的诊断脚本

用法:
    cd /data1/rongjiej/NSTF_MODEL
    python scripts/debug/diagnose_nstf_issue.py
"""

import os
import sys
import pickle
import json
from pathlib import Path

# 设置环境
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from env_setup import setup_all
setup_all()


def diagnose():
    """诊断 NSTF 检索问题"""
    
    print("="*70)
    print("NSTF 检索问题诊断")
    print("="*70)
    
    # 1. 检查 NSTF 图谱内容
    nstf_path = project_root / 'data/nstf_graphs/robot/kitchen_03_nstf.pkl'
    print(f"\n[1] NSTF 图谱内容 ({nstf_path.name})")
    print("-"*50)
    
    with open(nstf_path, 'rb') as f:
        nstf = pickle.load(f)
    
    proc_nodes = nstf.get('procedure_nodes', {})
    print(f"Procedure 数量: {len(proc_nodes)}")
    
    for proc_id, proc in proc_nodes.items():
        print(f"\n  === {proc_id} ===")
        print(f"  Goal: {proc.get('goal', 'N/A')}")
        print(f"  Description: {proc.get('description', 'N/A')[:100] if proc.get('description') else 'N/A'}")
        
        steps = proc.get('steps', [])
        print(f"  Steps ({len(steps)}):")
        for i, step in enumerate(steps[:5], 1):
            if isinstance(step, dict):
                action = step.get('action', 'N/A')
                print(f"    {i}. {action[:80] if action else 'N/A'}")
        
        links = proc.get('episodic_links', [])
        print(f"  Episodic Links: {len(links)} 个")
        if links:
            for link in links[:3]:
                print(f"    - clip_id={link.get('clip_id')}, step_idx={link.get('step_idx')}")
    
    # 2. 检查 Memory 图谱中是否有 dishcloth 相关内容
    mem_path = project_root / 'data/memory_graphs/robot/kitchen_03.pkl'
    print(f"\n\n[2] Memory 图谱搜索 'dishcloth' ({mem_path.name})")
    print("-"*50)
    
    from mmagent.utils.general import load_video_graph
    
    graph = load_video_graph(str(mem_path))
    graph.refresh_equivalences()
    
    print(f"总节点数: {len(graph.nodes)}")
    print(f"Clips 数: {len(graph.text_nodes_by_clip)}")
    
    # 搜索 dishcloth
    dishcloth_found = []
    for node_id, node in graph.nodes.items():
        metadata = getattr(node, 'metadata', {})
        contents = metadata.get('contents', [])
        for content in contents:
            if 'dishcloth' in content.lower() or 'cloth' in content.lower() or 'wipe' in content.lower():
                clip_id = metadata.get('timestamp', 0)
                dishcloth_found.append({
                    'clip_id': clip_id,
                    'content': content[:150]
                })
    
    print(f"\n找到 'dishcloth/cloth/wipe' 相关内容: {len(dishcloth_found)} 条")
    for item in dishcloth_found[:5]:
        print(f"  [CLIP_{item['clip_id']}] {item['content']}")
    
    # 3. 测试 baseline 检索
    print(f"\n\n[3] Baseline 检索测试")
    print("-"*50)
    
    from mmagent.retrieve import search
    
    test_queries = [
        "What are wiped by the dishcloth?",
        "dishcloth usage",
        "wiping cloth",
        "What vegetables did Saxon and Tamera buy?",
    ]
    
    for query in test_queries:
        memories, clips, _ = search(
            graph, query, [],
            threshold=0.3,
            topk=10,
            before_clip=None
        )
        print(f"\n  Query: '{query}'")
        print(f"  Baseline 返回 clips: {list(memories.keys())[:5]}")
        if not memories:
            print(f"    ⚠️ 无结果!")
    
    # 4. 测试 NSTF 检索
    print(f"\n\n[4] NSTF 检索测试")
    print("-"*50)
    
    from qa_system.core.retriever_nstf import NSTFRetriever
    
    retriever = NSTFRetriever(
        threshold=0.30,
        min_confidence=0.25,
    )
    
    for query in test_queries[:2]:
        memories, clips, metadata = retriever.search(
            mem_path=str(mem_path),
            query=query,
            nstf_path=str(nstf_path),
        )
        print(f"\n  Query: '{query}'")
        print(f"  Decision: {metadata.get('decision')}")
        print(f"  Fallback reason: {metadata.get('fallback_reason', 'N/A')}")
        print(f"  Matched procedures: {metadata.get('matched_procedures', [])}")
        print(f"  Memories keys: {list(memories.keys())[:5]}")
    
    # 5. 结论
    print(f"\n\n{'='*70}")
    print("诊断结论")
    print("="*70)
    print("""
问题根源:
1. NSTF 图谱的 Procedure 内容过于抽象/简化
   - 只有 "Unpacking groceries" 这样的高层目标
   - 缺少具体细节（如 dishcloth, spinach 放哪里）

2. episodic_links 没有实际被利用
   - 即使匹配到 Procedure，也没有返回关联的原始 clip 内容
   - 导致 LLM 只看到抽象步骤，无法回答具体问题

3. NSTF 图谱构建时可能丢失了细节
   - 提取器可能只关注了高层任务，忽略了具体事实

建议修复方向:
A. 增强 episodic_links 的内容回溯（代码层面）
B. 改进 NSTF 图谱构建，保留更多细节（数据层面）
C. 当 NSTF 无法回答时，确保 fallback 到 baseline 能正常工作
""")


if __name__ == '__main__':
    diagnose()
