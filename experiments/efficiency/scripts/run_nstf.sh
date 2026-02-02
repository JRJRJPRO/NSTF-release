#!/bin/bash
# Efficiency 实验 - NSTF 测试
#
# 运行 NSTF 模式的问答测试（默认模式，不设 --ablation）

cd /data1/rongjiej/NSTF_MODEL

echo "=========================================="
echo "Efficiency 实验 - NSTF 测试"
echo "=========================================="
echo "视频列表: experiments/efficiency/data/video_list.json"
echo "输出文件: experiments/efficiency/results/nstf_results.jsonl"
echo "注意: 需要先运行 build_nstf_graphs.sh 生成图谱！"
echo "=========================================="

# 检查 NSTF 图谱是否已生成
NSTF_DIR="/data1/rongjiej/NSTF_MODEL/data/nstf_graphs/robot"
if [ ! -d "$NSTF_DIR" ] || [ -z "$(ls -A $NSTF_DIR 2>/dev/null)" ]; then
    echo "警告: NSTF 图谱目录为空或不存在！"
    echo "请先运行: bash experiments/efficiency/scripts/build_nstf_graphs.sh"
    exit 1
fi

python experiments/run_qa.py \
    --dataset robot \
    --video-list experiments/efficiency/data/video_list.json \
    --output experiments/efficiency/results/nstf_results.jsonl

echo "=========================================="
echo "NSTF 测试完成！"
echo "结果文件: experiments/efficiency/results/nstf_results.jsonl"
echo "=========================================="
