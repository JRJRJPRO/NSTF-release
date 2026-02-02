#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Query Type 自动分类脚本

使用 GPT 将 QA 问题自动分类为 Factual / Procedural / Constrained 三类。

支持:
- web 数据集
- robot 数据集
- 增量标注（跳过已标注的问题）
- 断点续跑

用法:
    cd /data1/rongjiej/NSTF_MODEL
    
    # 标注 robot 数据集
    python experiments/query_type/classify_questions.py --dataset robot
    
    # 标注 web 数据集
    python experiments/query_type/classify_questions.py --dataset web
    
    # 预览模式（不调用 API，只显示统计）
    python experiments/query_type/classify_questions.py --dataset robot --dry-run
    
    # 指定输出文件
    python experiments/query_type/classify_questions.py --dataset robot --output data/my_output.json
"""

import os
import sys
import json
import time
import random
import argparse
from pathlib import Path
from typing import Dict, Optional
from collections import Counter, defaultdict
from datetime import datetime

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenAI API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai 包未安装，将只能使用本地规则分类")


# 分类 Prompt
CLASSIFICATION_PROMPT = """You are a question type classifier for a video understanding QA system.

Classify the following question into EXACTLY ONE category:

**1. Factual** - Direct recall of facts, entities, locations, or reasons
   - Keywords: who, what, when, where, why, which, is, are, does, did
   - Examples:
     * "What tool was used to cut vegetables?"
     * "Where did Abel put the yogurt?"
     * "Who is the person wearing a red shirt?"
     * "Why is Abel angry?"
   
**2. Procedural** - Process description, step sequencing, or how-to instructions
   - Keywords: how to, steps, procedure, process, method, sequence
   - Examples:
     * "What are the steps to make braised pork?"
     * "How to organize the drawer?"
     * "What is the process of cleaning the kitchen?"
     * "What should I do after taking out spices?"
   
**3. Constrained** - Alternative reasoning with constraints or missing resources
   - Keywords: without, no, missing, if...not, alternative, replace, instead
   - Examples:
     * "How to cook rice without a rice cooker?"
     * "What can I use if there is no knife?"
     * "How to organize the drawer without dividers?"
     * "What should I do if the pot is missing?"

**IMPORTANT RULES**:
1. If the question contains "without", "no", "missing", "if there is no" → **Constrained** (highest priority)
2. If the question starts with "how to" or asks for "steps", "process", "procedure" → **Procedural**
3. Otherwise (who/what/where/when/why/is/are/does) → **Factual**

Question: {question}

Output ONLY the category name (one word): Factual, Procedural, or Constrained
Do NOT include any explanation or punctuation."""


# API 配置
RATE_LIMIT_DELAY = 0.5  # 每次请求后等待（gpt-4o-mini: 0.3, gpt-4o: 1.0）
RATE_LIMIT_DELAY_GPT4O = 1.5  # gpt-4o 专用延迟
MAX_RETRIES = 5  # 最大重试次数
SAVE_INTERVAL = 50  # 每处理 N 个问题保存一次


def classify_by_rules(question: str) -> str:
    """基于规则的本地分类（作为 fallback）"""
    q_lower = question.lower()
    
    # Constrained 优先级最高
    constrained_keywords = [
        'without', 'no ', ' no ', 'missing', "if there is no", 
        "if don't", "if you don't", "if i don't", 
        'alternative', 'replace', 'instead of', 'substitute'
    ]
    if any(kw in q_lower for kw in constrained_keywords):
        return 'Constrained'
    
    # Procedural
    procedural_keywords = [
        'how to', 'how do', 'how can', 'how should',
        'steps', 'step by step', 'procedure', 'process', 
        'method', 'sequence', 'order of'
    ]
    if any(kw in q_lower for kw in procedural_keywords):
        return 'Procedural'
    
    # 默认 Factual
    return 'Factual'


def classify_question_gpt(question: str, client, model: str = "gpt-4o-mini") -> str:
    """使用 GPT 分类问题，带重试机制"""
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": CLASSIFICATION_PROMPT.format(question=question)
                }],
                temperature=0,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip()
            
            # 验证结果
            valid_types = {'Factual', 'Procedural', 'Constrained'}
            if result not in valid_types:
                # 尝试从结果中提取有效类型
                for vt in valid_types:
                    if vt.lower() in result.lower():
                        return vt
                # fallback 到规则分类
                return classify_by_rules(question)
            
            return result
            
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'rate_limit' in error_str.lower():
                wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                print(f"  ⏳ 速率限制，等待 {wait_time:.1f}s ({attempt+1}/{MAX_RETRIES})...")
                if attempt == 0:
                    # 首次遇到限制时打印完整错误
                    print(f"     详细错误: {error_str[:200]}")
                time.sleep(wait_time)
            else:
                print(f"  ❌ API 错误: {e}")
                break
    
    # 所有重试失败，使用本地规则
    return classify_by_rules(question)


def load_existing_results(output_path: Path) -> Dict:
    """加载已有的分类结果（用于断点续跑）"""
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    return {}


def get_type_query(qa: Dict) -> Optional[str]:
    """获取 QA 的 type_query 字段（兼容两种格式）
    
    - 旧格式: qa['type'] 是字符串 'Factual' (web 数据集已有标注)
    - 新格式: qa['type_query'] 是字符串 'Factual'
    """
    # 优先检查 type_query
    if 'type_query' in qa:
        return qa['type_query']
    
    # 兼容旧格式：如果 type 是字符串且是有效的 query type
    if 'type' in qa:
        t = qa['type']
        if isinstance(t, str) and t in {'Factual', 'Procedural', 'Constrained'}:
            return t
    
    return None


def save_results(data: Dict, output_path: Path):
    """保存结果（原子写入）"""
    tmp_path = output_path.with_suffix('.json.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp_path.replace(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='Query Type 自动分类',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
    python experiments/query_type/classify_questions.py --dataset robot
    python experiments/query_type/classify_questions.py --dataset web --dry-run
    python experiments/query_type/classify_questions.py --dataset robot --local-only
'''
    )
    
    parser.add_argument('--dataset', type=str, required=True,
                        choices=['robot', 'web'],
                        help='数据集类型')
    parser.add_argument('--input', type=str, default=None,
                        help='输入文件路径（默认 data/annotations/<dataset>.json）')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径（默认 experiments/query_type/data/all_<dataset>_questions_typed.json）')
    parser.add_argument('--model', type=str, default='gpt-4o-mini',
                        help='OpenAI 模型（默认 gpt-4o-mini，更便宜）')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式，不调用 API')
    parser.add_argument('--local-only', action='store_true',
                        help='只使用本地规则分类，不调用 API')
    parser.add_argument('--force', action='store_true',
                        help='强制重新分类所有问题（不跳过已标注的）')
    
    args = parser.parse_args()
    
    # 路径设置
    script_dir = Path(__file__).parent.resolve()
    nstf_model_dir = script_dir.parent.parent
    
    # 输入路径
    if args.input:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = nstf_model_dir / input_path
    else:
        input_path = nstf_model_dir / 'data' / 'annotations' / f'{args.dataset}.json'
    
    # 输出路径
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = nstf_model_dir / output_path
    else:
        output_path = script_dir / 'data' / f'all_{args.dataset}_questions_typed.json'
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Query Type 自动分类")
    print("=" * 60)
    print(f"数据集: {args.dataset}")
    print(f"输入: {input_path}")
    print(f"输出: {output_path}")
    print(f"模型: {args.model}")
    if args.dry_run:
        print("⚠️  预览模式：不会调用 API 或修改文件")
    if args.local_only:
        print("⚠️  本地模式：只使用规则分类")
    print()
    
    # 检查输入文件
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        return 1
    
    # 加载数据
    print("[1] 加载数据...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_videos = len(data)
    total_questions = sum(len(v.get('qa_list', [])) for v in data.values())
    print(f"    视频数: {total_videos}")
    print(f"    问题数: {total_questions}")
    
    # 加载已有结果（断点续跑）
    existing_results = {}
    if not args.force and output_path.exists():
        existing_results = load_existing_results(output_path)
        existing_count = sum(
            1 for v in existing_results.values() 
            for qa in v.get('qa_list', []) 
            if get_type_query(qa)
        )
        print(f"    已有结果: {existing_count} 个问题已标注")
    
    # 初始化 OpenAI 客户端
    client = None
    if not args.dry_run and not args.local_only:
        if not OPENAI_AVAILABLE:
            print("❌ openai 包未安装，请使用 --local-only 或 --dry-run")
            return 1
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ 未设置 OPENAI_API_KEY 环境变量")
            return 1
        
        client = OpenAI(api_key=api_key)
        print(f"    ✓ OpenAI 客户端已初始化")
    
    # 开始分类
    print()
    print("[2] 开始分类...")
    
    results = {}
    stats = Counter()
    processed = 0
    skipped = 0
    
    for video_id, video_data in data.items():
        qa_list = video_data.get('qa_list', [])
        if not qa_list:
            continue
        
        # 检查是否有已有结果
        existing_video = existing_results.get(video_id, {})
        existing_qa_map = {
            qa.get('question_id'): get_type_query(qa)
            for qa in existing_video.get('qa_list', [])
        }
        
        typed_qa_list = []
        
        for qa in qa_list:
            question = qa['question']
            question_id = qa.get('question_id', '')
            
            # 检查是否已有标注
            existing_type = existing_qa_map.get(question_id)
            if existing_type and not args.force:
                # 使用已有标注
                typed_qa = qa.copy()
                typed_qa['type_query'] = existing_type
                typed_qa_list.append(typed_qa)
                stats[existing_type] += 1
                skipped += 1
                continue
            
            # 需要分类
            if args.dry_run:
                # 预览模式：使用规则分类
                q_type = classify_by_rules(question)
            elif args.local_only:
                # 本地模式
                q_type = classify_by_rules(question)
            else:
                # GPT 分类
                q_type = classify_question_gpt(question, client, args.model)
                # 根据模型选择延迟
                delay = RATE_LIMIT_DELAY_GPT4O if 'gpt-4o' == args.model else RATE_LIMIT_DELAY
                time.sleep(delay)
            
            typed_qa = qa.copy()
            typed_qa['type_query'] = q_type
            typed_qa_list.append(typed_qa)
            
            stats[q_type] += 1
            processed += 1
            
            # 进度显示
            if processed % 100 == 0:
                print(f"    已处理: {processed} 个问题")
        
        # 保存视频结果
        results[video_id] = {
            **video_data,
            'qa_list': typed_qa_list
        }
        
        # 定期保存（断点续跑支持）
        if not args.dry_run and processed > 0 and processed % SAVE_INTERVAL == 0:
            save_results(results, output_path)
            print(f"    💾 已保存 ({processed} 个问题)")
    
    # 最终保存
    if not args.dry_run:
        save_results(results, output_path)
    
    # 统计
    print()
    print("=" * 60)
    print("分类完成")
    print("=" * 60)
    print(f"新处理: {processed} 个问题")
    print(f"跳过（已标注）: {skipped} 个问题")
    print()
    print("类型分布:")
    for q_type in ['Factual', 'Procedural', 'Constrained']:
        count = stats.get(q_type, 0)
        pct = count / sum(stats.values()) * 100 if stats else 0
        print(f"  {q_type:12s}: {count:5d} ({pct:5.1f}%)")
    
    if not args.dry_run:
        print()
        print(f"✓ 结果已保存: {output_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
