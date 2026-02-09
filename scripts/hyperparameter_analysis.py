#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超参数实验分析脚本

分析当前NSTF实验结果，计算关键衡量指标，为超参数调优提供数据支持。

使用方法:
    cd /data1/rongjiej/NSTF_MODEL
    python scripts/hyperparameter_analysis.py
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "results/nstf"
CONFIG_DIR = PROJECT_ROOT / "nstf_builder/config"
QA_CONFIG_DIR = PROJECT_ROOT / "qa_system/config"


def load_config():
    """加载当前配置"""
    config = {}
    
    # NSTF Builder 配置
    builder_config_path = CONFIG_DIR / "default.json"
    if builder_config_path.exists():
        with open(builder_config_path, 'r', encoding='utf-8') as f:
            config['nstf_builder'] = json.load(f)
    
    # QA System 配置
    qa_config_path = QA_CONFIG_DIR / "default.json"
    if qa_config_path.exists():
        with open(qa_config_path, 'r', encoding='utf-8') as f:
            config['qa_system'] = json.load(f)
    
    return config


def load_results(dataset='robot'):
    """加载实验结果"""
    index_file = RESULTS_DIR / f"index_{dataset}.jsonl"
    
    if not index_file.exists():
        print(f"❌ 结果文件不存在: {index_file}")
        return []
    
    results = []
    with open(index_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    
    return results


def deduplicate_results(results):
    """去重: 同一个问题可能被多次测试，取最新的"""
    latest = {}
    for r in results:
        qid = r.get('id', '')
        timestamp = r.get('timestamp', '')
        if qid not in latest or timestamp > latest[qid]['timestamp']:
            latest[qid] = r
    return list(latest.values())


def calculate_metrics(results):
    """计算关键衡量指标"""
    
    # 去重
    results = deduplicate_results(results)
    
    total = len(results)
    if total == 0:
        return None
    
    # 基本指标
    success_count = len([r for r in results if r.get('status') == 'success'])
    correct_count = len([r for r in results if r.get('gpt_eval') == True])
    
    # 按查询类型分组
    by_type = defaultdict(list)
    for r in results:
        q_type = r.get('type_query', 'Unknown')
        by_type[q_type].append(r)
    
    # 按视频分组
    by_video = defaultdict(list)
    for r in results:
        video_id = r.get('video_id', 'unknown')
        by_video[video_id].append(r)
    
    # 效率指标
    rounds_list = [r.get('num_rounds', 0) for r in results if r.get('status') == 'success']
    searches_list = [r.get('search_count', 0) for r in results if r.get('status') == 'success']
    times_list = [r.get('elapsed_time_sec', 0) for r in results if r.get('status') == 'success']
    
    metrics = {
        # 整体指标
        'total_questions': total,
        'success_count': success_count,
        'correct_count': correct_count,
        'overall_accuracy': correct_count / total if total > 0 else 0,
        'success_rate': success_count / total if total > 0 else 0,
        
        # 效率指标
        'avg_rounds': np.mean(rounds_list) if rounds_list else 0,
        'std_rounds': np.std(rounds_list) if rounds_list else 0,
        'avg_searches': np.mean(searches_list) if searches_list else 0,
        'std_searches': np.std(searches_list) if searches_list else 0,
        'avg_time_sec': np.mean(times_list) if times_list else 0,
        'std_time_sec': np.std(times_list) if times_list else 0,
        
        # 按类型统计
        'by_type': {},
        
        # 按视频统计
        'by_video': {},
    }
    
    # 按类型统计
    for q_type, type_results in by_type.items():
        type_total = len(type_results)
        type_correct = len([r for r in type_results if r.get('gpt_eval') == True])
        metrics['by_type'][q_type] = {
            'total': type_total,
            'correct': type_correct,
            'accuracy': type_correct / type_total if type_total > 0 else 0
        }
    
    # 按视频统计
    for video_id, video_results in by_video.items():
        video_total = len(video_results)
        video_correct = len([r for r in video_results if r.get('gpt_eval') == True])
        metrics['by_video'][video_id] = {
            'total': video_total,
            'correct': video_correct,
            'accuracy': video_correct / video_total if video_total > 0 else 0
        }
    
    return metrics


def print_metrics_report(metrics, dataset_name):
    """打印指标报告"""
    print(f"\n{'='*80}")
    print(f"📊 {dataset_name} 数据集指标报告")
    print(f"{'='*80}")
    
    print(f"\n【1. 整体性能】")
    print(f"  总问题数: {metrics['total_questions']}")
    print(f"  成功数: {metrics['success_count']}")
    print(f"  正确数: {metrics['correct_count']}")
    print(f"  ✅ 整体准确率 (QA Accuracy): {metrics['overall_accuracy']:.2%}")
    print(f"  成功率: {metrics['success_rate']:.2%}")
    
    print(f"\n【2. 效率指标】")
    print(f"  平均轮数: {metrics['avg_rounds']:.2f} ± {metrics['std_rounds']:.2f}")
    print(f"  平均搜索次数: {metrics['avg_searches']:.2f} ± {metrics['std_searches']:.2f}")
    print(f"  平均耗时: {metrics['avg_time_sec']:.2f}秒 ± {metrics['std_time_sec']:.2f}秒")
    
    print(f"\n【3. 按查询类型分析】")
    for q_type, stats in sorted(metrics['by_type'].items()):
        print(f"  {q_type}:")
        print(f"    问题数: {stats['total']}")
        print(f"    正确数: {stats['correct']}")
        print(f"    准确率: {stats['accuracy']:.2%}")
    
    print(f"\n【4. 按视频分析 (前10个)】")
    sorted_videos = sorted(metrics['by_video'].items(), key=lambda x: x[1]['accuracy'], reverse=True)
    for video_id, stats in sorted_videos[:10]:
        print(f"  {video_id}: {stats['correct']}/{stats['total']} = {stats['accuracy']:.2%}")


def print_config_summary(config):
    """打印当前配置"""
    print(f"\n{'='*80}")
    print(f"⚙️ 当前超参数配置")
    print(f"{'='*80}")
    
    if 'nstf_builder' in config:
        builder = config['nstf_builder']
        print(f"\n【NSTF Builder 参数】")
        print(f"  Support Threshold (σ, pattern_min_support): {builder.get('pattern_min_support', 'N/A')}")
        print(f"  Verify Threshold (τ, verify_threshold): {builder.get('verify_threshold', 'N/A')}")
        print(f"  Gating Threshold (δ, match_threshold): {builder.get('match_threshold', 'N/A')}")
        print(f"  EMA Coefficient (β, ema_beta): {builder.get('ema_beta', 'N/A')}")
        print(f"  Fusion Similarity Threshold: {builder.get('fusion_similarity_threshold', 'N/A')}")
        print(f"  Step Align Threshold: {builder.get('step_align_threshold', 'N/A')}")
    
    if 'qa_system' in config:
        qa = config['qa_system']
        print(f"\n【QA System 参数】")
        print(f"  Retrieval Threshold (θ, threshold): {qa.get('threshold', 'N/A')}")
        print(f"  Baseline Threshold: {qa.get('threshold_baseline', 'N/A')}")
        print(f"  TopK: {qa.get('topk', 'N/A')}")
    
    print(f"\n【检索权重参数 (在代码中硬编码)】")
    print(f"  Retrieval Weight (α): 0.3 (硬编码于 hybrid_retriever.py)")


def print_hyperparameter_recommendations():
    """打印超参数实验建议"""
    print(f"\n{'='*80}")
    print(f"🔬 超参数实验建议")
    print(f"{'='*80}")
    
    print(f"""
【待实验参数分析】

1. Support Threshold (σ) - 最小支持度阈值
   当前值: 0.2
   影响: 控制PrefixSpan模式挖掘的最小支持度
   实验难度: ⚠️ 中等 - 需要重新构建图谱
   建议测试范围: [0.1, 0.15, 0.2, 0.25, 0.3]
   
2. EMA Coefficient (β) - EMA衰减系数
   当前值: 0.9
   影响: 控制增量更新时历史vs新观测的权重
   实验难度: ⚠️ 中等 - 需要重新运行增量更新
   建议测试范围: [0.7, 0.8, 0.85, 0.9, 0.95]

3. Retrieval Weight (α) - 检索权重参数 ⭐ 推荐
   当前值: 0.3 (硬编码)
   影响: 论文Eq.(2)核心公式，goal vs step匹配权重
   实验难度: ✅ 容易 - 只需修改一个参数，无需重建图谱
   建议测试范围: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
   
4. Fusion Similarity Threshold
   当前值: 0.80
   影响: 决定两个Procedure是否足够相似以进行融合
   实验难度: ⚠️ 中等 - 需要重新运行fusion
   建议测试范围: [0.70, 0.75, 0.80, 0.85, 0.90]

5. Step Alignment Threshold
   当前值: 0.75
   影响: DAG融合时判断两个step是否语义等价
   实验难度: ⚠️ 中等 - 需要重新运行fusion
   建议测试范围: [0.65, 0.70, 0.75, 0.80, 0.85]

【推荐实验顺序】
1. 首选 Retrieval Weight (α) - 最容易实验，直接影响检索效果
2. 次选 Fusion Similarity Threshold - 影响图谱质量
3. 再次 Support Threshold (σ) - 需要完整重建
""")


def print_metric_explanations():
    """打印衡量指标说明"""
    print(f"\n{'='*80}")
    print(f"📏 衡量指标说明")
    print(f"{'='*80}")
    
    print(f"""
【核心指标】

1. QA Accuracy (整体准确率)
   定义: 正确回答的问题数 / 总问题数
   当前值: 见上方报告
   预期: NSTF应比Baseline(~50%)有提升，目标 > 60%
   
2. Procedural类问题准确率
   定义: Procedural类型问题的正确率
   意义: NSTF的核心优势应体现在程序性问题上
   预期: 应明显高于Factual类问题
   
3. 平均检索轮数 (Avg Rounds)
   定义: 每个问题平均需要的推理轮数
   意义: 反映检索效率
   预期: NSTF应该能更快找到答案，轮数应下降
   
4. 平均搜索次数 (Avg Searches)
   定义: 每个问题平均的搜索次数
   意义: 反映检索精准度
   预期: 更少搜索次数 = 更精准的检索

【超参数调优的观察指标】

对于 Retrieval Weight (α) 实验:
- α 增大: Goal匹配权重增加
  - Procedural问题准确率应提升
  - 高层意图匹配更好
  
- α 减小: Step匹配权重增加
  - 具体步骤相关问题应提升
  - 细节检索更准确

预期曲线:
- Procedural问题: 可能在 α=0.3-0.5 最优
- Factual问题: 可能在 α=0.2-0.3 最优
- 整体: 应该有一个最优 α 平衡两者
""")


def main():
    print("="*80)
    print("🔬 NSTF 超参数实验分析报告")
    print("="*80)
    
    # 加载配置
    config = load_config()
    print_config_summary(config)
    
    # 加载并分析 robot 数据集结果
    robot_results = load_results('robot')
    if robot_results:
        robot_metrics = calculate_metrics(robot_results)
        if robot_metrics:
            print_metrics_report(robot_metrics, "Robot")
    
    # 加载并分析 web 数据集结果
    web_results = load_results('web')
    if web_results:
        web_metrics = calculate_metrics(web_results)
        if web_metrics:
            print_metrics_report(web_metrics, "Web")
    
    # 打印指标说明
    print_metric_explanations()
    
    # 打印超参数实验建议
    print_hyperparameter_recommendations()
    
    print(f"\n{'='*80}")
    print("✅ 分析完成!")
    print("="*80)


if __name__ == "__main__":
    main()
