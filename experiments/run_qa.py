#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问答测试入口脚本 - qa_system 命令行入口

支持两种存储模式：
1. 结构化存储（默认）：按 STORAGE_SCHEMA.md 规范存储到 results/<method>/<dataset>/
2. 自定义输出（--output）：旧的 JSONL 模式，用于临时测试
"""

import os
import sys
import argparse
from pathlib import Path

# === 设置工作目录和路径 ===
# 通过相对路径确定 NSTF_MODEL 目录（本脚本在 experiments/ 下）
EXPERIMENTS_DIR = Path(__file__).parent.resolve()
NSTF_MODEL_DIR = EXPERIMENTS_DIR.parent

# 切换到 NSTF_MODEL 目录（configs/ 在这里）
os.chdir(NSTF_MODEL_DIR)

# 添加路径并加载环境
sys.path.insert(0, str(NSTF_MODEL_DIR))
from env_setup import setup_all
setup_all()

from qa_system import QARunner
from qa_system.config import QAConfig, get_ablation_config


def resolve_path(path_str: str) -> str:
    """将相对路径转为绝对路径（基于当前工作目录 NSTF_MODEL）"""
    if path_str is None:
        return None
    p = Path(path_str)
    if p.is_absolute():
        return str(p)
    # 相对路径基于当前工作目录 (NSTF_MODEL)
    return str(NSTF_MODEL_DIR / p)


def main():
    parser = argparse.ArgumentParser(
        description='NSTF问答测试',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # Baseline 测试
  python experiments/run_qa.py --dataset web --ablation baseline

  # NSTF Procedure级别检索（新设计）
  python experiments/run_qa.py --dataset robot --ablation nstf_level --limit 100

  # NSTF 测试，带 Query Type 标注
  python experiments/run_qa.py --dataset web --query-type-file experiments/query_type/data/all_web_questions_typed.json

  # 强制重跑
  python experiments/run_qa.py --dataset web --ablation baseline --force

  # 自定义输出（旧模式）
  python experiments/run_qa.py --dataset web --output my_results.jsonl
'''
    )
    
    # 数据配置
    parser.add_argument('--dataset', type=str, default='web',
                        choices=['robot', 'web'],
                        help='数据集类型')
    parser.add_argument('--data-file', type=str, default=None,
                        help='自定义问答数据文件 (JSON)')
    parser.add_argument('--video-list', type=str, default=None,
                        help='视频列表文件 (JSON)')
    parser.add_argument('--videos', type=str, default=None,
                        help='指定视频ID，逗号分隔')
    parser.add_argument('--limit', type=int, default=None,
                        help='最多测试题数')
    
    # Query Type 标注
    parser.add_argument('--query-type-file', type=str, default=None,
                        help='Query Type 标注文件路径（用于合并 type_query 字段）')
    
    # 模式配置  
    parser.add_argument('--ablation', type=str, default=None,
                        choices=['baseline', 'prototype', 'structure', 'full_nstf', 'nstf_level', 'nstf_node'],
                        help='检索策略: baseline(原始M3), nstf_level(Procedure增强), full_nstf(原NSTF), nstf_node(节点级)')
    
    # 输出配置
    parser.add_argument('--output', type=str, default=None,
                        help='自定义输出文件路径（指定则使用旧的 JSONL 模式）')
    parser.add_argument('--no-resume', action='store_true',
                        help='不从断点续跑（仅 --output 模式有效）')
    parser.add_argument('--force', action='store_true',
                        help='强制覆盖已有结果（仅结构化存储模式有效）')
    
    # LLM配置 - 默认从 .env 读取
    parser.add_argument('--llm-source', type=str, default=None,
                        choices=['cloud', 'local'],
                        help='LLM来源，默认从 .env 的 CONTROL_LLM_SOURCE 读取')
    parser.add_argument('--llm-model', type=str, default=None,
                        help='LLM模型名称')
    
    args = parser.parse_args()
    
    # 配置
    if args.ablation:
        config = get_ablation_config(args.ablation)
    else:
        config = QAConfig.load_default()
    
    # 只有用户显式指定时才覆盖配置，否则使用 .env 中的设置
    if args.llm_source is not None:
        config.llm_source = args.llm_source
    if args.llm_model is not None:
        config.llm_model = args.llm_model
    
    # 确定存储模式
    use_structured = (args.output is None)
    from qa_system.runner import get_method_name
    method_name = get_method_name(config.ablation_mode)
    
    # 打印配置
    print("="*60)
    print("NSTF 问答测试")
    print("="*60)
    print(f"数据集: {args.dataset}")
    if args.data_file:
        print(f"数据文件: {args.data_file}")
    if args.video_list:
        print(f"视频列表: {args.video_list}")
    print(f"模式: {method_name}")
    print(f"LLM: {config.llm_source} / {config.llm_model}")
    if args.query_type_file:
        print(f"Query Type 文件: {args.query_type_file}")
    if args.limit:
        print(f"限制: {args.limit} 题")
    
    if use_structured:
        print(f"存储模式: 结构化存储 (results/{method_name}/{args.dataset}/)")
        if args.force:
            print(f"⚠️  强制模式: 将覆盖已有结果")
    else:
        print(f"存储模式: 自定义输出 ({args.output})")
    print("="*60)
    
    # 解析路径（相对路径基于 NSTF_MODEL 目录）
    data_file = resolve_path(args.data_file)
    video_list_file = resolve_path(args.video_list)
    output_file = resolve_path(args.output)
    query_type_file = resolve_path(args.query_type_file)
    
    # 运行
    runner = QARunner(config=config)
    
    video_names = None
    if args.videos:
        video_names = [v.strip() for v in args.videos.split(',')]
    
    result = runner.run(
        dataset=args.dataset,
        video_names=video_names,
        video_list_file=video_list_file,
        data_file=data_file,
        query_type_file=query_type_file,
        limit=args.limit,
        output_file=output_file,
        resume=not args.no_resume,
        force=args.force,
    )
    
    return 0 if result['accuracy'] > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
