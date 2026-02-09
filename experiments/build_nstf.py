#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NSTF 图谱构建脚本

支持两种构建模式:
- static: 静态一次性构建（用于消融实验）
- incremental: 增量构建，支持 Procedure 融合（推荐用于生产）

用法:
  # 增量构建全部视频（推荐）
  python experiments/build_nstf.py --dataset robot --mode incremental --force

  # 静态构建
  python experiments/build_nstf.py --dataset robot --mode static --force

  # 构建单个视频
  python experiments/build_nstf.py --dataset robot --videos kitchen_03 --mode incremental --force
"""

import os
import sys
import json
import argparse
from pathlib import Path

# === 设置路径 ===
EXPERIMENTS_DIR = Path(__file__).parent.resolve()
NSTF_MODEL_DIR = EXPERIMENTS_DIR.parent

os.chdir(NSTF_MODEL_DIR)

sys.path.insert(0, str(NSTF_MODEL_DIR))
from env_setup import setup_all
setup_all()


def get_video_list_from_annotations(dataset: str, data_dir: Path) -> list:
    """从 annotations 目录获取视频列表"""
    ann_dir = data_dir / "annotations" / dataset
    if ann_dir.exists():
        return sorted([f.stem for f in ann_dir.glob("*.json")])
    
    # 旧格式: 单个 JSON 文件
    ann_file = data_dir / "annotations" / f"{dataset}.json"
    if ann_file.exists():
        with open(ann_file, 'r') as f:
            data = json.load(f)
        return list(data.keys())
    
    return []


def main():
    parser = argparse.ArgumentParser(
        description='NSTF 图谱构建',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--video-list', type=str, default=None,
                        help='视频列表文件（可选，不指定则从 annotations 读取）')
    parser.add_argument('--dataset', type=str, default='robot',
                        choices=['robot', 'web'],
                        help='数据集类型')
    parser.add_argument('--mode', type=str, default='incremental',
                        choices=['static', 'incremental'],
                        help='构建模式: static(静态) 或 incremental(增量，推荐)')
    parser.add_argument('--max-procedures', type=int, default=5,
                        help='每视频最多提取程序数（仅 static 模式）')
    parser.add_argument('--force', '-f', action='store_true',
                        help='强制重新生成（覆盖已存在的图谱）')
    parser.add_argument('--videos', type=str, nargs='+', default=None,
                        help='指定要处理的视频名称')
    parser.add_argument('--debug', action='store_true',
                        help='输出调试信息')
    
    args = parser.parse_args()
    
    data_dir = NSTF_MODEL_DIR / 'data'
    
    # 获取视频列表
    if args.videos:
        videos = args.videos
    elif args.video_list:
        video_list_path = NSTF_MODEL_DIR / args.video_list
        with open(video_list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        videos = data.get('videos', data) if isinstance(data, dict) else data
    else:
        videos = get_video_list_from_annotations(args.dataset, data_dir)
    
    if not videos:
        print(f"❌ 未找到视频列表")
        return 1
    
    print("=" * 60)
    print("NSTF 图谱构建")
    print("=" * 60)
    print(f"数据集: {args.dataset}")
    print(f"构建模式: {args.mode}")
    print(f"视频数量: {len(videos)}")
    
    # 输出目录
    output_dir = data_dir / 'nstf_graphs' / args.dataset
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查已存在的图谱 - incremental 是默认模式，统一使用 _nstf.pkl
    suffix = '_nstf.pkl'
    
    if args.force:
        to_process = videos
        print(f"强制模式: 将重新生成 {len(to_process)} 个图谱")
    else:
        existing = set()
        for f in output_dir.glob(f'*{suffix}'):
            video_name = f.stem.replace('_nstf_incremental', '').replace('_nstf', '')
            existing.add(video_name)
        
        to_process = [v for v in videos if v not in existing]
        print(f"已存在: {len(existing)} 个，待处理: {len(to_process)} 个")
    
    if not to_process:
        print("所有视频已处理完成！")
        return 0
    
    print("=" * 60)
    
    # 选择构建器
    if args.mode == 'incremental':
        from nstf_builder import IncrementalNSTFBuilder
        builder = IncrementalNSTFBuilder(
            data_dir=str(data_dir),
            output_dir=str(data_dir / 'nstf_graphs'),
            debug=args.debug,
        )
        print("✓ 使用增量构建器 (IncrementalNSTFBuilder)")
        builder.build_batch(to_process, dataset=args.dataset)
    else:
        from nstf_builder import NSTFBuilder
        builder = NSTFBuilder(
            data_dir=str(data_dir),
            output_dir=str(data_dir / 'nstf_graphs'),
            debug=args.debug,
        )
        print("✓ 使用静态构建器 (NSTFBuilder)")
        builder.build_batch(to_process, dataset=args.dataset, max_procedures=args.max_procedures)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
