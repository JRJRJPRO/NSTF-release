#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NSTF 检索修复验证脚本

验证：
1. 多粒度检索加权组合是否正确实现
2. 字段名是否统一（step_emb vs steps_emb）
3. 检索分数是否符合预期范围
"""

import sys
import pickle
import numpy as np
from pathlib import Path

# 添加路径
NSTF_MODEL_DIR = Path(__file__).parent
sys.path.insert(0, str(NSTF_MODEL_DIR))

from env_setup import setup_all
setup_all()

from qa_system.core.retriever_nstf import NSTFRetriever


def test_multi_granularity_retrieval():
    """测试多粒度检索"""
    print("=" * 60)
    print("测试 1: 多粒度检索加权组合")
    print("=" * 60)
    
    # 加载图谱
    nstf_path = "data/nstf_graphs/robot/kitchen_03_nstf.pkl"
    if not Path(nstf_path).exists():
        print(f"❌ 找不到测试图谱: {nstf_path}")
        return False
    
    with open(nstf_path, 'rb') as f:
        nstf_graph = pickle.load(f)
    
    # 创建检索器
    retriever = NSTFRetriever(
        threshold=0.35,
        min_confidence=0.30,
    )
    
    # 测试查询
    test_query = "Where should the spinach be placed in the silver fridge?"
    
    print(f"\n查询: {test_query}")
    print(f"阈值: {retriever.threshold}")
    print(f"最低置信度: {retriever.min_confidence}")
    
    # 获取 Procedure embeddings
    proc_embeddings = retriever._get_procedure_embeddings(nstf_graph, nstf_path)
    
    print(f"\n加载的 Procedure 数量: {len(proc_embeddings)}")
    
    # 检查 embedding 字段
    first_proc_id = list(proc_embeddings.keys())[0]
    first_emb = proc_embeddings[first_proc_id]
    
    print(f"\nEmbedding 字段检查:")
    print(f"  - 包含 goal_emb: {'goal_emb' in first_emb}")
    print(f"  - 包含 step_emb: {'step_emb' in first_emb}")
    print(f"  - 包含 steps_emb (旧): {'steps_emb' in first_emb}")
    
    if 'goal_emb' not in first_emb or 'step_emb' not in first_emb:
        print("  ❌ Embedding 字段缺失！")
        return False
    
    # 执行检索
    matched_procs = retriever._search_procedures(test_query, proc_embeddings, alpha=0.3)
    
    print(f"\n检索结果:")
    print(f"  匹配数量: {len(matched_procs)}")
    
    if matched_procs:
        print(f"\nTop 3 匹配:")
        for i, proc in enumerate(matched_procs[:3], 1):
            print(f"  {i}. {proc['proc_id']}")
            print(f"     - 综合相似度: {proc['similarity']:.4f}")
            print(f"     - Goal 相似度: {proc.get('sim_goal', 0):.4f}")
            print(f"     - Step 相似度: {proc.get('sim_step', 0):.4f}")
            print(f"     - 匹配类型: {proc['match_type']}")
            
            # 验证加权公式
            alpha = 0.3
            expected = alpha * proc['sim_goal'] + (1 - alpha) * proc['sim_step']
            actual = proc['similarity']
            diff = abs(expected - actual)
            
            if diff < 0.0001:
                print(f"     ✅ 加权公式正确 (diff={diff:.6f})")
            else:
                print(f"     ❌ 加权公式错误! Expected={expected:.4f}, Actual={actual:.4f}")
                return False
        
        # 检查分数范围
        top_sim = matched_procs[0]['similarity']
        if top_sim < 0.35:
            print(f"\n⚠️ 警告: Top 相似度 {top_sim:.4f} 低于阈值 0.35")
        elif top_sim >= 0.5:
            print(f"\n✅ Top 相似度 {top_sim:.4f} 符合预期范围 (>= 0.5)")
        else:
            print(f"\n✅ Top 相似度 {top_sim:.4f} 在合理范围内 (>= 0.35)")
    else:
        print("  ⚠️ 没有匹配结果")
    
    return True


def test_field_compatibility():
    """测试字段兼容性"""
    print("\n" + "=" * 60)
    print("测试 2: 字段兼容性")
    print("=" * 60)
    
    # 模拟旧版本 embedding（使用 steps_emb）
    old_embeddings = {
        'proc_1': {
            'goal_emb': np.random.rand(3072),
            'steps_emb': np.random.rand(3072),  # 旧字段名
        }
    }
    
    # 模拟新版本 embedding（使用 step_emb）
    new_embeddings = {
        'proc_2': {
            'goal_emb': np.random.rand(3072),
            'step_emb': np.random.rand(3072),  # 新字段名
        }
    }
    
    retriever = NSTFRetriever()
    
    # 测试旧版本兼容性
    query = "test query"
    
    try:
        results_old = retriever._search_procedures(query, old_embeddings)
        print(f"✅ 旧字段 (steps_emb) 兼容: {len(results_old)} 个结果")
    except Exception as e:
        print(f"❌ 旧字段兼容失败: {e}")
        return False
    
    try:
        results_new = retriever._search_procedures(query, new_embeddings)
        print(f"✅ 新字段 (step_emb) 正常: {len(results_new)} 个结果")
    except Exception as e:
        print(f"❌ 新字段处理失败: {e}")
        return False
    
    return True


def main():
    """运行所有测试"""
    print("\n🔧 NSTF 检索修复验证\n")
    
    results = []
    
    # 测试 1: 多粒度检索
    try:
        success = test_multi_granularity_retrieval()
        results.append(("多粒度检索", success))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("多粒度检索", False))
    
    # 测试 2: 字段兼容性
    try:
        success = test_field_compatibility()
        results.append(("字段兼容性", success))
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("字段兼容性", False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！检索修复成功。")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查代码。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
