#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
索引重建脚本

从详细结果文件重建索引文件。
索引是加速缓存，可随时通过本脚本重建。

用法:
    cd /data1/rongjiej/NSTF_MODEL
    
    # 重建所有索引
    python results/rebuild_index.py
    
    # 重建指定 method 和 dataset 的索引
    python results/rebuild_index.py --method baseline --dataset web
    
    # 列出可用的 method
    python results/rebuild_index.py --list
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime


# 支持的 method 列表
METHODS = ['baseline', 'nstf', 'ablation_prototype', 'ablation_structure']
DATASETS = ['robot', 'web']


def extract_index_entry(result: dict) -> dict:
    """从详细结果中提取索引条目"""
    return {
        'id': result['id'],
        'video_id': result['video_id'],
        'status': result.get('status', 'success'),
        'type_original': result.get('type_original', []),
        'type_query': result.get('type_query'),
        'gpt_eval': result.get('gpt_eval', False),
        'num_rounds': result.get('num_rounds', 0),
        'elapsed_time_sec': result.get('elapsed_time_sec', 0),
        'search_count': result.get('search_count', 0),
        'timestamp': result.get('timestamp'),
    }


def rebuild_index(base_dir: Path, method: str, dataset: str) -> int:
    """
    重建指定 method + dataset 的索引
    
    Returns:
        重建的条目数
    """
    method_dir = base_dir / method
    dataset_dir = method_dir / dataset
    index_file = method_dir / f'index_{dataset}.jsonl'
    
    if not dataset_dir.exists():
        print(f"  跳过: {dataset_dir} 不存在")
        return 0
    
    # 收集所有结果文件
    entries = []
    for video_dir in dataset_dir.iterdir():
        if video_dir.is_dir():
            for json_file in video_dir.glob('*.json'):
                # 跳过临时文件
                if json_file.name.endswith('.tmp'):
                    continue
                
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                    entry = extract_index_entry(result)
                    entries.append(entry)
                except Exception as e:
                    print(f"  ⚠️ 读取失败: {json_file} - {e}")
    
    if not entries:
        print(f"  跳过: {method}/{dataset} 无结果文件")
        return 0
    
    # 按 id 排序
    entries.sort(key=lambda x: x['id'])
    
    # 写入索引文件
    method_dir.mkdir(parents=True, exist_ok=True)
    with open(index_file, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"  ✓ {method}/{dataset}: {len(entries)} 条")
    return len(entries)


def list_available(base_dir: Path):
    """列出可用的 method 和统计信息"""
    print("\n可用的结果目录:")
    print("-" * 60)
    
    total = 0
    for method in METHODS:
        method_dir = base_dir / method
        if not method_dir.exists():
            continue
        
        for dataset in DATASETS:
            dataset_dir = method_dir / dataset
            if not dataset_dir.exists():
                continue
            
            # 统计文件数
            count = 0
            for video_dir in dataset_dir.iterdir():
                if video_dir.is_dir():
                    count += len(list(video_dir.glob('*.json')))
            
            if count > 0:
                # 检查索引是否存在
                index_file = method_dir / f'index_{dataset}.jsonl'
                index_status = "✓" if index_file.exists() else "✗"
                print(f"  {method}/{dataset}: {count} 个结果 [索引: {index_status}]")
                total += count
    
    print("-" * 60)
    print(f"总计: {total} 个结果文件")


def main():
    parser = argparse.ArgumentParser(
        description='重建索引文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python results/rebuild_index.py              # 重建所有索引
  python results/rebuild_index.py --method baseline --dataset web
  python results/rebuild_index.py --list       # 列出可用目录
'''
    )
    
    parser.add_argument('--method', type=str, default=None,
                        choices=METHODS,
                        help='指定 method（不指定则重建所有）')
    parser.add_argument('--dataset', type=str, default=None,
                        choices=DATASETS,
                        help='指定 dataset（不指定则重建所有）')
    parser.add_argument('--list', action='store_true',
                        help='列出可用的 method 和统计信息')
    
    args = parser.parse_args()
    
    # 确定 results 目录
    script_dir = Path(__file__).parent.resolve()
    base_dir = script_dir  # rebuild_index.py 就在 results/ 目录下
    
    # 列出模式
    if args.list:
        list_available(base_dir)
        return 0
    
    # 确定要重建的范围
    methods = [args.method] if args.method else METHODS
    datasets = [args.dataset] if args.dataset else DATASETS
    
    print("="*60)
    print("重建索引")
    print("="*60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目录: {base_dir}")
    print()
    
    total_count = 0
    for method in methods:
        for dataset in datasets:
            count = rebuild_index(base_dir, method, dataset)
            total_count += count
    
    print()
    print(f"完成: 共重建 {total_count} 条索引")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
