#!/usr/bin/env python3
"""
Comprehensive NSTF vs Baseline Analysis Script
==============================================
分析 query_type 实验中 NSTF 和 Baseline 的性能差异

问题类型：
- Factual: 事实性问题 (who/what/where/when)
- Procedural: 程序性问题 (how to/steps)
- Constrained: 约束性问题 (without X/if missing)

输出内容：
1. 总体准确率统计
2. 分类型准确率统计  
3. 对比分析（双对/双错/单方正确）
4. 详细案例研究
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import random

# 配置文件路径
NSTF_FILE = "results/nstf_new.json"
BASELINE_FILE = "results/baseline_new.jsonl"
OUTPUT_REPORT = "COMPREHENSIVE_ANALYSIS_REPORT.md"

# 问题类型（三种）
QUESTION_TYPES = ["Factual", "Procedural", "Constrained"]


def load_jsonl(filepath: str) -> List[Dict]:
    """加载JSONL格式文件"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def load_json(filepath: str) -> List[Dict]:
    """加载JSON格式文件（可能是JSONL）"""
    # 先尝试作为JSONL加载
    try:
        return load_jsonl(filepath)
    except:
        pass
    # 尝试作为标准JSON加载
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_question_id(item: Dict) -> str:
    """获取问题ID"""
    return item.get("id", item.get("question_id", ""))


def is_correct(item: Dict) -> bool:
    """判断回答是否正确"""
    gpt_eval = item.get("gpt_eval", False)
    if isinstance(gpt_eval, bool):
        return gpt_eval
    if isinstance(gpt_eval, str):
        return gpt_eval.lower() in ["true", "yes", "1", "correct"]
    return False


def get_question_type(item: Dict) -> str:
    """获取问题类型"""
    return item.get("type", "Unknown")


def analyze_results() -> Dict[str, Any]:
    """执行综合分析"""
    
    print("=" * 60)
    print("NSTF vs Baseline 综合分析")
    print("=" * 60)
    
    # 加载数据
    print("\n[1] 加载数据...")
    nstf_data = load_json(NSTF_FILE)
    baseline_data = load_jsonl(BASELINE_FILE)
    
    print(f"  NSTF 数据量: {len(nstf_data)}")
    print(f"  Baseline 数据量: {len(baseline_data)}")
    
    # 建立索引
    nstf_by_id = {get_question_id(item): item for item in nstf_data}
    baseline_by_id = {get_question_id(item): item for item in baseline_data}
    
    # 找到共同的问题
    common_ids = set(nstf_by_id.keys()) & set(baseline_by_id.keys())
    print(f"  共同问题数: {len(common_ids)}")
    
    # 初始化统计
    stats = {
        "total": {
            "count": 0,
            "nstf_correct": 0,
            "baseline_correct": 0,
            "both_correct": 0,
            "both_wrong": 0,
            "nstf_only_correct": 0,
            "baseline_only_correct": 0
        }
    }
    
    for qtype in QUESTION_TYPES:
        stats[qtype] = {
            "count": 0,
            "nstf_correct": 0,
            "baseline_correct": 0,
            "both_correct": 0,
            "both_wrong": 0,
            "nstf_only_correct": 0,
            "baseline_only_correct": 0
        }
    
    # 收集案例
    cases = {
        "both_correct": [],
        "both_wrong": [],
        "nstf_only_correct": [],
        "baseline_only_correct": []
    }
    
    # 分析每个问题
    print("\n[2] 分析问题...")
    for qid in common_ids:
        nstf_item = nstf_by_id[qid]
        baseline_item = baseline_by_id[qid]
        
        nstf_correct = is_correct(nstf_item)
        baseline_correct = is_correct(baseline_item)
        qtype = get_question_type(nstf_item)
        
        # 确保类型在预定义列表中
        if qtype not in QUESTION_TYPES:
            qtype = "Unknown"
            if "Unknown" not in stats:
                stats["Unknown"] = {
                    "count": 0, "nstf_correct": 0, "baseline_correct": 0,
                    "both_correct": 0, "both_wrong": 0,
                    "nstf_only_correct": 0, "baseline_only_correct": 0
                }
        
        # 更新统计
        for key in ["total", qtype]:
            if key in stats:
                stats[key]["count"] += 1
                if nstf_correct:
                    stats[key]["nstf_correct"] += 1
                if baseline_correct:
                    stats[key]["baseline_correct"] += 1
                    
                if nstf_correct and baseline_correct:
                    stats[key]["both_correct"] += 1
                elif not nstf_correct and not baseline_correct:
                    stats[key]["both_wrong"] += 1
                elif nstf_correct and not baseline_correct:
                    stats[key]["nstf_only_correct"] += 1
                elif not nstf_correct and baseline_correct:
                    stats[key]["baseline_only_correct"] += 1
        
        # 收集案例
        case_info = {
            "id": qid,
            "type": qtype,
            "question": nstf_item.get("question", ""),
            "answer": nstf_item.get("answer", ""),
            "video_id": nstf_item.get("video_id", ""),
            "nstf_response": nstf_item.get("response", ""),
            "baseline_response": baseline_item.get("response", ""),
            "nstf_correct": nstf_correct,
            "baseline_correct": baseline_correct
        }
        
        if nstf_correct and baseline_correct:
            cases["both_correct"].append(case_info)
        elif not nstf_correct and not baseline_correct:
            cases["both_wrong"].append(case_info)
        elif nstf_correct and not baseline_correct:
            cases["nstf_only_correct"].append(case_info)
        else:
            cases["baseline_only_correct"].append(case_info)
    
    return stats, cases


def generate_report(stats: Dict, cases: Dict) -> str:
    """生成分析报告"""
    
    report = []
    report.append("# NSTF vs Baseline 综合分析报告")
    report.append("")
    report.append("## 概述")
    report.append("")
    report.append("本报告对比分析了 **NSTF (Neural-Symbolic Task Flow)** 模型和 **Baseline** 模型在视频问答任务上的表现。")
    report.append("")
    report.append("### 问题类型说明")
    report.append("")
    report.append("| 类型 | 说明 | 示例 |")
    report.append("|------|------|------|")
    report.append("| **Factual** | 事实性问题，询问具体信息 | Who/What/Where/When 类问题 |")
    report.append("| **Procedural** | 程序性问题，询问操作步骤 | How to 类问题 |")
    report.append("| **Constrained** | 约束性问题，涉及条件限制 | Without X / If missing 类问题 |")
    report.append("")
    
    # 总体统计
    report.append("---")
    report.append("")
    report.append("## 1. 总体统计")
    report.append("")
    
    total = stats["total"]
    nstf_acc = total["nstf_correct"] / total["count"] * 100 if total["count"] > 0 else 0
    baseline_acc = total["baseline_correct"] / total["count"] * 100 if total["count"] > 0 else 0
    
    report.append(f"**总问题数**: {total['count']}")
    report.append("")
    report.append("| 指标 | NSTF | Baseline | 差异 |")
    report.append("|------|------|----------|------|")
    report.append(f"| 正确数 | {total['nstf_correct']} | {total['baseline_correct']} | {total['nstf_correct'] - total['baseline_correct']:+d} |")
    report.append(f"| 准确率 | {nstf_acc:.2f}% | {baseline_acc:.2f}% | {nstf_acc - baseline_acc:+.2f}% |")
    report.append("")
    
    # 对比分析
    report.append("### 详细对比")
    report.append("")
    report.append("| 情况 | 数量 | 占比 |")
    report.append("|------|------|------|")
    report.append(f"| 双方都正确 (Both Correct) | {total['both_correct']} | {total['both_correct']/total['count']*100:.2f}% |")
    report.append(f"| 双方都错误 (Both Wrong) | {total['both_wrong']} | {total['both_wrong']/total['count']*100:.2f}% |")
    report.append(f"| 仅NSTF正确 (NSTF Only) | {total['nstf_only_correct']} | {total['nstf_only_correct']/total['count']*100:.2f}% |")
    report.append(f"| 仅Baseline正确 (Baseline Only) | {total['baseline_only_correct']} | {total['baseline_only_correct']/total['count']*100:.2f}% |")
    report.append("")
    
    # 分类型统计
    report.append("---")
    report.append("")
    report.append("## 2. 分类型统计")
    report.append("")
    
    report.append("### 准确率对比")
    report.append("")
    report.append("| 类型 | 问题数 | NSTF准确率 | Baseline准确率 | NSTF优势 |")
    report.append("|------|--------|------------|----------------|----------|")
    
    for qtype in QUESTION_TYPES:
        if qtype in stats and stats[qtype]["count"] > 0:
            s = stats[qtype]
            nstf_acc = s["nstf_correct"] / s["count"] * 100
            baseline_acc = s["baseline_correct"] / s["count"] * 100
            diff = nstf_acc - baseline_acc
            diff_str = f"{diff:+.2f}%"
            if diff > 0:
                diff_str = f"**{diff_str}** ↑"
            elif diff < 0:
                diff_str = f"*{diff_str}* ↓"
            report.append(f"| {qtype} | {s['count']} | {nstf_acc:.2f}% | {baseline_acc:.2f}% | {diff_str} |")
    
    report.append("")
    
    # 分类型详细对比
    report.append("### 分类型详细对比")
    report.append("")
    
    for qtype in QUESTION_TYPES:
        if qtype in stats and stats[qtype]["count"] > 0:
            s = stats[qtype]
            report.append(f"#### {qtype} 类问题")
            report.append("")
            report.append(f"- 总数: {s['count']}")
            report.append(f"- 双方都正确: {s['both_correct']} ({s['both_correct']/s['count']*100:.1f}%)")
            report.append(f"- 双方都错误: {s['both_wrong']} ({s['both_wrong']/s['count']*100:.1f}%)")
            report.append(f"- 仅NSTF正确: {s['nstf_only_correct']} ({s['nstf_only_correct']/s['count']*100:.1f}%)")
            report.append(f"- 仅Baseline正确: {s['baseline_only_correct']} ({s['baseline_only_correct']/s['count']*100:.1f}%)")
            report.append("")
    
    # 案例分析
    report.append("---")
    report.append("")
    report.append("## 3. 典型案例分析")
    report.append("")
    
    # NSTF优势案例
    report.append("### 3.1 NSTF 优势案例 (仅NSTF正确)")
    report.append("")
    report.append(f"共 {len(cases['nstf_only_correct'])} 个案例")
    report.append("")
    
    # 按类型分组展示
    nstf_cases_by_type = defaultdict(list)
    for case in cases["nstf_only_correct"]:
        nstf_cases_by_type[case["type"]].append(case)
    
    for qtype in QUESTION_TYPES:
        type_cases = nstf_cases_by_type.get(qtype, [])
        if type_cases:
            report.append(f"#### {qtype} 类 ({len(type_cases)} 个)")
            report.append("")
            # 展示前3个案例
            for case in type_cases[:3]:
                report.append(f"**问题ID**: `{case['id']}`")
                report.append("")
                report.append(f"**视频ID**: `{case['video_id']}`")
                report.append("")
                report.append(f"**问题**: {case['question']}")
                report.append("")
                report.append(f"**标准答案**: {case['answer']}")
                report.append("")
                report.append(f"**NSTF回答** ✓: {case['nstf_response'][:500]}..." if len(case['nstf_response']) > 500 else f"**NSTF回答** ✓: {case['nstf_response']}")
                report.append("")
                report.append(f"**Baseline回答** ✗: {case['baseline_response'][:500]}..." if len(case['baseline_response']) > 500 else f"**Baseline回答** ✗: {case['baseline_response']}")
                report.append("")
                report.append("---")
                report.append("")
    
    # Baseline优势案例
    report.append("### 3.2 Baseline 优势案例 (仅Baseline正确)")
    report.append("")
    report.append(f"共 {len(cases['baseline_only_correct'])} 个案例")
    report.append("")
    
    baseline_cases_by_type = defaultdict(list)
    for case in cases["baseline_only_correct"]:
        baseline_cases_by_type[case["type"]].append(case)
    
    for qtype in QUESTION_TYPES:
        type_cases = baseline_cases_by_type.get(qtype, [])
        if type_cases:
            report.append(f"#### {qtype} 类 ({len(type_cases)} 个)")
            report.append("")
            # 展示前3个案例
            for case in type_cases[:3]:
                report.append(f"**问题ID**: `{case['id']}`")
                report.append("")
                report.append(f"**视频ID**: `{case['video_id']}`")
                report.append("")
                report.append(f"**问题**: {case['question']}")
                report.append("")
                report.append(f"**标准答案**: {case['answer']}")
                report.append("")
                report.append(f"**NSTF回答** ✗: {case['nstf_response'][:500]}..." if len(case['nstf_response']) > 500 else f"**NSTF回答** ✗: {case['nstf_response']}")
                report.append("")
                report.append(f"**Baseline回答** ✓: {case['baseline_response'][:500]}..." if len(case['baseline_response']) > 500 else f"**Baseline回答** ✓: {case['baseline_response']}")
                report.append("")
                report.append("---")
                report.append("")
    
    # 双方都错误案例
    report.append("### 3.3 双方都错误案例")
    report.append("")
    report.append(f"共 {len(cases['both_wrong'])} 个案例")
    report.append("")
    
    both_wrong_by_type = defaultdict(list)
    for case in cases["both_wrong"]:
        both_wrong_by_type[case["type"]].append(case)
    
    for qtype in QUESTION_TYPES:
        type_cases = both_wrong_by_type.get(qtype, [])
        if type_cases:
            report.append(f"#### {qtype} 类 ({len(type_cases)} 个)")
            report.append("")
            # 展示前2个案例
            for case in type_cases[:2]:
                report.append(f"**问题ID**: `{case['id']}`")
                report.append("")
                report.append(f"**视频ID**: `{case['video_id']}`")
                report.append("")
                report.append(f"**问题**: {case['question']}")
                report.append("")
                report.append(f"**标准答案**: {case['answer']}")
                report.append("")
                report.append(f"**NSTF回答** ✗: {case['nstf_response'][:400]}..." if len(case['nstf_response']) > 400 else f"**NSTF回答** ✗: {case['nstf_response']}")
                report.append("")
                report.append(f"**Baseline回答** ✗: {case['baseline_response'][:400]}..." if len(case['baseline_response']) > 400 else f"**Baseline回答** ✗: {case['baseline_response']}")
                report.append("")
                report.append("---")
                report.append("")
    
    # 总结
    report.append("---")
    report.append("")
    report.append("## 4. 分析总结")
    report.append("")
    
    total = stats["total"]
    nstf_advantage = total["nstf_only_correct"] - total["baseline_only_correct"]
    
    report.append("### 关键发现")
    report.append("")
    report.append(f"1. **总体表现**: NSTF 准确率为 {total['nstf_correct']/total['count']*100:.2f}%, Baseline 为 {total['baseline_correct']/total['count']*100:.2f}%")
    report.append("")
    
    if nstf_advantage > 0:
        report.append(f"2. **差异化表现**: NSTF 在 {total['nstf_only_correct']} 个问题上独占优势, Baseline 在 {total['baseline_only_correct']} 个问题上独占优势, NSTF 净优势 {nstf_advantage} 个问题")
    else:
        report.append(f"2. **差异化表现**: NSTF 在 {total['nstf_only_correct']} 个问题上独占优势, Baseline 在 {total['baseline_only_correct']} 个问题上独占优势, Baseline 净优势 {-nstf_advantage} 个问题")
    report.append("")
    
    # 按类型分析优势
    report.append("3. **分类型优势分析**:")
    report.append("")
    for qtype in QUESTION_TYPES:
        if qtype in stats and stats[qtype]["count"] > 0:
            s = stats[qtype]
            nstf_acc = s["nstf_correct"] / s["count"] * 100
            baseline_acc = s["baseline_correct"] / s["count"] * 100
            diff = nstf_acc - baseline_acc
            if diff > 0:
                report.append(f"   - **{qtype}**: NSTF 领先 {diff:.2f}%")
            elif diff < 0:
                report.append(f"   - **{qtype}**: Baseline 领先 {-diff:.2f}%")
            else:
                report.append(f"   - **{qtype}**: 两者持平")
    report.append("")
    
    report.append("### NSTF 优势分析")
    report.append("")
    report.append("NSTF 模型利用了:")
    report.append("- **NSTF Procedures**: 结构化程序知识 (DAG形式)")
    report.append("- **Episodic Memory**: 情节记忆用于检索相关视频片段")
    report.append("- **Symbolic Reasoning**: 符号推理进行多步推理")
    report.append("")
    
    report.append("### 潜在改进方向")
    report.append("")
    report.append(f"1. 双方都错误的 {total['both_wrong']} 个问题值得深入分析")
    report.append(f"2. Baseline 独占优势的 {total['baseline_only_correct']} 个问题可能揭示 NSTF 的弱点")
    report.append("3. 可进一步分析不同视频类型的表现差异")
    report.append("")
    
    return "\n".join(report)


def main():
    """主函数"""
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 检查文件是否存在
    if not os.path.exists(NSTF_FILE):
        print(f"错误: 找不到 NSTF 文件 {NSTF_FILE}")
        return
    if not os.path.exists(BASELINE_FILE):
        print(f"错误: 找不到 Baseline 文件 {BASELINE_FILE}")
        return
    
    # 执行分析
    stats, cases = analyze_results()
    
    # 打印统计摘要
    print("\n[3] 统计摘要:")
    print("-" * 40)
    total = stats["total"]
    print(f"  总问题数: {total['count']}")
    print(f"  NSTF 正确: {total['nstf_correct']} ({total['nstf_correct']/total['count']*100:.2f}%)")
    print(f"  Baseline 正确: {total['baseline_correct']} ({total['baseline_correct']/total['count']*100:.2f}%)")
    print(f"  双方都正确: {total['both_correct']}")
    print(f"  双方都错误: {total['both_wrong']}")
    print(f"  仅NSTF正确: {total['nstf_only_correct']}")
    print(f"  仅Baseline正确: {total['baseline_only_correct']}")
    
    print("\n[4] 分类型统计:")
    print("-" * 40)
    for qtype in QUESTION_TYPES:
        if qtype in stats and stats[qtype]["count"] > 0:
            s = stats[qtype]
            nstf_acc = s["nstf_correct"] / s["count"] * 100
            baseline_acc = s["baseline_correct"] / s["count"] * 100
            print(f"  {qtype}: 共{s['count']}个, NSTF={nstf_acc:.1f}%, Baseline={baseline_acc:.1f}%")
    
    # 生成报告
    print("\n[5] 生成分析报告...")
    report = generate_report(stats, cases)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"  报告已保存至: {OUTPUT_REPORT}")
    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
