#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query Type 标注合并脚本

将 all_web_questions_typed.json 中的 query type 标注合并到原始 annotation 文件中。

合并逻辑：
1. 原始 annotation 中的 `type` 字段保持不变（即 type_original 的来源）
2. 从 all_web_questions_typed.json 读取新的 type 标注，作为 `type_query` 字段添加
3. 通过 question_id + question 匹配问题
4. 没有 query type 标注的问题，type_query 字段设为 null

用法:
    cd /data1/rongjiej/NSTF_MODEL
    python experiments/query_type/merge_query_type.py
    
    # 预览模式（不实际修改）
    python experiments/query_type/merge_query_type.py --dry-run
    
    # 指定输出文件
    python experiments/query_type/merge_query_type.py --output data/annotations/web_merged.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def load_json(path: str) -> dict:
    """加载 JSON 文件"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict, path: str, backup: bool = True):
    """保存 JSON 文件（可选备份）"""
    path = Path(path)
    
    # 备份原文件
    if backup and path.exists():
        backup_path = path.with_suffix(f'.json.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        with open(path, 'r', encoding='utf-8') as f:
            original = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original)
        print(f"✓ 备份原文件: {backup_path}")
    
    # 保存新文件
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✓ 保存文件: {path}")


def build_query_type_map(typed_data: dict) -> dict:
    """
    从 all_xxx_questions_typed.json 构建 query type 映射
    
    Returns:
        {(question_id, question): type_query}
    """
    type_map = {}
    
    for video_id, video_data in typed_data.items():
        for qa in video_data.get('qa_list', []):
            question_id = qa.get('question_id', '')
            question = qa.get('question', '')
            type_query = qa.get('type_query')  # 字符串格式，如 "Factual"
            
            if question_id and question and type_query:
                # 使用 (question_id, question) 作为复合键
                key = (question_id, question)
                type_map[key] = type_query
    
    return type_map


def merge_annotations(original_data: dict, type_map: dict) -> tuple:
    """
    合并 query type 到原始 annotation
    
    Returns:
        (merged_data, stats)
    """
    merged = {}
    stats = {
        'total_videos': 0,
        'total_questions': 0,
        'matched': 0,
        'unmatched': 0,
    }
    
    for video_id, video_data in original_data.items():
        stats['total_videos'] += 1
        
        merged_video = {
            'video_url': video_data.get('video_url', ''),
            'video_path': video_data.get('video_path', ''),
            'mem_path': video_data.get('mem_path', ''),
            'qa_list': []
        }
        
        for qa in video_data.get('qa_list', []):
            stats['total_questions'] += 1
            
            question_id = qa.get('question_id', '')
            question = qa.get('question', '')
            
            # 查找 query type
            key = (question_id, question)
            type_query = type_map.get(key)
            
            if type_query:
                stats['matched'] += 1
            else:
                stats['unmatched'] += 1
            
            # 构建新的 qa 条目
            merged_qa = {
                'question': qa.get('question', ''),
                'answer': qa.get('answer', ''),
                'question_id': question_id,
                'reasoning': qa.get('reasoning', ''),
                'type': qa.get('type', []),  # 保留原始 type（数组格式）
                'type_query': type_query,     # 新增 query type（字符串或 null）
            }
            
            # 保留其他可能存在的字段
            for key in qa:
                if key not in merged_qa:
                    merged_qa[key] = qa[key]
            
            merged_video['qa_list'].append(merged_qa)
        
        merged[video_id] = merged_video
    
    return merged, stats


def main():
    parser = argparse.ArgumentParser(
        description='合并 Query Type 标注到原始 annotation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    python experiments/query_type/merge_query_type.py
    python experiments/query_type/merge_query_type.py --dry-run
    python experiments/query_type/merge_query_type.py --output data/annotations/web_merged.json
'''
    )
    
    parser.add_argument('--original', type=str, 
                        default='data/annotations/web.json',
                        help='原始 annotation 文件路径')
    parser.add_argument('--typed', type=str,
                        default='experiments/query_type/data/all_web_questions_typed.json',
                        help='带 query type 标注的文件路径')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径（默认覆盖原文件）')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式，不实际修改文件')
    parser.add_argument('--no-backup', action='store_true',
                        help='不备份原文件')
    
    args = parser.parse_args()
    
    # 确定路径（基于 NSTF_MODEL 目录）
    script_dir = Path(__file__).parent.resolve()
    nstf_model_dir = script_dir.parent.parent  # experiments/query_type -> NSTF_MODEL
    
    original_path = nstf_model_dir / args.original
    typed_path = nstf_model_dir / args.typed
    output_path = Path(args.output) if args.output else original_path
    if not output_path.is_absolute():
        output_path = nstf_model_dir / output_path
    
    print("="*60)
    print("Query Type 标注合并")
    print("="*60)
    print(f"原始文件: {original_path}")
    print(f"标注文件: {typed_path}")
    print(f"输出文件: {output_path}")
    if args.dry_run:
        print("⚠️  预览模式：不会修改文件")
    print()
    
    # 检查文件存在
    if not original_path.exists():
        print(f"❌ 原始文件不存在: {original_path}")
        return 1
    if not typed_path.exists():
        print(f"❌ 标注文件不存在: {typed_path}")
        return 1
    
    # 加载数据
    print("[1] 加载数据...")
    original_data = load_json(original_path)
    typed_data = load_json(typed_path)
    print(f"    原始 annotation: {len(original_data)} 个视频")
    print(f"    Query Type 标注: {len(typed_data)} 个视频")
    
    # 构建映射
    print("\n[2] 构建 Query Type 映射...")
    type_map = build_query_type_map(typed_data)
    print(f"    共 {len(type_map)} 个问题有 Query Type 标注")
    
    # 统计 type 分布
    type_dist = defaultdict(int)
    for t in type_map.values():
        type_dist[t] += 1
    print("    类型分布:")
    for t, count in sorted(type_dist.items()):
        print(f"      - {t}: {count}")
    
    # 合并
    print("\n[3] 合并标注...")
    merged_data, stats = merge_annotations(original_data, type_map)
    
    print(f"    总视频数: {stats['total_videos']}")
    print(f"    总问题数: {stats['total_questions']}")
    print(f"    匹配成功: {stats['matched']}")
    print(f"    未匹配: {stats['unmatched']}")
    
    # 保存
    if args.dry_run:
        print("\n[4] 预览模式，跳过保存")
        print("\n示例输出（第一个视频的第一个问题）:")
        first_video = list(merged_data.keys())[0]
        first_qa = merged_data[first_video]['qa_list'][0]
        print(json.dumps(first_qa, ensure_ascii=False, indent=2))
    else:
        print("\n[4] 保存文件...")
        save_json(merged_data, output_path, backup=not args.no_backup)
    
    print("\n" + "="*60)
    print("完成!")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
