#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速分析 baseline_results.jsonl 的轮次和准确率
"""

import json
from collections import Counter

results_file = '/data1/rongjiej/NSTF_MODEL/experiments/efficiency/results/baseline_results.jsonl'

# 读取数据
items = []
with open(results_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                items.append(json.loads(line))
            except:
                pass

print(f"总问题数: {len(items)}")
print()

# 统计轮次分布
rounds_counter = Counter()
for item in items:
    rounds = item.get('num_rounds', 'N/A')
    rounds_counter[rounds] += 1

print("轮次分布:")
for rounds in sorted(rounds_counter.keys()):
    count = rounds_counter[rounds]
    print(f"  {rounds} 轮: {count} 题 ({count/len(items)*100:.1f}%)")

# 统计准确率
correct = sum(1 for item in items if item.get('gpt_eval', False))
print(f"\n准确率: {correct}/{len(items)} = {correct/len(items)*100:.1f}%")

# 统计平均轮次
rounds_list = [item.get('num_rounds', 0) for item in items if item.get('num_rounds')]
if rounds_list:
    avg_rounds = sum(rounds_list) / len(rounds_list)
    print(f"平均轮次: {avg_rounds:.2f}")

# 统计平均耗时
time_list = [item.get('elapsed_time_sec', 0) for item in items if item.get('elapsed_time_sec')]
if time_list:
    avg_time = sum(time_list) / len(time_list)
    print(f"平均耗时: {avg_time:.2f}s")

# 按正确/错误分组的轮次分布
print("\n按正确/错误分组的轮次分布:")
correct_rounds = [item.get('num_rounds', 0) for item in items if item.get('gpt_eval', False)]
wrong_rounds = [item.get('num_rounds', 0) for item in items if not item.get('gpt_eval', False)]

if correct_rounds:
    print(f"  正确答案平均轮次: {sum(correct_rounds)/len(correct_rounds):.2f}")
if wrong_rounds:
    print(f"  错误答案平均轮次: {sum(wrong_rounds)/len(wrong_rounds):.2f}")
