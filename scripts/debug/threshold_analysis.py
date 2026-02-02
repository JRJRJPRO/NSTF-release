# -*- coding: utf-8 -*-
"""
全面阈值分析 - 用真实问答数据测试
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from env_setup import setup_all
setup_all()

from mmagent.retrieve import search, retrieve_from_videograph
from mmagent.utils.general import load_video_graph

# 加载真实问答数据
annotations_file = project_root / "data" / "annotations" / "robot.json"
annotations = json.load(open(annotations_file))

# 收集所有问题和对应的图谱
all_questions = []
for video_name, video_data in annotations.items():
    mem_path = video_data.get('mem_path', '')
    if not os.path.isabs(mem_path):
        mem_path = str(project_root / mem_path)
    
    if not os.path.exists(mem_path):
        continue
    
    for qa in video_data.get('qa_list', []):
        all_questions.append({
            'question': qa['question'],
            'answer': qa['answer'],
            'mem_path': mem_path,
            'video': video_name,
            'before_clip': qa.get('before_clip'),
        })

print(f"总共 {len(all_questions)} 个问题")

# 随机抽样 100 个问题进行分析
import random
random.seed(42)
sample_questions = random.sample(all_questions, min(100, len(all_questions)))

print(f"抽样 {len(sample_questions)} 个问题进行分析\n")

# 缓存已加载的图谱
graph_cache = {}

def get_graph(mem_path):
    if mem_path not in graph_cache:
        g = load_video_graph(mem_path)
        g.refresh_equivalences()
        graph_cache[mem_path] = g
    return graph_cache[mem_path]

# 收集每个问题的分数分布
print("正在分析每个问题的检索分数分布...")
question_stats = []

for i, q in enumerate(sample_questions):
    if (i + 1) % 20 == 0:
        print(f"  处理 {i+1}/{len(sample_questions)}...")
    
    try:
        g = get_graph(q['mem_path'])
        _, clip_scores, _ = retrieve_from_videograph(
            g, q['question'], topk=100, threshold=0, before_clip=q['before_clip']
        )
        
        if clip_scores:
            max_score = max(clip_scores.values())
            avg_score = sum(clip_scores.values()) / len(clip_scores)
            num_clips = len(clip_scores)
            
            # 统计不同阈值下能返回多少 clip
            clips_by_threshold = {}
            for th in [0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5]:
                clips_by_threshold[th] = sum(1 for s in clip_scores.values() if s >= th)
            
            question_stats.append({
                'question': q['question'][:50],
                'max_score': max_score,
                'avg_score': avg_score,
                'num_clips': num_clips,
                'clips_by_threshold': clips_by_threshold,
            })
    except Exception as e:
        print(f"  错误: {e}")
        continue

print(f"\n成功分析 {len(question_stats)} 个问题")

# === 分析 1: 分数分布 ===
print(f"\n{'='*70}")
print("【分析1: 最高分分布】")
print(f"{'='*70}")

max_scores = [q['max_score'] for q in question_stats]
print(f"最高分范围: {min(max_scores):.4f} ~ {max(max_scores):.4f}")
print(f"最高分平均: {sum(max_scores)/len(max_scores):.4f}")
print(f"最高分中位数: {sorted(max_scores)[len(max_scores)//2]:.4f}")

# 分布直方图
print(f"\n最高分分布:")
for low, high in [(0, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.0)]:
    count = sum(1 for s in max_scores if low <= s < high)
    bar = '█' * (count * 40 // len(max_scores))
    print(f"  {low:.1f}-{high:.1f}: {count:3d} ({count/len(max_scores)*100:5.1f}%) {bar}")

# === 分析 2: 不同阈值下的命中率和平均返回数 ===
print(f"\n{'='*70}")
print("【分析2: 不同阈值下的效果】")
print(f"{'='*70}")

print(f"\n{'阈值':<10} {'命中率':<15} {'平均返回clip数':<15} {'说明'}")
print("-" * 60)

for th in [0, 0.1, 0.2, 0.3, 0.35, 0.4, 0.45, 0.5]:
    # 命中率：有多少问题至少返回1个clip
    hit_count = sum(1 for q in question_stats if q['clips_by_threshold'][th] > 0)
    hit_rate = hit_count / len(question_stats)
    
    # 平均返回clip数（只算命中的）
    clips_returned = [q['clips_by_threshold'][th] for q in question_stats if q['clips_by_threshold'][th] > 0]
    avg_clips = sum(clips_returned) / len(clips_returned) if clips_returned else 0
    
    note = ""
    if th == 0.5:
        note = "← 原始代码"
    elif th == 0.4:
        note = "← 候选"
    elif th == 0.3:
        note = "← 候选"
    elif th == 0:
        note = "← 无过滤"
    
    print(f"{th:<10.2f} {hit_rate*100:>6.1f}%        {avg_clips:>6.1f}          {note}")

# === 分析 3: 阈值与信息量的权衡 ===
print(f"\n{'='*70}")
print("【分析3: 阈值与信息量权衡思考】")
print(f"{'='*70}")

print("""
问题：更低的阈值返回更多clip，但这是好事还是坏事？

权衡因素:
1. 返回太多 → LLM上下文变长，可能淹没关键信息，增加token成本
2. 返回太少 → 可能漏掉答案所在的clip
3. topk=2 已经限制了最多返回2个clip，所以阈值主要影响"能否返回"

关键洞察:
- 如果 max_score < threshold → 返回0个clip（完全没有信息）
- 如果 max_score >= threshold → 返回top-k个clip（有信息）

所以阈值的核心作用是：过滤掉"完全不相关"的检索，而不是控制返回数量。
返回数量由 topk 控制。
""")

# === 分析 4: 具体看几个低分问题 ===
print(f"\n{'='*70}")
print("【分析4: 低分问题示例（最高分 < 0.4）】")
print(f"{'='*70}")

low_score_questions = [q for q in question_stats if q['max_score'] < 0.4]
print(f"\n共有 {len(low_score_questions)} 个问题最高分 < 0.4:\n")

for q in low_score_questions[:5]:
    print(f"  问题: {q['question']}...")
    print(f"  最高分: {q['max_score']:.4f}")
    print()

# === 结论 ===
print(f"\n{'='*70}")
print("【结论与建议】")
print(f"{'='*70}")

# 计算在不同阈值下会丢失多少问题
lost_at_05 = sum(1 for s in max_scores if s < 0.5)
lost_at_04 = sum(1 for s in max_scores if s < 0.4)
lost_at_03 = sum(1 for s in max_scores if s < 0.3)

print(f"""
基于 {len(question_stats)} 个问题的分析:

1. threshold=0.5 (原始代码): 
   - {lost_at_05} 个问题 ({lost_at_05/len(question_stats)*100:.1f}%) 第一轮搜索会返回空
   - 这些问题需要靠 LLM 换角度重新搜索

2. threshold=0.4:
   - {lost_at_04} 个问题 ({lost_at_04/len(question_stats)*100:.1f}%) 第一轮搜索会返回空
   - 比 0.5 少丢失 {lost_at_05 - lost_at_04} 个问题

3. threshold=0.3:
   - {lost_at_03} 个问题 ({lost_at_03/len(question_stats)*100:.1f}%) 第一轮搜索会返回空
   - 比 0.5 少丢失 {lost_at_05 - lost_at_03} 个问题

建议: 使用 threshold=0.3 或 0.35
原因: 
- topk=2 已经限制了返回数量，不会信息过载
- 更低阈值减少"空返回"，让LLM更早获得有用信息
- 真正的噪声过滤应该靠 LLM 的推理能力，而不是硬阈值
""")
