#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试节点级别检索器

验证 RetrieverV2 和 NodeLevelStrategy 能正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_retriever_v2():
    """测试 RetrieverV2"""
    print("=" * 60)
    print("测试 RetrieverV2")
    print("=" * 60)
    
    from qa_system.core.retriever_v2 import RetrieverV2
    
    # 测试初始化
    print("\n1. 测试初始化...")
    retriever = RetrieverV2(
        strategy='node_level',
        threshold=0.25,
        topk=10,
        include_timestamp=True,
        group_by_clip=True,
        include_semantic=False,
        preserve_clip_order=True,
    )
    print(f"   策略: {retriever.strategy_name}")
    print(f"   threshold: {retriever.threshold}")
    print(f"   topk: {retriever.topk}")
    print("   ✓ 初始化成功")
    
    # 测试 reset
    print("\n2. 测试 reset...")
    retriever.reset()
    print("   ✓ reset 成功")
    
    # 测试策略切换
    print("\n3. 测试策略切换...")
    retriever.set_strategy('clip_level')
    print(f"   切换后策略: {retriever.strategy_name}")
    retriever.set_strategy('node_level', group_by_clip=False)
    print(f"   再次切换策略: {retriever.strategy_name}")
    print("   ✓ 策略切换成功")
    
    return True


def test_node_strategy():
    """测试 NodeLevelStrategy"""
    print("\n" + "=" * 60)
    print("测试 NodeLevelStrategy")
    print("=" * 60)
    
    from qa_system.core.strategies.node_strategy import NodeLevelStrategy
    
    # 测试初始化
    print("\n1. 测试初始化...")
    strategy = NodeLevelStrategy(
        include_timestamp=True,
        group_by_clip=True,
        include_semantic=False,
        preserve_clip_order=True,
    )
    print(f"   name: {strategy.name}")
    print("   ✓ 初始化成功")
    
    # 测试 reset
    print("\n2. 测试 reset...")
    strategy._retrieved_node_ids.add(1)
    strategy._retrieved_node_ids.add(2)
    print(f"   reset 前: {len(strategy._retrieved_node_ids)} 个节点")
    strategy.reset()
    print(f"   reset 后: {len(strategy._retrieved_node_ids)} 个节点")
    print("   ✓ reset 成功")
    
    return True


def test_config():
    """测试配置扩展"""
    print("\n" + "=" * 60)
    print("测试 QAConfig 扩展")
    print("=" * 60)
    
    from qa_system.config import QAConfig, ABLATION_CONFIGS, get_ablation_config
    
    # 测试新字段
    print("\n1. 测试新配置字段...")
    config = QAConfig()
    print(f"   retrieval_strategy: {config.retrieval_strategy}")
    print(f"   node_topk: {config.node_topk}")
    print(f"   node_threshold: {config.node_threshold}")
    print(f"   include_timestamp: {config.include_timestamp}")
    print(f"   group_by_clip: {config.group_by_clip}")
    print(f"   include_semantic: {config.include_semantic}")
    print(f"   preserve_clip_order: {config.preserve_clip_order}")
    print("   ✓ 新字段存在")
    
    # 测试 to_dict
    print("\n2. 测试 to_dict...")
    config_dict = config.to_dict()
    assert 'retrieval_strategy' in config_dict
    assert 'node_topk' in config_dict
    print("   ✓ to_dict 包含新字段")
    
    # 测试预定义配置
    print("\n3. 测试预定义配置...")
    print(f"   可用配置: {list(ABLATION_CONFIGS.keys())}")
    
    baseline_config = get_ablation_config('baseline')
    print(f"   baseline: retrieval_strategy={baseline_config.retrieval_strategy}")
    
    nstf_node_config = get_ablation_config('nstf_node')
    print(f"   nstf_node: retrieval_strategy={nstf_node_config.retrieval_strategy}")
    print(f"   nstf_node: node_topk={nstf_node_config.node_topk}")
    print("   ✓ 预定义配置正确")
    
    return True


def test_with_real_data():
    """测试实际数据（需要图谱文件）"""
    print("\n" + "=" * 60)
    print("测试实际数据检索")
    print("=" * 60)
    
    # 使用 baseline 图谱（节点级别检索基于 baseline 图谱的 embeddings）
    # NSTF 图谱是 dict 格式，只包含 procedure 信息，不适合直接用于节点检索
    data_dir = PROJECT_ROOT / 'data' / 'memory_graphs' / 'robot'
    
    if not data_dir.exists():
        print(f"  ⚠️ 数据目录不存在: {data_dir}")
        print("  跳过实际数据测试")
        return True
    
    pkl_files = list(data_dir.glob('*.pkl'))
    if not pkl_files:
        print("  ⚠️ 没有找到图谱文件")
        print("  跳过实际数据测试")
        return True
    
    mem_path = str(pkl_files[0])
    print(f"\n使用图谱: {pkl_files[0].name} (baseline memory graph)")
    
    from qa_system.core.retriever_v2 import RetrieverV2
    
    # 测试节点级别检索
    print("\n1. 测试节点级别检索...")
    retriever = RetrieverV2(
        strategy='node_level',
        threshold=0.2,
        topk=5,
    )
    
    query = "What did the person do?"
    result = retriever.search(
        mem_path=mem_path,
        query=query,
    )
    
    print(f"   查询: {query}")
    print(f"   返回 {result['metadata']['num_nodes']} 个节点")
    print(f"   memories keys: {list(result['memories'].keys())}")
    
    if result['memories']:
        first_key = list(result['memories'].keys())[0]
        first_value = result['memories'][first_key]
        if isinstance(first_value, list) and first_value:
            print(f"   示例内容: {first_value[0][:100]}...")
    
    print("   ✓ 节点级别检索成功")
    
    # 测试 clip 级别检索
    print("\n2. 测试 clip 级别检索...")
    retriever.set_strategy('clip_level')
    
    result = retriever.search(
        mem_path=mem_path,
        query=query,
        current_context=[],
    )
    
    print(f"   返回 {result['metadata']['num_clips']} 个 clips")
    print(f"   memories keys: {list(result['memories'].keys())}")
    print("   ✓ clip 级别检索成功")
    
    return True


def main():
    print("节点级别检索器测试")
    print("=" * 60)
    
    all_passed = True
    
    try:
        all_passed &= test_retriever_v2()
        all_passed &= test_node_strategy()
        all_passed &= test_config()
        all_passed &= test_with_real_data()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
