#!/usr/bin/env python3
"""
绘制Threshold分析图表 - 用于论文可视化

生成三个核心图表：
1. threshold_tradeoff.pdf - Threshold vs Performance权衡曲线
2. embedding_similarity.pdf - Embedding相似度热力图
3. retrieval_distribution.pdf - 不同Threshold下的检索分布
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# 设置中文字体和样式
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
sns.set_style("whitegrid")

# 路径配置
project_root = Path(__file__).parent.parent
data_file = project_root / "analysis_results/threshold_analysis_robot.json"
output_dir = project_root / "docs/figures"
output_dir.mkdir(parents=True, exist_ok=True)

print(f"🎨 Threshold Analysis 可视化")
print(f"数据文件: {data_file}")
print(f"输出目录: {output_dir}")

# 加载数据
with open(data_file, 'r') as f:
    data = json.load(f)

# ============================================================================
# 图1: Threshold vs Performance Trade-off (多条曲线)
# ============================================================================

def plot_threshold_tradeoff():
    """绘制Threshold对各项指标的影响"""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Retrieval Threshold Impact on Performance Metrics', 
                 fontsize=14, fontweight='bold')
    
    # 汇总三个视频的平均值
    videos = ['kitchen_03', 'kitchen_22', 'kitchen_15']
    thresholds = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    
    metrics = {
        'coverage': [],
        'recall@5': [],
        'precision': [],
        'mrr': []
    }
    
    for threshold in thresholds:
        values = {
            'coverage': [],
            'recall@5': [],
            'precision': [],
            'mrr': []
        }
        
        for video in videos:
            threshold_data = data[video]['retrieval_metrics']['threshold_analysis'][str(threshold)]
            values['coverage'].append(threshold_data['coverage'])
            values['recall@5'].append(threshold_data['recall@5'])
            values['precision'].append(threshold_data['precision'])
            values['mrr'].append(threshold_data['mrr'])
        
        # 计算平均值
        for key in metrics:
            metrics[key].append(np.mean(values[key]))
    
    # 子图1: Coverage
    ax1 = axes[0, 0]
    ax1.plot(thresholds, metrics['coverage'], 'o-', linewidth=2, markersize=6, 
             color='#2ecc71', label='Coverage')
    ax1.axvline(x=0.05, color='red', linestyle='--', alpha=0.5, label='Current (θ=0.05)')
    ax1.axhline(y=0.95, color='gray', linestyle=':', alpha=0.3, label='95% Target')
    ax1.set_xlabel('Threshold (θ)', fontsize=11)
    ax1.set_ylabel('Coverage', fontsize=11)
    ax1.set_title('(a) Coverage vs Threshold', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)
    ax1.set_ylim([0, 1.05])
    
    # 子图2: Recall@5
    ax2 = axes[0, 1]
    ax2.plot(thresholds, metrics['recall@5'], 's-', linewidth=2, markersize=6,
             color='#3498db', label='Recall@5')
    ax2.axvline(x=0.05, color='red', linestyle='--', alpha=0.5, label='Current (θ=0.05)')
    ax2.set_xlabel('Threshold (θ)', fontsize=11)
    ax2.set_ylabel('Recall@5', fontsize=11)
    ax2.set_title('(b) Recall@5 vs Threshold', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)
    ax2.set_ylim([0, max(metrics['recall@5']) * 1.1])
    
    # 子图3: Precision
    ax3 = axes[1, 0]
    ax3.plot(thresholds, metrics['precision'], '^-', linewidth=2, markersize=6,
             color='#e74c3c', label='Precision')
    ax3.axvline(x=0.05, color='red', linestyle='--', alpha=0.5, label='Current (θ=0.05)')
    ax3.set_xlabel('Threshold (θ)', fontsize=11)
    ax3.set_ylabel('Precision', fontsize=11)
    ax3.set_title('(c) Precision vs Threshold', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)
    ax3.set_ylim([0, max(metrics['precision']) * 1.1])
    
    # 子图4: MRR
    ax4 = axes[1, 1]
    ax4.plot(thresholds, metrics['mrr'], 'D-', linewidth=2, markersize=6,
             color='#9b59b6', label='MRR')
    ax4.axvline(x=0.05, color='red', linestyle='--', alpha=0.5, label='Current (θ=0.05)')
    ax4.set_xlabel('Threshold (θ)', fontsize=11)
    ax4.set_ylabel('MRR (Mean Reciprocal Rank)', fontsize=11)
    ax4.set_title('(d) MRR vs Threshold', fontsize=12)
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=9)
    ax4.set_ylim([0, max(metrics['mrr']) * 1.1])
    
    plt.tight_layout()
    output_path = output_dir / "threshold_tradeoff.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.savefig(output_dir / "threshold_tradeoff.png", format='png', bbox_inches='tight')
    print(f"✅ 图1已保存: {output_path}")
    plt.close()

# ============================================================================
# 图2: Embedding Similarity Heatmap
# ============================================================================

def plot_embedding_similarity():
    """绘制Goal和Step Embedding的内部相似度分布"""
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle('Procedure Embedding Internal Similarity Distribution', 
                 fontsize=14, fontweight='bold')
    
    videos = ['kitchen_03', 'kitchen_22', 'kitchen_15']
    titles = ['(a) Kitchen_03 (31 Procedures)', 
              '(b) Kitchen_22 (22 Procedures)', 
              '(c) Kitchen_15 (16 Procedures)']
    
    for idx, (video, title) in enumerate(zip(videos, titles)):
        emb_stats = data[video]['embedding_stats']
        
        goal_sim = emb_stats['goal_embeddings']['internal_similarity']
        step_sim = emb_stats['step_embeddings']['internal_similarity']
        
        # 准备数据用于箱线图
        metrics = ['Min', 'P50', 'P75', 'P90', 'P95', 'Max']
        goal_values = [goal_sim['min'], goal_sim['p50'], goal_sim['p75'], 
                      goal_sim['p90'], goal_sim['p95'], goal_sim['max']]
        step_values = [step_sim['min'], step_sim['p50'], step_sim['p75'],
                      step_sim['p90'], step_sim['p95'], step_sim['max']]
        
        x = np.arange(len(metrics))
        width = 0.35
        
        ax = axes[idx]
        ax.bar(x - width/2, goal_values, width, label='Goal Embedding', 
               color='#3498db', alpha=0.8)
        ax.bar(x + width/2, step_values, width, label='Step Embedding',
               color='#e74c3c', alpha=0.8)
        
        ax.set_xlabel('Similarity Percentiles', fontsize=10)
        ax.set_ylabel('Cosine Similarity', fontsize=10)
        ax.set_title(title, fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(metrics, fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim([0, 1])
        
        # 添加均值参考线
        ax.axhline(y=goal_sim['mean'], color='#3498db', linestyle='--', 
                  alpha=0.3, linewidth=1)
        ax.axhline(y=step_sim['mean'], color='#e74c3c', linestyle='--',
                  alpha=0.3, linewidth=1)
    
    plt.tight_layout()
    output_path = output_dir / "embedding_similarity.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.savefig(output_dir / "embedding_similarity.png", format='png', bbox_inches='tight')
    print(f"✅ 图2已保存: {output_path}")
    plt.close()

# ============================================================================
# 图3: Retrieval Count Distribution
# ============================================================================

def plot_retrieval_distribution():
    """绘制不同Threshold下检索结果数量分布"""
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle('Retrieved Procedure Count Distribution (Different Thresholds)',
                 fontsize=14, fontweight='bold')
    
    videos = ['kitchen_03', 'kitchen_22', 'kitchen_15']
    titles = ['(a) Kitchen_03', '(b) Kitchen_22', '(c) Kitchen_15']
    
    # 选择几个有代表性的threshold值
    selected_thresholds = [0.05, 0.15, 0.25, 0.35, 0.5]
    colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#95a5a6']
    
    for idx, (video, title) in enumerate(zip(videos, titles)):
        ax = axes[idx]
        
        avg_retrieved = []
        zero_recall = []
        
        for threshold in selected_thresholds:
            threshold_data = data[video]['retrieval_metrics']['threshold_analysis'][str(threshold)]
            avg_retrieved.append(threshold_data['avg_retrieved'])
            zero_recall.append(threshold_data['zero_recall_count'])
        
        x = np.arange(len(selected_thresholds))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, avg_retrieved, width, label='Avg Retrieved',
                      color=colors, alpha=0.8)
        bars2 = ax.bar(x + width/2, zero_recall, width, label='Zero Recall Count',
                      color='red', alpha=0.6)
        
        ax.set_xlabel('Threshold', fontsize=10)
        ax.set_ylabel('Count', fontsize=10)
        ax.set_title(title, fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels([f'{t:.2f}' for t in selected_thresholds], fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 标注当前使用值
        current_idx = selected_thresholds.index(0.05)
        ax.axvline(x=current_idx, color='green', linestyle='--', alpha=0.5,
                  linewidth=2, label='Current')
    
    plt.tight_layout()
    output_path = output_dir / "retrieval_distribution.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.savefig(output_dir / "retrieval_distribution.png", format='png', bbox_inches='tight')
    print(f"✅ 图3已保存: {output_path}")
    plt.close()

# ============================================================================
# 图4: 综合对比图 (All-in-One)
# ============================================================================

def plot_comprehensive_comparison():
    """单图展示所有关键信息 - 适合论文主图"""
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 汇总数据
    videos = ['kitchen_03', 'kitchen_22', 'kitchen_15']
    thresholds = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    
    metrics = {
        'Coverage': [],
        'Recall@5': [],
        'Precision': [],
        'MRR': []
    }
    
    for threshold in thresholds:
        for metric_name in metrics:
            values = []
            for video in videos:
                threshold_data = data[video]['retrieval_metrics']['threshold_analysis'][str(threshold)]
                
                if metric_name == 'Coverage':
                    values.append(threshold_data['coverage'])
                elif metric_name == 'Recall@5':
                    values.append(threshold_data['recall@5'])
                elif metric_name == 'Precision':
                    values.append(threshold_data['precision'])
                elif metric_name == 'MRR':
                    values.append(threshold_data['mrr'])
            
            metrics[metric_name].append(np.mean(values))
    
    # 绘制曲线
    ax.plot(thresholds, metrics['Coverage'], 'o-', linewidth=2.5, markersize=7,
            color='#2ecc71', label='Coverage', alpha=0.9)
    ax.plot(thresholds, metrics['Recall@5'], 's-', linewidth=2.5, markersize=7,
            color='#3498db', label='Recall@5', alpha=0.9)
    ax.plot(thresholds, metrics['Precision'], '^-', linewidth=2.5, markersize=7,
            color='#e74c3c', label='Precision', alpha=0.9)
    ax.plot(thresholds, metrics['MRR'], 'D-', linewidth=2.5, markersize=7,
            color='#9b59b6', label='MRR', alpha=0.9)
    
    # 标注当前值
    ax.axvline(x=0.05, color='red', linestyle='--', linewidth=2, alpha=0.6,
              label='Current (θ=0.05)')
    
    # 标注Baseline对比点
    ax.axvline(x=0.50, color='gray', linestyle=':', linewidth=2, alpha=0.4,
              label='Baseline (θ=0.50)')
    
    # 添加95% Coverage参考线
    ax.axhline(y=0.95, color='green', linestyle=':', alpha=0.3, linewidth=1.5)
    ax.text(0.25, 0.97, '95% Coverage Target', fontsize=9, color='green', alpha=0.7)
    
    ax.set_xlabel('Retrieval Threshold (θ)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Performance Metrics', fontsize=12, fontweight='bold')
    ax.set_title('Threshold Impact on Retrieval Performance (Average across 3 videos)',
                fontsize=13, fontweight='bold')
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([-0.02, 0.52])
    ax.set_ylim([0, 1.05])
    
    plt.tight_layout()
    output_path = output_dir / "comprehensive_comparison.pdf"
    plt.savefig(output_path, format='pdf', bbox_inches='tight')
    plt.savefig(output_dir / "comprehensive_comparison.png", format='png', bbox_inches='tight')
    print(f"✅ 综合对比图已保存: {output_path}")
    plt.close()

# ============================================================================
# 主函数
# ============================================================================

def main():
    print("\n生成图表...")
    
    plot_threshold_tradeoff()
    plot_embedding_similarity()
    plot_retrieval_distribution()
    plot_comprehensive_comparison()
    
    print(f"\n{'='*80}")
    print("✅ 所有图表生成完成！")
    print(f"{'='*80}")
    print(f"\n输出目录: {output_dir}")
    print("\n生成的文件:")
    for file in sorted(output_dir.glob("*.pdf")):
        print(f"  - {file.name}")
    
    print("\n论文使用建议:")
    print("  - 主图: comprehensive_comparison.pdf (展示整体trade-off)")
    print("  - 详细分析: threshold_tradeoff.pdf (四个子图)")
    print("  - Embedding质量: embedding_similarity.pdf")
    print("  - 检索分布: retrieval_distribution.pdf")

if __name__ == "__main__":
    main()
