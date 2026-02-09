#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retrieval Weight (α) 超参数实验脚本 v2

这个脚本用于测试不同的 α 值对检索效果的影响。

α 参数控制 goal vs step 的检索权重:
  score(q, N) = α * sim(q, goal) + (1-α) * sim(q, step)

实验设计:
- 测试范围: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
- 每个 α 值运行相同的测试集
- 每个 α 的结果存入独立的输出文件

使用方法:
    cd /data1/rongjiej/NSTF_MODEL
    
    # 查看实验指南
    python scripts/experiment_alpha.py --guide
    
    # 1. 先设置 α 值
    python scripts/experiment_alpha.py --set-alpha 0.4
    
    # 2. 然后手动运行测试 (推荐方式)
    python experiments/run_qa.py --dataset robot --videos kitchen_09,kitchen_03,kitchen_22,gym_03 --output results/experiments/alpha_0.4.jsonl --force
    
    # 3. 测试完成后，分析所有结果
    python scripts/experiment_alpha.py --analyze
    
    # 4. 恢复默认值
    python scripts/experiment_alpha.py --restore
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 实验配置
ALPHA_VALUES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
TEST_VIDEOS = ['kitchen_09', 'kitchen_03', 'kitchen_22', 'gym_03']
RESULTS_DIR = PROJECT_ROOT / "results/experiments"


def get_current_alpha():
    """读取当前代码中的 alpha 值"""
    retriever_path = PROJECT_ROOT / "qa_system/core/hybrid_retriever.py"
    
    with open(retriever_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'def _search_procedures\([^)]*alpha:\s*float\s*=\s*([\d.]+)'
    match = re.search(pattern, content)
    
    if match:
        return float(match.group(1))
    return None


def set_alpha(alpha_value):
    """修改 hybrid_retriever.py 中的 alpha 默认值"""
    retriever_path = PROJECT_ROOT / "qa_system/core/hybrid_retriever.py"
    
    with open(retriever_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r'(def _search_procedures\([^)]*alpha:\s*float\s*=\s*)[\d.]+'
    new_content = re.sub(pattern, f'\\g<1>{alpha_value}', content)
    
    if new_content == content:
        print(f"⚠️ 警告: 未能找到并修改 alpha 值")
        return False
    
    with open(retriever_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ 已将 alpha 修改为 {alpha_value}")
    return True


def restore_alpha():
    """恢复 alpha 默认值为 0.3"""
    return set_alpha(0.3)


def analyze_jsonl_results(file_path):
    """分析单个 JSONL 结果文件"""
    if not file_path.exists():
        return None
    
    results = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    results.append(json.loads(line))
                except:
                    continue
    
    if not results:
        return None
    
    total = len(results)
    correct = len([r for r in results if r.get('gpt_eval') == True])
    
    # 按类型统计
    by_type = defaultdict(lambda: {'total': 0, 'correct': 0})
    for r in results:
        q_type = r.get('type_query', 'Unknown')
        by_type[q_type]['total'] += 1
        if r.get('gpt_eval') == True:
            by_type[q_type]['correct'] += 1
    
    # 效率统计
    rounds_list = [r.get('num_rounds', 0) for r in results if r.get('status') == 'success']
    searches_list = [r.get('search_count', 0) for r in results if r.get('status') == 'success']
    
    import numpy as np
    
    return {
        'total': total,
        'correct': correct,
        'accuracy': correct / total if total > 0 else 0,
        'by_type': dict(by_type),
        'avg_rounds': float(np.mean(rounds_list)) if rounds_list else 0,
        'avg_searches': float(np.mean(searches_list)) if searches_list else 0,
    }


def analyze_all_experiments():
    """分析所有实验结果"""
    print("="*80)
    print("📊 α 参数实验结果分析")
    print("="*80)
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for alpha in ALPHA_VALUES:
        file_path = RESULTS_DIR / f"alpha_{alpha}.jsonl"
        
        if not file_path.exists():
            print(f"  α={alpha}: 未找到结果文件")
            continue
        
        stats = analyze_jsonl_results(file_path)
        if stats:
            stats['alpha'] = alpha
            results.append(stats)
            print(f"  α={alpha}: {stats['correct']}/{stats['total']} = {stats['accuracy']:.2%}")
    
    if not results:
        print("\n❌ 没有找到任何实验结果")
        print(f"请将结果文件保存到: {RESULTS_DIR}/alpha_X.X.jsonl")
        return
    
    # 打印表格
    print(f"\n{'='*80}")
    print("📈 结果汇总表")
    print("="*80)
    
    print(f"\n| α 值 | 总数 | 正确 | 准确率 | 平均轮数 | 平均搜索 |")
    print(f"|------|------|------|--------|----------|----------|")
    
    for r in sorted(results, key=lambda x: x['alpha']):
        print(f"| {r['alpha']:.1f}  | {r['total']:4d} | {r['correct']:4d} | {r['accuracy']:.2%} | {r['avg_rounds']:.2f} | {r['avg_searches']:.2f} |")
    
    # 找到最优 α
    if results:
        best = max(results, key=lambda x: x['accuracy'])
        print(f"\n🏆 最优 α = {best['alpha']}, 准确率 = {best['accuracy']:.2%}")
        
        # 按类型分析
        print(f"\n{'='*80}")
        print("📊 按查询类型分析")
        print("="*80)
        
        for r in sorted(results, key=lambda x: x['alpha']):
            print(f"\nα = {r['alpha']}:")
            for q_type, stats in sorted(r['by_type'].items()):
                acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
                print(f"  {q_type}: {stats['correct']}/{stats['total']} = {acc:.2%}")
    
    # 保存汇总
    summary_file = RESULTS_DIR / "alpha_experiment_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 汇总已保存到: {summary_file}")


def print_experiment_guide():
    """打印实验指南"""
    current_alpha = get_current_alpha()
    
    print("="*80)
    print("🔬 Retrieval Weight (α) 超参数实验指南")
    print("="*80)
    
    print(f"\n当前 α 值: {current_alpha}")
    print(f"结果保存目录: {RESULTS_DIR}")
    
    # 检查已有结果
    existing = []
    for alpha in ALPHA_VALUES:
        file_path = RESULTS_DIR / f"alpha_{alpha}.jsonl"
        if file_path.exists():
            existing.append(alpha)
    
    if existing:
        print(f"已有结果: {existing}")
    else:
        print(f"已有结果: 无")
    
    videos_str = ','.join(TEST_VIDEOS)
    
    print(f"\n{'='*80}")
    print("【推荐实验步骤 - 手动逐个测试】")
    print("="*80)
    
    # 只显示还没有结果的 alpha 值
    remaining = [a for a in ALPHA_VALUES if a not in existing]
    if not remaining:
        remaining = ALPHA_VALUES
    
    for i, alpha in enumerate(remaining[:4], 1):  # 先只显示 4 个
        print(f"\n--- 实验 {i}: α = {alpha} ---")
        print(f"python scripts/experiment_alpha.py --set-alpha {alpha}")
        print(f"python experiments/run_qa.py --dataset robot --videos {videos_str} --output results/experiments/alpha_{alpha}.jsonl --force")
    
    print(f"\n--- 分析结果 ---")
    print(f"python scripts/experiment_alpha.py --analyze")
    
    print(f"\n--- 恢复默认 ---")
    print(f"python scripts/experiment_alpha.py --restore")
    
    print(f"\n{'='*80}")
    print("💡 提示: 每个实验大约需要 10-20 分钟，可以先测试 α=0.2, 0.3, 0.4, 0.5")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description="Retrieval Weight (α) 超参数实验",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--set-alpha', type=float, metavar='VALUE',
                        help='设置 α 值 (例如: --set-alpha 0.4)')
    parser.add_argument('--restore', action='store_true',
                        help='恢复 α 默认值为 0.3')
    parser.add_argument('--analyze', action='store_true',
                        help='分析所有实验结果')
    parser.add_argument('--guide', action='store_true',
                        help='打印实验指南')
    parser.add_argument('--status', action='store_true',
                        help='显示当前状态')
    
    args = parser.parse_args()
    
    # 默认显示指南
    if not any([args.set_alpha, args.restore, args.analyze, args.guide, args.status]):
        args.guide = True
    
    if args.status:
        current = get_current_alpha()
        print(f"当前 α 值: {current}")
        return
    
    if args.guide:
        print_experiment_guide()
        return
    
    if args.set_alpha is not None:
        set_alpha(args.set_alpha)
        videos_str = ','.join(TEST_VIDEOS)
        print(f"\n现在请运行测试:")
        print(f"python experiments/run_qa.py --dataset robot --videos {videos_str} --output results/experiments/alpha_{args.set_alpha}.jsonl --force")
        return
    
    if args.restore:
        restore_alpha()
        print("✅ 已恢复 α 默认值为 0.3")
        return
    
    if args.analyze:
        analyze_all_experiments()
        return


if __name__ == "__main__":
    main()
