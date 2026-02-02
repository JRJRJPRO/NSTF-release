#!/usr/bin/env python3
"""
验证重建的 NSTF 图谱
Phase 0 验证脚本 - 只输出关键统计信息
"""
import sys
import os
import pickle

sys.path.insert(0, '/data1/rongjiej/NSTF_MODEL')

def verify_graph(graph_path: str):
    """验证 NSTF 图谱"""
    print(f"\n{'='*60}")
    print(f"验证图谱: {graph_path}")
    print('='*60)
    
    if not os.path.exists(graph_path):
        print("❌ 文件不存在!")
        return False
    
    with open(graph_path, 'rb') as f:
        nstf_graph = pickle.load(f)
    
    # 1. 基本信息
    print(f"\n📊 基本信息:")
    print(f"  - video_name: {nstf_graph.get('video_name', 'N/A')}")
    print(f"  - dataset: {nstf_graph.get('dataset', 'N/A')}")
    
    # 2. Character 映射
    char_mapping = nstf_graph.get('character_mapping', {})
    print(f"\n👤 Character 映射: {len(char_mapping)} 个")
    for char_id, name in char_mapping.items():
        print(f"  - {char_id} → {name}")
    
    # 3. Procedure 节点统计
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    print(f"\n📝 Procedure 节点: {len(proc_nodes)} 个")
    
    total_links = 0
    total_steps = 0
    has_embedding = 0
    
    for proc_id, proc in proc_nodes.items():
        links = proc.get('episodic_links', [])
        steps = proc.get('steps', [])
        total_links += len(links)
        total_steps += len(steps)
        
        # 检查 embedding - 处理两种格式
        emb_data = proc.get('embeddings', {})
        if isinstance(emb_data, dict):
            emb = emb_data.get('goal_emb')
        elif isinstance(emb_data, list) and len(emb_data) > 0:
            emb = emb_data[0]  # 旧格式
        else:
            emb = None
        if emb is not None:
            has_embedding += 1
        
        print(f"\n  [{proc_id}]")
        print(f"    Goal: {proc.get('goal', 'N/A')[:80]}...")
        print(f"    Type: {proc.get('proc_type', 'N/A')}")
        print(f"    Steps: {len(steps)}")
        print(f"    Episodic Links: {len(links)}")
        print(f"    Has Embedding: {'✓' if emb is not None else '✗'}")
        
        # 显示 episodic_links 详情（不显示 content）
        if links:
            print(f"    Links detail:")
            for link in links[:5]:  # 最多显示 5 个
                clip_id = link.get('clip_id', 'N/A')
                relevance = link.get('relevance', 'N/A')
                sim = link.get('similarity', 0)
                print(f"      - clip_{clip_id} ({relevance}, sim={sim:.3f})")
            if len(links) > 5:
                print(f"      ... and {len(links)-5} more")
    
    # 4. 汇总统计
    print(f"\n📈 汇总统计:")
    print(f"  - 总 Procedures: {len(proc_nodes)}")
    print(f"  - 总 Steps: {total_steps}")
    print(f"  - 总 Episodic Links: {total_links}")
    print(f"  - 有 Embedding 的 Procedures: {has_embedding}/{len(proc_nodes)}")
    if proc_nodes:
        print(f"  - 平均 Links/Procedure: {total_links/len(proc_nodes):.1f}")
        print(f"  - 平均 Steps/Procedure: {total_steps/len(proc_nodes):.1f}")
    
    # 5. 质量检查
    print(f"\n🔍 质量检查:")
    issues = []
    
    if len(proc_nodes) == 0:
        issues.append("❌ 没有 Procedure 节点")
    
    if total_links == 0:
        issues.append("❌ 没有 Episodic Links")
    
    if has_embedding < len(proc_nodes):
        issues.append(f"⚠️ {len(proc_nodes) - has_embedding} 个 Procedure 缺少 embedding")
    
    if not char_mapping:
        issues.append("⚠️ 没有 Character 映射")
    
    # 检查是否有空 links 的 Procedure
    empty_link_procs = [pid for pid, p in proc_nodes.items() if not p.get('episodic_links')]
    if empty_link_procs:
        issues.append(f"⚠️ {len(empty_link_procs)} 个 Procedure 没有 episodic_links")
    
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  ✅ 所有检查通过!")
    
    return len(issues) == 0


def main():
    # 验证 kitchen_03
    graph_path = "/data1/rongjiej/NSTF_MODEL/data/nstf_graphs/robot/kitchen_03_nstf.pkl"
    verify_graph(graph_path)
    
    print("\n" + "="*60)
    print("验证完成")
    print("="*60)


if __name__ == "__main__":
    main()
