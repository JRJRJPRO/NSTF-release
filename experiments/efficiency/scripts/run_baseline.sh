#!/bin/bash
# Efficiency 实验 - Baseline 测试
#
# 运行 Baseline 模式的问答测试，记录每个问题的轮次和时间

cd /data1/rongjiej/NSTF_MODEL

echo "=========================================="
echo "Efficiency 实验 - Baseline 测试"
echo "=========================================="
echo "视频列表: experiments/efficiency/data/video_list.json"
echo "输出文件: experiments/efficiency/results/baseline_results.jsonl"
echo "=========================================="

python experiments/run_qa.py \
    --dataset robot \
    --video-list experiments/efficiency/data/video_list.json \
    --ablation baseline \
    --output experiments/efficiency/results/baseline_results.jsonl

echo "=========================================="
echo "Baseline 测试完成！"
echo "结果文件: experiments/efficiency/results/baseline_results.jsonl"
echo "=========================================="
