# -*- coding: utf-8 -*-
"""
检查 NSTF 图谱结构和内容

用法:
    cd /data1/rongjiej/NSTF_MODEL
    python scripts/debug/check_nstf_graph.py --video kitchen_03 --dataset robot
"""

import os
import sys
import pickle
import argparse
from pathlib import Path

# 设置环境
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from env_setup import setup_all
setup_all()


def check_nstf_graph(nstf_path: str):
    """检查 NSTF 图谱结构"""
    print(f"=== 检查 NSTF 图谱 ===")
    print(f"路径: {nstf_path}")
    
    if not os.path.exists(nstf_path):
        print(f"❌ 文件不存在!")
        return
    
    with open(nstf_path, 'rb') as f:
        graph = pickle.load(f)
    
    print(f"\n图谱类型: {type(graph)}")
    
    if isinstance(graph, dict):
        print(f"顶层键: {list(graph.keys())}")
        
        # 检查 procedure_nodes
        if 'procedure_nodes' in graph:
            proc_nodes = graph['procedure_nodes']
            print(f"\n=== procedure_nodes ===")
            print(f"数量: {len(proc_nodes)}")
            
            for proc_id, proc in list(proc_nodes.items())[:3]:
                print(f"\n  --- {proc_id} ---")
                print(f"  keys: {list(proc.keys()) if isinstance(proc, dict) else type(proc)}")
                if isinstance(proc, dict):
                    print(f"  goal: {proc.get('goal', 'N/A')[:100] if proc.get('goal') else 'N/A'}")
                    steps = proc.get('steps', [])
                    print(f"  steps数量: {len(steps)}")
                    if steps and len(steps) > 0:
                        step = steps[0]
                        if isinstance(step, dict):
                            print(f"  step[0] keys: {list(step.keys())}")
                            print(f"  step[0] action: {step.get('action', 'N/A')[:80] if step.get('action') else 'N/A'}")
                    
                    links = proc.get('episodic_links', [])
                    print(f"  episodic_links数量: {len(links)}")
                    if links:
                        print(f"  episodic_links[0]: {links[0]}")
        else:
            print(f"\n❌ 没有 'procedure_nodes' 键!")
            print(f"  可能的键: {list(graph.keys())[:10]}")
        
        # 检查其他常见键
        for key in ['nodes', 'edges', 'metadata', 'video_info']:
            if key in graph:
                val = graph[key]
                print(f"\n=== {key} ===")
                if isinstance(val, dict):
                    print(f"  数量: {len(val)}")
                    if len(val) > 0:
                        first_key = list(val.keys())[0]
                        print(f"  示例键: {first_key}")
                        first_val = val[first_key]
                        if isinstance(first_val, dict):
                            print(f"  示例值的keys: {list(first_val.keys())[:10]}")
                elif isinstance(val, list):
                    print(f"  数量: {len(val)}")
                    if len(val) > 0:
                        print(f"  示例: {val[0]}")
    else:
        print(f"图谱不是 dict，而是: {type(graph)}")
        if hasattr(graph, '__dict__'):
            print(f"属性: {list(graph.__dict__.keys())[:20]}")


def check_memory_graph(mem_path: str):
    """检查 Memory 图谱结构"""
    print(f"\n\n=== 检查 Memory 图谱 ===")
    print(f"路径: {mem_path}")
    
    if not os.path.exists(mem_path):
        print(f"❌ 文件不存在!")
        return
    
    from mmagent.utils.general import load_video_graph
    
    graph = load_video_graph(mem_path)
    graph.refresh_equivalences()
    
    print(f"\n类型: {type(graph)}")
    print(f"nodes数量: {len(graph.nodes) if hasattr(graph, 'nodes') else 'N/A'}")
    
    if hasattr(graph, 'text_nodes_by_clip'):
        print(f"clips数量: {len(graph.text_nodes_by_clip)}")
        if graph.text_nodes_by_clip:
            clip_id = list(graph.text_nodes_by_clip.keys())[0]
            print(f"示例 clip_{clip_id}: {len(graph.text_nodes_by_clip[clip_id])} 个节点")


def test_nstf_retrieval(nstf_path: str, mem_path: str, query: str):
    """测试 NSTF 检索"""
    print(f"\n\n=== 测试 NSTF 检索 ===")
    print(f"Query: {query}")
    
    from qa_system.core.retriever_nstf import NSTFRetriever
    
    retriever = NSTFRetriever(
        threshold=0.30,
        min_confidence=0.25,
    )
    
    memories, clips, metadata = retriever.search(
        mem_path=mem_path,
        query=query,
        nstf_path=nstf_path,
    )
    
    print(f"\n检索结果:")
    print(f"  decision: {metadata.get('decision')}")
    print(f"  fallback_reason: {metadata.get('fallback_reason', 'N/A')}")
    print(f"  matched_procedures: {metadata.get('matched_procedures', [])}")
    print(f"  memories keys: {list(memories.keys())[:5]}")
    print(f"  clips: {clips[:5]}")
    
    if memories:
        for key, val in list(memories.items())[:2]:
            print(f"\n  {key}:")
            if isinstance(val, str):
                print(f"    {val[:500]}...")
            else:
                print(f"    {val}")


def main():
    parser = argparse.ArgumentParser(description="检查 NSTF 图谱")
    parser.add_argument('--video', type=str, default='kitchen_03', help='视频ID')
    parser.add_argument('--dataset', type=str, default='robot', choices=['robot', 'web'], help='数据集')
    parser.add_argument('--query', type=str, default='What are wiped by the dishcloth?', help='测试查询')
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent.parent.parent / 'data'
    nstf_path = base_dir / 'nstf_graphs' / args.dataset / f'{args.video}_nstf.pkl'
    mem_path = base_dir / 'memory_graphs' / args.dataset / f'{args.video}.pkl'
    
    # 检查 NSTF 图谱
    check_nstf_graph(str(nstf_path))
    
    # 检查 Memory 图谱
    check_memory_graph(str(mem_path))
    
    # 测试检索
    if nstf_path.exists() and mem_path.exists():
        test_nstf_retrieval(str(nstf_path), str(mem_path), args.query)


if __name__ == '__main__':
    main()
