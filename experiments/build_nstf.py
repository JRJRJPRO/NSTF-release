#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NSTF 图谱构建脚本 - 从 video_list.json 读取视频列表，生成 NSTF 图谱
"""

import os
import sys
import json
import argparse
from pathlib import Path

# === 设置路径 ===
# 通过相对路径确定 NSTF_MODEL 目录（本脚本在 experiments/ 下）
EXPERIMENTS_DIR = Path(__file__).parent.resolve()
NSTF_MODEL_DIR = EXPERIMENTS_DIR.parent

os.chdir(NSTF_MODEL_DIR)

# 添加路径并加载环境
sys.path.insert(0, str(NSTF_MODEL_DIR))
from env_setup import setup_all
setup_all()

from nstf_builder import NSTFBuilder


def main():
    parser = argparse.ArgumentParser(description='构建NSTF图谱')
    parser.add_argument('--video-list', type=str, 
                        default='experiments/query_type/data/video_list.json',
                        help='视频列表文件')
    parser.add_argument('--dataset', type=str, default='web',
                        choices=['robot', 'web'])
    parser.add_argument('--max-procedures', type=int, default=5,
                        help='每视频最多提取程序数')
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制重新生成（覆盖已存在的图谱）')
    parser.add_argument('--videos', type=str, nargs='+', default=None,
                        help='指定要处理的视频名称（不指定则处理列表中所有视频）')
    
    args = parser.parse_args()
    
    # 加载视频列表
    video_list_path = NSTF_MODEL_DIR / args.video_list
    with open(video_list_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos = data.get('videos', data) if isinstance(data, dict) else data
    print(f"读取视频列表: {len(videos)} 个视频")
    
    # 如果指定了具体视频，只处理这些视频
    if args.videos:
        videos = [v for v in videos if v in args.videos]
        for v in args.videos:
            if v not in videos:
                videos.append(v)
        print(f"指定处理视频: {videos}")
    
    # 检查已存在的图谱
    output_dir = NSTF_MODEL_DIR / 'data' / 'nstf_graphs' / args.dataset
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.force:
        to_process = videos
        print(f"强制模式: 将重新生成 {len(to_process)} 个图谱")
    else:
        # 默认跳过已存在的
        existing = set()
        for f in output_dir.glob('*_nstf.pkl'):
            video_name = f.stem.replace('_nstf', '')
            existing.add(video_name)
        
        to_process = [v for v in videos if v not in existing]
        print(f"已存在: {len(existing)} 个，待处理: {len(to_process)} 个")
        
        if existing:
            print(f"跳过: {existing}")
    
    if not to_process:
        print("所有视频已处理完成！")
        return
    
    # 构建
    builder = NSTFBuilder()
    builder.build_batch(to_process, dataset=args.dataset, max_procedures=args.max_procedures)


if __name__ == '__main__':
    main()
