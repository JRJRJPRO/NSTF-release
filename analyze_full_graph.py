#!/usr/bin/env python
"""彻底分析 NSTF 图谱结构"""

import pickle
import json
from collections import Counter

def analyze_graph(nstf_path, mem_path):
    """完整分析图谱结构"""
    
    print("=" * 80)
    print("NSTF 图谱完整分析")
    print("=" * 80)
    
    # 加载图谱
    with open(nstf_path, 'rb') as f:
        nstf_graph = pickle.load(f)
    
    with open(mem_path, 'rb') as f:
        video_graph = pickle.load(f)
    
    print(f"\n### 1. NSTF 图谱顶层结构")
    print(f"Keys: {list(nstf_graph.keys())}")
    
    for key, value in nstf_graph.items():
        if isinstance(value, dict):
            print(f"  {key}: dict with {len(value)} items")
        elif isinstance(value, list):
            print(f"  {key}: list with {len(value)} items")
        else:
            print(f"  {key}: {type(value).__name__} = {value}")
    
    # 分析 procedure_nodes
    print(f"\n### 2. Procedure Nodes 详细分析")
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    print(f"总共 {len(proc_nodes)} 个 Procedure")
    
    # 统计每个字段的情况
    field_stats = {
        'has_goal': 0,
        'has_context': 0,
        'has_steps': 0,
        'has_episodic_links': 0,
        'has_participants': 0,
        'has_proc_type': 0,
        'steps_count': [],
        'episodic_count': [],
    }
    
    all_fields = Counter()
    
    for proc_id, proc in proc_nodes.items():
        # 统计所有字段
        for key in proc.keys():
            all_fields[key] += 1
        
        if proc.get('goal'):
            field_stats['has_goal'] += 1
        if proc.get('context'):
            field_stats['has_context'] += 1
        steps = proc.get('steps', [])
        if steps:
            field_stats['has_steps'] += 1
        field_stats['steps_count'].append(len(steps))
        
        episodic = proc.get('episodic_links', [])
        if episodic:
            field_stats['has_episodic_links'] += 1
        field_stats['episodic_count'].append(len(episodic))
        
        if proc.get('participants'):
            field_stats['has_participants'] += 1
        if proc.get('proc_type'):
            field_stats['has_proc_type'] += 1
    
    print(f"\n所有字段统计:")
    for field, count in all_fields.most_common():
        print(f"  {field}: {count}/{len(proc_nodes)}")
    
    print(f"\n字段填充率:")
    print(f"  有 goal: {field_stats['has_goal']}/{len(proc_nodes)}")
    print(f"  有 context: {field_stats['has_context']}/{len(proc_nodes)}")
    print(f"  有 steps (非空): {field_stats['has_steps']}/{len(proc_nodes)}")
    print(f"  有 episodic_links (非空): {field_stats['has_episodic_links']}/{len(proc_nodes)}")
    print(f"  有 participants: {field_stats['has_participants']}/{len(proc_nodes)}")
    print(f"  有 proc_type: {field_stats['has_proc_type']}/{len(proc_nodes)}")
    
    print(f"\nsteps 数量分布: min={min(field_stats['steps_count'])}, max={max(field_stats['steps_count'])}, avg={sum(field_stats['steps_count'])/len(field_stats['steps_count']):.1f}")
    print(f"episodic_links 数量分布: min={min(field_stats['episodic_count'])}, max={max(field_stats['episodic_count'])}, avg={sum(field_stats['episodic_count'])/len(field_stats['episodic_count']):.1f}")
    
    # 展示几个完整的 Procedure 示例
    print(f"\n### 3. Procedure 完整示例 (前3个)")
    for i, (proc_id, proc) in enumerate(list(proc_nodes.items())[:3]):
        print(f"\n--- {proc_id} ---")
        print(json.dumps(proc, indent=2, ensure_ascii=False, default=str))
    
    # 分析 episodic_links 的质量
    print(f"\n### 4. Episodic Links 详细分析")
    all_clip_ids = set()
    link_similarities = []
    
    for proc_id, proc in proc_nodes.items():
        episodic = proc.get('episodic_links', [])
        for link in episodic:
            clip_id = link.get('clip_id')
            if clip_id is not None:
                all_clip_ids.add(int(clip_id))
            sim = link.get('similarity', 0)
            link_similarities.append(sim)
    
    print(f"引用的 clip IDs: {sorted(all_clip_ids)}")
    print(f"总共 {len(all_clip_ids)} 个不同的 clip 被引用")
    
    if link_similarities:
        print(f"相似度统计: min={min(link_similarities):.2f}, max={max(link_similarities):.2f}, avg={sum(link_similarities)/len(link_similarities):.2f}")
    
    # 检查 video_graph 中的 clip 数量
    print(f"\n### 5. Video Graph 分析")
    if hasattr(video_graph, 'text_nodes_by_clip'):
        total_clips = len(video_graph.text_nodes_by_clip)
        print(f"Video Graph 中总共有 {total_clips} 个 clips")
        print(f"NSTF 引用了 {len(all_clip_ids)}/{total_clips} 个 clips ({len(all_clip_ids)/total_clips*100:.1f}%)")
    
    # 检查其他图谱结构
    print(f"\n### 6. 其他图谱结构")
    for key in nstf_graph.keys():
        if key != 'procedure_nodes':
            value = nstf_graph[key]
            print(f"\n{key}:")
            if isinstance(value, dict):
                if len(value) <= 5:
                    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))
                else:
                    print(f"  (dict with {len(value)} items)")
                    for k in list(value.keys())[:3]:
                        print(f"  Sample - {k}: {str(value[k])[:100]}...")
            elif isinstance(value, list):
                if len(value) <= 5:
                    print(f"  {value}")
                else:
                    print(f"  (list with {len(value)} items)")
                    print(f"  Sample: {value[:3]}")
            else:
                print(f"  {value}")
    
    # 检查是否有 DAG 边
    print(f"\n### 7. DAG 结构分析")
    edges = nstf_graph.get('edges', [])
    if edges:
        print(f"总共 {len(edges)} 条边")
        print(f"示例边: {edges[:5]}")
    else:
        print("没有找到 edges!")
    
    # 检查是否有 alternative_paths
    alt_paths = nstf_graph.get('alternative_paths', {})
    if alt_paths:
        print(f"\nalternative_paths: {len(alt_paths)} 个")
    else:
        print("\n没有找到 alternative_paths!")
    
    # 针对具体问题分析
    print(f"\n### 8. 关键问题分析")
    print("\n问题 Q10: 'Where does the robot get the seasoning bottle from?'")
    print("正确答案: In the cabinet (红柜子)")
    print("\n检查是否有相关 Procedure:")
    
    keywords_q10 = ['season', 'bottle', 'cabinet', 'get', 'take']
    for proc_id, proc in proc_nodes.items():
        goal = proc.get('goal', '').lower()
        context = proc.get('context', '').lower()
        text = f"{goal} {context}"
        if any(k in text for k in keywords_q10):
            print(f"  可能相关: {proc_id}")
            print(f"    Goal: {proc.get('goal')}")
            print(f"    Context: {proc.get('context')[:100] if proc.get('context') else 'N/A'}...")
    
    print("\n问题 Q03: 'Where did the robot throw the expired ingredients?'")
    print("正确答案: The dust bin (垃圾桶)")
    print("\n检查是否有相关 Procedure:")
    
    keywords_q03 = ['throw', 'trash', 'bin', 'dust', 'expired', 'garbage', 'waste', 'dispose']
    for proc_id, proc in proc_nodes.items():
        goal = proc.get('goal', '').lower()
        context = proc.get('context', '').lower()
        text = f"{goal} {context}"
        if any(k in text for k in keywords_q03):
            print(f"  可能相关: {proc_id}")
            print(f"    Goal: {proc.get('goal')}")
            print(f"    Context: {proc.get('context')[:100] if proc.get('context') else 'N/A'}...")

if __name__ == '__main__':
    nstf_path = "/data1/rongjiej/NSTF_MODEL/data/nstf_graphs/robot/kitchen_03_nstf_incremental.pkl"
    mem_path = "/data1/rongjiej/NSTF_MODEL/data/memory_graphs/robot/kitchen_03.pkl"
    analyze_graph(nstf_path, mem_path)
