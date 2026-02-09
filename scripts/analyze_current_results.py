#!/usr/bin/env python3
"""
分析当前NSTF实验结果
基于已有的index_robot.jsonl和实验数据，评估当前threshold的表现
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

# 项目路径
project_root = Path(__file__).parent.parent
results_dir = project_root / "results/nstf"

def load_results(dataset='robot'):
    """加载实验结果"""
    index_file = results_dir / f"index_{dataset}.jsonl"
    
    if not index_file.exists():
        print(f"❌ 结果文件不存在: {index_file}")
        return []
    
    results = []
    with open(index_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    
    return results

def analyze_results(results):
    """分析实验结果"""
    
    print(f"\n{'='*80}")
    print(f"NSTF 实验结果分析")
    print(f"{'='*80}")
    
    # 基本统计
    total = len(results)
    success = len([r for r in results if r.get('status') == 'success'])
    
    print(f"\n📊 基本统计:")
    print(f"  总问题数: {total}")
    print(f"  成功数: {success}")
    print(f"  成功率: {success/total*100:.1f}%")
    
    # 按视频统计
    by_video = defaultdict(list)
    for r in results:
        video_id = r.get('video_id', 'unknown')
        by_video[video_id].append(r)
    
    print(f"\n📹 按视频分组:")
    for video_id, video_results in sorted(by_video.items()):
        video_total = len(video_results)
        video_success = len([r for r in video_results if r.get('status') == 'success'])
        video_correct = len([r for r in video_results if r.get('gpt_eval') == True])
        
        print(f"\n  {video_id}:")
        print(f"    问题数: {video_total}")
        print(f"    成功数: {video_success}")
        print(f"    正确数: {video_correct}")
        print(f"    准确率: {video_correct/video_total*100:.1f}%")
    
    # 按查询类型统计
    by_type = defaultdict(list)
    for r in results:
        q_type = r.get('type_query', 'Unknown')
        by_type[q_type].append(r)
    
    print(f"\n🔍 按查询类型分组:")
    for q_type, type_results in sorted(by_type.items()):
        type_total = len(type_results)
        type_correct = len([r for r in type_results if r.get('gpt_eval') == True])
        
        print(f"\n  {q_type}:")
        print(f"    问题数: {type_total}")
        print(f"    正确数: {type_correct}")
        print(f"    准确率: {type_correct/type_total*100:.1f}%" if type_total > 0 else "    准确率: N/A")
    
    # 检索效率统计
    rounds = [r.get('num_rounds', 0) for r in results if r.get('status') == 'success']
    searches = [r.get('search_count', 0) for r in results if r.get('status') == 'success']
    times = [r.get('elapsed_time_sec', 0) for r in results if r.get('status') == 'success']
    
    print(f"\n⚡ 检索效率:")
    print(f"  平均轮数: {np.mean(rounds):.2f} ± {np.std(rounds):.2f}")
    print(f"  平均搜索次数: {np.mean(searches):.2f} ± {np.std(searches):.2f}")
    print(f"  平均耗时: {np.mean(times):.2f}秒 ± {np.std(times):.2f}秒")
    
    # 分析search_count = 0的情况
    zero_search = [r for r in results if r.get('search_count', 0) == 0 and r.get('status') == 'success']
    print(f"\n  零搜索情况 (可能直接回答或出错):")
    print(f"    数量: {len(zero_search)}")
    print(f"    占比: {len(zero_search)/success*100:.1f}%")
    
    return {
        'total': total,
        'success': success,
        'accuracy': success/total if total > 0 else 0,
        'by_video': dict(by_video),
        'by_type': dict(by_type),
        'efficiency': {
            'avg_rounds': float(np.mean(rounds)) if rounds else 0,
            'avg_searches': float(np.mean(searches)) if searches else 0,
            'avg_time': float(np.mean(times)) if times else 0
        }
    }

def compare_with_baseline():
    """
    与Baseline对比分析
    
    注意：根据NSTF_EXPERIMENT_GUIDE.md，之前的baseline准确率约50%
    """
    print(f"\n{'='*80}")
    print(f"📊 与Baseline对比")
    print(f"{'='*80}")
    
    print(f"\n参考值 (来自NSTF_EXPERIMENT_GUIDE.md):")
    print(f"  Baseline准确率: ~50%")
    print(f"  之前5题测试(未正确集成NSTF): 60% (无统计意义)")
    
    print(f"\n预期改进:")
    print(f"  NSTF应该在程序性问题(Procedural)上有明显提升")
    print(f"  Factual问题可能与baseline相当")
    print(f"  Constrained问题应该有改善(利用DAG结构)")

def generate_recommendations():
    """生成优化建议"""
    print(f"\n{'='*80}")
    print(f"💡 优化建议")
    print(f"{'='*80}")
    
    print(f"\n1. Retrieval Threshold (θ) 调优:")
    print(f"   当前值: 0.05 (control.py line 289, 310, 323, 340)")
    print(f"   调优方向:")
    print(f"   - 若Recall过低(检索不到相关内容): 降低至0.00-0.03")
    print(f"   - 若Precision过低(检索到太多无关内容): 提高至0.10-0.20")
    print(f"   - 建议实验范围: [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]")
    
    print(f"\n2. α参数 (goal vs step权重):")
    print(f"   当前值: 0.3 (论文默认)")
    print(f"   公式: score = α * sim(goal) + (1-α) * sim(step)")
    print(f"   - α越大: 越倾向于匹配高层目标")
    print(f"   - α越小: 越倾向于匹配具体步骤")
    print(f"   - Procedural类问题可能需要较低α (关注步骤)")
    print(f"   - Factual类问题可能需要较高α (关注目标)")
    
    print(f"\n3. 衡量指标体系:")
    print(f"   a) 召回率指标:")
    print(f"      - Recall@K: Top-K结果中相关内容占比")
    print(f"      - Coverage: 至少检索到1个结果的查询比例")
    print(f"   b) 准确率指标:")
    print(f"      - Precision@K: Top-K结果中有多少是真正相关的")
    print(f"      - MRR: Mean Reciprocal Rank - 第一个相关结果的平均排名")
    print(f"   c) 端到端指标:")
    print(f"      - QA Accuracy: 最终答案正确率 (gpt_eval)")
    print(f"      - Avg Rounds: 平均推理轮数 (反映检索效率)")
    print(f"      - Avg Time: 平均响应时间")
    
    print(f"\n4. 分层分析:")
    print(f"   - 按查询类型(Procedural/Factual/Constrained)分别评估")
    print(f"   - 按视频复杂度分组(procedure数量、DAG分支数)")
    print(f"   - 分析失败case的共同特征")

def main():
    print(f"🔬 NSTF实验结果分析工具")
    
    # 加载结果
    robot_results = load_results('robot')
    web_results = load_results('web')
    
    if len(robot_results) > 0:
        print(f"\n{'#'*80}")
        print(f"Robot Dataset")
        print(f"{'#'*80}")
        robot_stats = analyze_results(robot_results)
    
    if len(web_results) > 0:
        print(f"\n{'#'*80}")
        print(f"Web Dataset")
        print(f"{'#'*80}")
        web_stats = analyze_results(web_results)
    
    # 对比分析
    compare_with_baseline()
    
    # 生成建议
    generate_recommendations()
    
    # 保存分析结果
    output_file = project_root / "analysis_results/current_performance_summary.json"
    output_file.parent.mkdir(exist_ok=True)
    
    summary = {
        'robot': robot_stats if 'robot_stats' in locals() else None,
        'web': web_stats if 'web_stats' in locals() else None,
        'timestamp': str(Path(results_dir / "index_robot.jsonl").stat().st_mtime if (results_dir / "index_robot.jsonl").exists() else "unknown")
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n{'='*80}")
    print(f"✅ 分析完成！结果已保存至: {output_file}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
