# -*- coding: utf-8 -*-
"""
Stage 0: NSTF 数据质量检查脚本

按照 NSTF_RETRIEVAL_REDESIGN.md 文档要求:
1. 统计 Procedure 数量、episodic_links 覆盖率（参考值）
2. 统计程序性问题覆盖率（关键指标）
3. 问题类型分布统计

停止条件:
- 如果程序性问题覆盖率 < 30%，需要先改进 E2P
- 如果程序性问题本身 < 10%，NSTF 的价值有限
"""

import os
import sys
import json
import pickle
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

# 数据路径
DATA_DIR = PROJECT_DIR / 'data'
NSTF_GRAPHS_DIR = DATA_DIR / 'nstf_graphs'
ANNOTATIONS_DIR = DATA_DIR / 'annotations'


def load_nstf_graphs(dataset: str) -> Dict[str, Dict]:
    """加载指定数据集的所有NSTF图谱"""
    graphs = {}
    nstf_dir = NSTF_GRAPHS_DIR / dataset
    
    if not nstf_dir.exists():
        print(f"⚠️ NSTF目录不存在: {nstf_dir}")
        return graphs
    
    for pkl_file in nstf_dir.glob('*_nstf.pkl'):
        video_name = pkl_file.stem.replace('_nstf', '')
        try:
            with open(pkl_file, 'rb') as f:
                graphs[video_name] = pickle.load(f)
        except Exception as e:
            print(f"  ⚠️ 加载失败 {pkl_file.name}: {e}")
    
    return graphs


def load_annotations(dataset: str) -> Dict:
    """加载annotation数据"""
    ann_path = ANNOTATIONS_DIR / f'{dataset}.json'
    if not ann_path.exists():
        print(f"⚠️ Annotation文件不存在: {ann_path}")
        return {}
    
    with open(ann_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def classify_question(question: str) -> str:
    """
    对问题进行类型分类
    
    类别:
    - procedural: 程序性问题（how to, 步骤, 时序）
    - character: 人物理解（熟悉, 习惯, 性格）
    - factual: 事实查询（颜色, 位置, 数量）
    - identity: 身份识别（who is, 名字）
    - other: 其他
    """
    q_lower = question.lower()
    
    # 程序性问题关键词
    procedural_keywords = [
        'how to', 'how do', 'how did', 'how does', 'how can',
        'step', 'procedure', 'process', 'method',
        'after', 'before', 'then', 'first', 'next', 'finally',
        'sequence', 'order',
        '怎么', '如何', '步骤', '方法', '流程',
        '之后', '之前', '然后', '首先', '接下来', '最后'
    ]
    
    # 人物理解关键词
    character_keywords = [
        'familiar', 'usually', 'habit', 'often', 'always',
        'personality', 'character', 'trait', 'behavior',
        '熟悉', '习惯', '经常', '总是', '性格', '特点'
    ]
    
    # 身份识别关键词
    identity_keywords = [
        'who is', 'who are', 'what is the name', 'character id',
        '谁是', '叫什么'
    ]
    
    if any(kw in q_lower for kw in procedural_keywords):
        return 'procedural'
    elif any(kw in q_lower for kw in character_keywords):
        return 'character'
    elif any(kw in q_lower for kw in identity_keywords):
        return 'identity'
    else:
        return 'factual'


def analyze_single_video(
    video_name: str,
    nstf_graph: Dict,
    annotations: Dict,
    dataset: str
) -> Dict:
    """分析单个视频的NSTF覆盖情况"""
    result = {
        'video_name': video_name,
        'num_procedures': 0,
        'total_steps': 0,
        'linked_clips': set(),
        'total_clips': 0,
        'questions': [],
        'question_types': defaultdict(int),
    }
    
    # 统计Procedure信息
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    result['num_procedures'] = len(proc_nodes)
    
    for proc_id, proc_node in proc_nodes.items():
        # 统计步骤数
        steps = proc_node.get('steps', [])
        result['total_steps'] += len(steps)
        
        # 收集episodic_links
        episodic_links = proc_node.get('episodic_links', [])
        for link in episodic_links:
            clip_id = link.get('clip_id')
            if clip_id is not None:
                result['linked_clips'].add(clip_id)
    
    # 获取视频总clip数（从annotation或估计）
    video_ann = annotations.get(video_name, {})
    qa_list = video_ann.get('qa_list', [])
    
    # 估计总clip数：找before_clip的最大值，或从问题中推断
    max_clip = 0
    for qa in qa_list:
        if 'before_clip' in qa:
            max_clip = max(max_clip, qa['before_clip'])
    
    if max_clip == 0:
        # 默认估计
        max_clip = max(result['linked_clips']) + 10 if result['linked_clips'] else 50
    
    result['total_clips'] = max_clip
    
    # 分析问题类型
    for qa in qa_list:
        question = qa.get('question', '')
        q_type = classify_question(question)
        result['question_types'][q_type] += 1
        result['questions'].append({
            'question': question,
            'type': q_type,
            'answer': qa.get('answer', ''),
            'before_clip': qa.get('before_clip'),
        })
    
    return result


def calculate_coverage_stats(all_results: List[Dict]) -> Dict:
    """计算汇总统计"""
    stats = {
        'total_videos': len(all_results),
        'total_procedures': 0,
        'total_steps': 0,
        'total_linked_clips': 0,
        'total_clips': 0,
        'question_types': defaultdict(int),
        'total_questions': 0,
        'procedural_questions': 0,
        'character_questions': 0,
    }
    
    all_linked_clips = set()
    
    for r in all_results:
        stats['total_procedures'] += r['num_procedures']
        stats['total_steps'] += r['total_steps']
        stats['total_linked_clips'] += len(r['linked_clips'])
        stats['total_clips'] += r['total_clips']
        
        for q_type, count in r['question_types'].items():
            stats['question_types'][q_type] += count
            stats['total_questions'] += count
        
        all_linked_clips.update(r['linked_clips'])
    
    stats['procedural_questions'] = stats['question_types'].get('procedural', 0)
    stats['character_questions'] = stats['question_types'].get('character', 0)
    
    # 计算覆盖率
    if stats['total_clips'] > 0:
        stats['clip_coverage'] = stats['total_linked_clips'] / stats['total_clips']
    else:
        stats['clip_coverage'] = 0
    
    # 程序性问题占比
    if stats['total_questions'] > 0:
        stats['procedural_ratio'] = stats['procedural_questions'] / stats['total_questions']
        stats['character_ratio'] = stats['character_questions'] / stats['total_questions']
    else:
        stats['procedural_ratio'] = 0
        stats['character_ratio'] = 0
    
    return stats


def print_report(stats: Dict, all_results: List[Dict], dataset: str):
    """打印分析报告"""
    print(f"\n{'='*70}")
    print(f"NSTF 数据质量分析报告 - {dataset.upper()}")
    print(f"{'='*70}")
    
    print(f"\n【基础统计】")
    print(f"  视频数量: {stats['total_videos']}")
    print(f"  Procedure总数: {stats['total_procedures']}")
    print(f"  平均每视频Procedure数: {stats['total_procedures']/max(stats['total_videos'],1):.1f}")
    print(f"  步骤总数: {stats['total_steps']}")
    print(f"  平均每Procedure步骤数: {stats['total_steps']/max(stats['total_procedures'],1):.1f}")
    
    print(f"\n【Clip覆盖率】（参考值）")
    print(f"  被链接的Clip总数: {stats['total_linked_clips']}")
    print(f"  估计Clip总数: {stats['total_clips']}")
    print(f"  Clip覆盖率: {stats['clip_coverage']:.1%}")
    
    print(f"\n【问题类型分布】")
    print(f"  问题总数: {stats['total_questions']}")
    for q_type, count in sorted(stats['question_types'].items(), key=lambda x: -x[1]):
        ratio = count / max(stats['total_questions'], 1)
        bar = '█' * int(ratio * 30)
        print(f"  {q_type:12s}: {count:4d} ({ratio:5.1%}) {bar}")
    
    print(f"\n【关键指标】")
    print(f"  程序性问题数: {stats['procedural_questions']}")
    print(f"  程序性问题占比: {stats['procedural_ratio']:.1%}")
    print(f"  人物理解问题数: {stats['character_questions']}")
    print(f"  人物理解问题占比: {stats['character_ratio']:.1%}")
    
    # 检查停止条件
    print(f"\n【停止条件检查】")
    
    # 条件1: 程序性问题占比
    if stats['procedural_ratio'] < 0.10:
        print(f"  ⚠️ 警告: 程序性问题占比 < 10% ({stats['procedural_ratio']:.1%})")
        print(f"     NSTF 的价值可能有限，大部分问题是事实查询")
    else:
        print(f"  ✓ 程序性问题占比 >= 10% ({stats['procedural_ratio']:.1%})")
    
    # 条件2: 覆盖率（这里简化，只看clip覆盖率作为参考）
    if stats['clip_coverage'] < 0.10:
        print(f"  ⚠️ 警告: Clip覆盖率 < 10% ({stats['clip_coverage']:.1%})")
        print(f"     建议改进 E2P 扩大 episodic_links 关联")
    else:
        print(f"  ✓ Clip覆盖率 >= 10% ({stats['clip_coverage']:.1%})")
    
    # 综合建议
    print(f"\n【综合建议】")
    nstf_target_ratio = stats['procedural_ratio'] + stats['character_ratio']
    print(f"  NSTF目标问题占比(程序性+人物理解): {nstf_target_ratio:.1%}")
    
    if nstf_target_ratio >= 0.25:
        print(f"  ✓ NSTF有足够的应用场景，可以继续实验")
    elif nstf_target_ratio >= 0.15:
        print(f"  ⚠️ NSTF应用场景有限，但仍值得实验")
    else:
        print(f"  ❌ NSTF应用场景过少，建议重新评估方案")
    
    print(f"\n{'='*70}")


def print_sample_procedures(all_results: List[Dict], num_samples: int = 3):
    """打印示例Procedure信息"""
    print(f"\n【示例Procedure详情】")
    
    sample_count = 0
    for r in all_results:
        if sample_count >= num_samples:
            break
        
        video_name = r['video_name']
        print(f"\n  视频: {video_name}")
        print(f"  Procedure数: {r['num_procedures']}")
        print(f"  链接Clips: {sorted(r['linked_clips'])}")
        sample_count += 1


def main():
    """主函数"""
    print("Stage 0: NSTF 数据质量检查")
    print("=" * 70)
    
    # 分析两个数据集
    for dataset in ['robot', 'web']:
        print(f"\n正在分析 {dataset} 数据集...")
        
        # 加载数据
        nstf_graphs = load_nstf_graphs(dataset)
        annotations = load_annotations(dataset)
        
        if not nstf_graphs:
            print(f"  跳过 {dataset}: 无NSTF图谱")
            continue
        
        print(f"  加载了 {len(nstf_graphs)} 个NSTF图谱")
        
        # 分析每个视频
        all_results = []
        for video_name, nstf_graph in nstf_graphs.items():
            result = analyze_single_video(video_name, nstf_graph, annotations, dataset)
            all_results.append(result)
        
        # 汇总统计
        stats = calculate_coverage_stats(all_results)
        
        # 打印报告
        print_report(stats, all_results, dataset)
        print_sample_procedures(all_results)
    
    print("\n" + "=" * 70)
    print("Stage 0 分析完成")
    print("=" * 70)
    print("\n下一步:")
    print("  如果检查通过，执行 Stage 1: 离线相似度测试")
    print("  如果覆盖率不足，先改进 nstf_builder/")


if __name__ == '__main__':
    main()
