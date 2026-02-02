#!/bin/bash
# Efficiency 实验 - 生成 NSTF 图谱
# 
# 为 efficiency/data/video_list.json 中的视频生成 NSTF 图谱

cd /data1/rongjiej/NSTF_MODEL

echo "=========================================="
echo "Efficiency 实验 - NSTF 图谱生成"
echo "=========================================="

# 使用 build_nstf.py 构建图谱
python experiments/build_nstf.py \
    --video-list experiments/efficiency/data/video_list.json \
    --dataset robot \
    --max-procedures 5

echo "=========================================="
echo "完成！检查图谱文件："
echo "ls -la data/nstf_graphs/robot/"
echo "=========================================="
