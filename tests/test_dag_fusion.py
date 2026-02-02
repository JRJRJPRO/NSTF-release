# -*- coding: utf-8 -*-
"""
DAG Fusion 测试脚本

测试 DAG 融合功能是否正常工作
"""

import sys
import os

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_setup import setup_all
setup_all()

import numpy as np
from nstf_builder.dag_fusion import DAGFusion, ProcedureFusionManager


def create_test_procedure(proc_id: str, goal: str, steps: list, edges: list = None) -> dict:
    """创建测试用的 procedure"""
    from nstf_builder.utils import get_normalized_embedding
    
    # 生成 embedding
    emb = get_normalized_embedding(goal)
    
    return {
        'proc_id': proc_id,
        'type': 'procedure',
        'goal': goal,
        'description': f'Test procedure: {goal}',
        'steps': [
            {'step_id': f'step_{i+1}', 'action': action, 'triggers': [], 'outcomes': [], 
             'duration_seconds': 30, 'success_rate': 0.9}
            for i, action in enumerate(steps)
        ],
        'edges': edges or [
            {'from_step': f'step_{i+1}', 'to_step': f'step_{i+2}', 'probability': 1.0, 'condition': ''}
            for i in range(len(steps) - 1)
        ],
        'episodic_links': [{'clip_id': 1, 'relevance': 'source'}],
        'embeddings': {'goal_emb': emb},
        'metadata': {'source': 'test', 'fusion_count': 0}
    }


def test_should_fuse():
    """测试 should_fuse 函数"""
    print("\n=== Test: should_fuse ===")
    
    fusion = DAGFusion(debug=True)
    
    # 相似的 procedure 应该被识别为需要融合
    proc1 = create_test_procedure(
        'proc_1', 
        'Making breakfast: prepare eggs and toast',
        ['get eggs', 'crack eggs', 'cook eggs', 'make toast', 'serve']
    )
    
    proc2 = create_test_procedure(
        'proc_2',
        'Preparing breakfast meal with eggs',
        ['get ingredients', 'prepare eggs', 'cook food', 'plate it']
    )
    
    proc3 = create_test_procedure(
        'proc_3',
        'Fixing a car engine',
        ['open hood', 'diagnose problem', 'replace parts', 'test']
    )
    
    # proc1 和 proc2 应该融合
    should_fuse_12 = fusion.should_fuse(proc1, proc2)
    print(f"proc1 vs proc2 (similar breakfast): {should_fuse_12}")
    
    # proc1 和 proc3 不应该融合
    should_fuse_13 = fusion.should_fuse(proc1, proc3)
    print(f"proc1 vs proc3 (breakfast vs car): {should_fuse_13}")
    
    assert should_fuse_12 == True, "Similar procedures should fuse"
    assert should_fuse_13 == False, "Different procedures should not fuse"
    
    print("✓ should_fuse test passed!")


def test_step_alignment():
    """测试步骤对齐"""
    print("\n=== Test: Step Alignment ===")
    
    fusion = DAGFusion(similarity_threshold=0.7, debug=True)
    
    steps1 = [
        {'step_id': 'step_1', 'action': 'get the eggs from refrigerator'},
        {'step_id': 'step_2', 'action': 'crack the eggs into a bowl'},
        {'step_id': 'step_3', 'action': 'beat the eggs with a fork'},
        {'step_id': 'step_4', 'action': 'heat the pan'},
        {'step_id': 'step_5', 'action': 'cook the eggs'},
    ]
    
    steps2 = [
        {'step_id': 'step_1', 'action': 'take eggs from the fridge'},  # 应该匹配 step_1
        {'step_id': 'step_2', 'action': 'crack eggs'},  # 应该匹配 step_2
        {'step_id': 'step_3', 'action': 'stir eggs'},  # 应该匹配 step_3
        {'step_id': 'step_4', 'action': 'add salt and pepper'},  # 新步骤
        {'step_id': 'step_5', 'action': 'cook in hot pan'},  # 可能匹配 step_5
    ]
    
    alignment = fusion._align_steps(steps1, steps2)
    
    print(f"Matched pairs: {len(alignment['matched'])}")
    for idx1, idx2, sim in alignment['matched']:
        print(f"  {steps1[idx1]['action'][:30]} <-> {steps2[idx2]['action'][:30]} (sim: {sim:.3f})")
    
    print(f"Only in proc1: {alignment['only_proc1']}")
    print(f"Only in proc2: {alignment['only_proc2']}")
    
    assert len(alignment['matched']) >= 3, "Should match at least 3 similar steps"
    print("✓ Step alignment test passed!")


def test_full_fusion():
    """测试完整的融合流程"""
    print("\n=== Test: Full Fusion ===")
    
    fusion = DAGFusion(similarity_threshold=0.7, debug=True)
    
    proc1 = create_test_procedure(
        'proc_1',
        'Making scrambled eggs for breakfast',
        ['get eggs', 'crack eggs into bowl', 'beat eggs', 'heat pan', 'cook eggs', 'serve']
    )
    proc1['edges'] = [
        {'from_step': 'step_1', 'to_step': 'step_2', 'probability': 1.0, 'condition': ''},
        {'from_step': 'step_2', 'to_step': 'step_3', 'probability': 1.0, 'condition': ''},
        {'from_step': 'step_3', 'to_step': 'step_4', 'probability': 1.0, 'condition': ''},
        {'from_step': 'step_4', 'to_step': 'step_5', 'probability': 1.0, 'condition': ''},
        {'from_step': 'step_5', 'to_step': 'step_6', 'probability': 1.0, 'condition': ''},
    ]
    proc1['episodic_links'] = [{'clip_id': 1}, {'clip_id': 2}]
    
    proc2 = create_test_procedure(
        'proc_2',
        'Prepare eggs for breakfast',
        ['take eggs from fridge', 'crack them', 'whisk eggs', 'add salt', 'cook in pan']
    )
    proc2['edges'] = [
        {'from_step': 'step_1', 'to_step': 'step_2', 'probability': 1.0, 'condition': ''},
        {'from_step': 'step_2', 'to_step': 'step_3', 'probability': 1.0, 'condition': ''},
        {'from_step': 'step_3', 'to_step': 'step_4', 'probability': 0.8, 'condition': 'want flavor'},  # 可选步骤
        {'from_step': 'step_3', 'to_step': 'step_5', 'probability': 0.2, 'condition': 'skip seasoning'},  # 替代路径
        {'from_step': 'step_4', 'to_step': 'step_5', 'probability': 1.0, 'condition': ''},
    ]
    proc2['episodic_links'] = [{'clip_id': 5}, {'clip_id': 6}]
    
    # 执行融合
    fused = fusion.fuse(proc1, proc2)
    
    print(f"\nFused procedure:")
    print(f"  Goal: {fused['goal']}")
    print(f"  Steps: {len(fused['steps'])}")
    for step in fused['steps']:
        print(f"    - {step['step_id']}: {step['action'][:40]}")
    
    print(f"  Edges: {len(fused['edges'])}")
    for edge in fused['edges']:
        print(f"    - {edge['from_step']} -> {edge['to_step']} (p={edge['probability']:.2f})")
    
    print(f"  Episodic links: {len(fused['episodic_links'])}")
    print(f"  Fusion info: {fused['fusion_info']}")
    
    # 验证
    assert len(fused['steps']) >= 5, "Fused procedure should have at least 5 steps"
    assert len(fused['edges']) >= 5, "Fused procedure should preserve edges"
    assert len(fused['episodic_links']) == 4, "Should merge all episodic links"
    
    print("✓ Full fusion test passed!")


def test_fusion_manager():
    """测试 ProcedureFusionManager 批量融合"""
    print("\n=== Test: Fusion Manager ===")
    
    manager = ProcedureFusionManager(
        similarity_threshold=0.80,
        step_align_threshold=0.70,
        debug=True
    )
    
    # 创建测试数据
    procedure_nodes = {
        'video1_proc_1': create_test_procedure(
            'video1_proc_1',
            'Making breakfast with eggs',
            ['get eggs', 'cook eggs', 'serve']
        ),
        'video1_proc_2': create_test_procedure(
            'video1_proc_2',
            'Preparing eggs for morning meal',  # 应该与 proc_1 融合
            ['take eggs', 'prepare eggs', 'plate']
        ),
        'video1_proc_3': create_test_procedure(
            'video1_proc_3',
            'Fixing the car engine',  # 不应该融合
            ['open hood', 'check engine', 'fix it']
        ),
        'video1_proc_4': create_test_procedure(
            'video1_proc_4',
            'Repairing automobile motor',  # 应该与 proc_3 融合
            ['lift hood', 'diagnose', 'repair']
        ),
    }
    
    print(f"Before fusion: {len(procedure_nodes)} procedures")
    
    # 执行批量融合
    fused_nodes = manager.fuse_all(procedure_nodes)
    
    print(f"After fusion: {len(fused_nodes)} procedures")
    print(f"Stats: {manager.get_stats()}")
    
    for proc_id, proc in fused_nodes.items():
        print(f"\n  {proc_id}: {proc['goal'][:40]}")
        if 'fusion_info' in proc:
            print(f"    Fused from: {proc['fusion_info']['source_procs']}")
    
    # 验证
    assert len(fused_nodes) <= 3, "Should have at most 3 procedures after fusion"
    
    print("✓ Fusion manager test passed!")


def test_incremental_fusion():
    """测试增量融合"""
    print("\n=== Test: Incremental Fusion ===")
    
    manager = ProcedureFusionManager(
        similarity_threshold=0.75,
        debug=True
    )
    
    # 初始 procedures
    existing = {
        'proc_1': create_test_procedure(
            'proc_1',
            'Making coffee in the morning',
            ['boil water', 'add coffee grounds', 'pour water', 'serve']
        ),
    }
    
    # 新的相似 procedure
    new_similar = create_test_procedure(
        'proc_new',
        'Brewing morning coffee',
        ['heat water', 'prepare coffee', 'brew', 'drink']
    )
    
    # 新的不同 procedure
    new_different = create_test_procedure(
        'proc_diff',
        'Walking the dog',
        ['get leash', 'attach to dog', 'go outside', 'walk']
    )
    
    # 增量融合 - 相似的
    result1, was_fused1 = manager.incremental_fuse(existing, new_similar)
    print(f"After adding similar: {len(result1)} procedures, was_fused={was_fused1}")
    
    # 增量融合 - 不同的
    result2, was_fused2 = manager.incremental_fuse(result1, new_different)
    print(f"After adding different: {len(result2)} procedures, was_fused={was_fused2}")
    
    assert was_fused1 == True, "Similar procedure should be fused"
    assert was_fused2 == False, "Different procedure should not be fused"
    assert len(result2) == 2, "Should have 2 procedures total"
    
    print("✓ Incremental fusion test passed!")


if __name__ == '__main__':
    print("=" * 60)
    print("DAG Fusion Tests")
    print("=" * 60)
    
    try:
        test_should_fuse()
        test_step_alignment()
        test_full_fusion()
        test_fusion_manager()
        test_incremental_fusion()
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
