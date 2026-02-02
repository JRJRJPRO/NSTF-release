#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Efficiency 实验 - 轮次分析脚本

分析 Baseline 和 NSTF 的问答轮次差异
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def count_rounds_from_conversations(conversations: list) -> int:
    """
    从 conversations 中统计轮次数
    
    轮次定义：assistant 的响应次数（即 LLM 调用次数）
    """
    return sum(1 for c in conversations if c.get('role') == 'assistant')


def count_search_rounds(conversations: list) -> int:
    """
    统计有效检索轮次（即 Search action 的次数）
    
    通过检查 user 消息中是否包含 "Searched knowledge:" 来判断
    """
    search_count = 0
    for c in conversations:
        if c.get('role') == 'user':
            content = c.get('content', '')
            if 'Searched knowledge:' in content and content != 'Searched knowledge: {}':
                search_count += 1
    # 减1因为初始 user 消息也包含空的 Searched knowledge
    return max(0, search_count)


def analyze_results(results_file: str) -> dict:
    """分析单个结果文件"""
    results_path = Path(results_file)
    if not results_path.exists():
        print(f"文件不存在: {results_file}")
        return None
    
    items = []
    with open(results_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    if not items:
        print(f"文件为空: {results_file}")
        return None
    
    # 统计
    total_rounds = 0
    total_search = 0
    total_correct = 0
    total_time = 0
    
    details = []
    for item in items:
        conversations = item.get('conversations', [])
        rounds = count_rounds_from_conversations(conversations)
        search = count_search_rounds(conversations)
        correct = item.get('gpt_eval', False)
        elapsed = item.get('elapsed_time_sec', 0)
        
        total_rounds += rounds
        total_search += search
        total_correct += 1 if correct else 0
        total_time += elapsed
        
        details.append({
            'id': item.get('id'),
            'video_id': item.get('video_id'),
            'rounds': rounds,
            'search_rounds': search,
            'correct': correct,
            'elapsed_time_sec': elapsed,
        })
    
    n = len(items)
    return {
        'total_questions': n,
        'avg_rounds': round(total_rounds / n, 2),
        'avg_search_rounds': round(total_search / n, 2),
        'accuracy': round(total_correct / n * 100, 2),
        'avg_time_sec': round(total_time / n, 2) if total_time > 0 else None,
        'details': details,
    }


def compare_results(baseline_file: str, nstf_file: str, output_file: str = None):
    """对比 Baseline 和 NSTF 结果"""
    
    print("="*60)
    print("Efficiency 实验 - 轮次分析报告")
    print("="*60)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    baseline_stats = analyze_results(baseline_file)
    nstf_stats = analyze_results(nstf_file)
    
    if not baseline_stats:
        print("Baseline 结果不可用")
        return
    if not nstf_stats:
        print("NSTF 结果不可用")
        return
    
    # 打印对比
    print(f"{'指标':<25} {'Baseline':>12} {'NSTF':>12} {'差异':>12}")
    print("-"*60)
    
    metrics = [
        ('问题总数', 'total_questions'),
        ('平均轮次', 'avg_rounds'),
        ('平均检索轮次', 'avg_search_rounds'),
        ('准确率 (%)', 'accuracy'),
    ]
    
    report = {
        'analysis_time': datetime.now().isoformat(),
        'baseline': {
            'file': str(baseline_file),
            **{k: baseline_stats[k] for k in ['total_questions', 'avg_rounds', 'avg_search_rounds', 'accuracy', 'avg_time_sec']}
        },
        'nstf': {
            'file': str(nstf_file),
            **{k: nstf_stats[k] for k in ['total_questions', 'avg_rounds', 'avg_search_rounds', 'accuracy', 'avg_time_sec']}
        },
        'comparison': {}
    }
    
    for name, key in metrics:
        b_val = baseline_stats[key]
        n_val = nstf_stats[key]
        
        if key in ['avg_rounds', 'avg_search_rounds']:
            # 轮次越少越好
            diff = b_val - n_val
            diff_str = f"+{diff:.2f}" if diff > 0 else f"{diff:.2f}"
            report['comparison'][f'{key}_reduction'] = round(diff, 2)
        elif key == 'accuracy':
            # 准确率越高越好
            diff = n_val - b_val
            diff_str = f"+{diff:.2f}%" if diff > 0 else f"{diff:.2f}%"
            report['comparison']['accuracy_improvement'] = round(diff, 2)
        else:
            diff_str = "-"
        
        print(f"{name:<25} {b_val:>12} {n_val:>12} {diff_str:>12}")
    
    # 添加时间对比（如果有）
    if baseline_stats.get('avg_time_sec') and nstf_stats.get('avg_time_sec'):
        b_time = baseline_stats['avg_time_sec']
        n_time = nstf_stats['avg_time_sec']
        diff = n_time - b_time
        diff_str = f"+{diff:.2f}s" if diff > 0 else f"{diff:.2f}s"
        print(f"{'平均耗时 (秒)':<25} {b_time:>12} {n_time:>12} {diff_str:>12}")
        report['comparison']['time_diff_sec'] = round(diff, 2)
    
    print("-"*60)
    
    # 按视频统计
    print("\n按视频统计:")
    print(f"{'视频':<20} {'Baseline 轮次':>15} {'NSTF 轮次':>15} {'差异':>10}")
    print("-"*60)
    
    # 构建按视频的统计
    baseline_by_video = defaultdict(lambda: {'rounds': 0, 'count': 0, 'correct': 0})
    nstf_by_video = defaultdict(lambda: {'rounds': 0, 'count': 0, 'correct': 0})
    
    for d in baseline_stats['details']:
        vid = d['video_id']
        baseline_by_video[vid]['rounds'] += d['rounds']
        baseline_by_video[vid]['count'] += 1
        baseline_by_video[vid]['correct'] += 1 if d['correct'] else 0
    
    for d in nstf_stats['details']:
        vid = d['video_id']
        nstf_by_video[vid]['rounds'] += d['rounds']
        nstf_by_video[vid]['count'] += 1
        nstf_by_video[vid]['correct'] += 1 if d['correct'] else 0
    
    video_comparison = []
    for vid in sorted(set(baseline_by_video.keys()) | set(nstf_by_video.keys())):
        b_data = baseline_by_video.get(vid, {'rounds': 0, 'count': 0})
        n_data = nstf_by_video.get(vid, {'rounds': 0, 'count': 0})
        
        b_avg = b_data['rounds'] / b_data['count'] if b_data['count'] > 0 else 0
        n_avg = n_data['rounds'] / n_data['count'] if n_data['count'] > 0 else 0
        diff = b_avg - n_avg
        
        diff_str = f"+{diff:.2f}" if diff > 0 else f"{diff:.2f}"
        print(f"{vid:<20} {b_avg:>15.2f} {n_avg:>15.2f} {diff_str:>10}")
        
        video_comparison.append({
            'video_id': vid,
            'baseline_avg_rounds': round(b_avg, 2),
            'nstf_avg_rounds': round(n_avg, 2),
            'rounds_reduction': round(diff, 2)
        })
    
    report['video_comparison'] = video_comparison
    
    print()
    print("="*60)
    print("结论:")
    
    rounds_reduction = report['comparison'].get('avg_rounds_reduction', 0)
    accuracy_improvement = report['comparison'].get('accuracy_improvement', 0)
    
    if rounds_reduction > 0:
        print(f"✓ NSTF 平均减少 {rounds_reduction:.2f} 个轮次 (效率提升)")
    elif rounds_reduction < 0:
        print(f"✗ NSTF 平均增加 {-rounds_reduction:.2f} 个轮次")
    else:
        print("  轮次数相同")
    
    if accuracy_improvement > 0:
        print(f"✓ NSTF 准确率提升 {accuracy_improvement:.2f}%")
    elif accuracy_improvement < 0:
        print(f"✗ NSTF 准确率下降 {-accuracy_improvement:.2f}%")
    else:
        print("  准确率相同")
    
    print("="*60)
    
    # 保存报告
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存: {output_file}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Efficiency 实验轮次分析')
    parser.add_argument('--baseline', type=str, 
                        default='experiments/efficiency/results/baseline_results.jsonl',
                        help='Baseline 结果文件')
    parser.add_argument('--nstf', type=str,
                        default='experiments/efficiency/results/nstf_results.jsonl',
                        help='NSTF 结果文件')
    parser.add_argument('--output', type=str,
                        default='experiments/efficiency/results/analysis_report.json',
                        help='分析报告输出路径')
    
    args = parser.parse_args()
    
    # 获取 NSTF_MODEL 根目录
    script_dir = Path(__file__).parent
    nstf_model_dir = script_dir.parent.parent.parent
    
    baseline_file = nstf_model_dir / args.baseline
    nstf_file = nstf_model_dir / args.nstf
    output_file = nstf_model_dir / args.output
    
    compare_results(str(baseline_file), str(nstf_file), str(output_file))


if __name__ == '__main__':
    main()
