#!/usr/bin/env python
"""
NSTF 图谱完整性分析工具 (增量模式专用)

根据 nstf_builder/README.md 中的 Schema 规范，检测图谱中的异常数据。
分析结果自动保存到 analysis_graph/reports/ 目录下。

使用方法:
    python -m analysis_graph.analyze_nstf kitchen_03 --dataset robot
    python -m analysis_graph.analyze_nstf kitchen_03 --output custom_report.md
    python -m analysis_graph.analyze_nstf --all --dataset robot  # 分析所有视频
"""

import pickle
import argparse
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import os


# ============== 配置 ==============

EXPECTED_SCHEMA_VERSION = "2.3.2"

# 报告输出目录 (相对于 analysis_graph/)
REPORT_DIR = Path(__file__).parent / "reports"

# Procedure Node 必需字段
REQUIRED_PROC_FIELDS = [
    'proc_id', 'type', 'goal', 'description', 'proc_type',
    'embeddings', 'dag', 'steps', 'episodic_links', 'metadata'
]

# 可选字段
OPTIONAL_PROC_FIELDS = ['edges', 'fusion_info']

# proc_type 允许的值（单一值，不允许组合如 'task|social'）
VALID_PROC_TYPES = {'task', 'habit', 'trait', 'social'}

# DAG 必需节点
REQUIRED_DAG_NODES = ['START', 'GOAL']

# embedding 维度
EXPECTED_EMBEDDING_DIM = 3072


# ============== 颜色输出 ==============

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_ok(msg):
    print(f"  {Colors.GREEN}✓{Colors.END} {msg}")


def print_warn(msg):
    print(f"  {Colors.YELLOW}⚠{Colors.END} {msg}")


def print_error(msg):
    print(f"  {Colors.RED}✗{Colors.END} {msg}")


def print_info(msg):
    print(f"  {Colors.BLUE}ℹ{Colors.END} {msg}")


def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{title}{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}")


# ============== 分析类 ==============

class NSTFGraphAnalyzer:
    """NSTF 图谱分析器 (增量模式专用)"""
    
    def __init__(self, video_name: str, dataset: str = 'robot'):
        self.video_name = video_name
        self.dataset = dataset
        
        # 固定使用增量模式
        self.nstf_path = Path(f'data/nstf_graphs/{dataset}/{video_name}_nstf.pkl')
        self.mem_path = Path(f'data/memory_graphs/{dataset}/{video_name}.pkl')
        
        # 分析结果
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}
        
        # 加载的数据
        self.nstf_graph: Optional[Dict] = None
        self.video_graph = None
        
        # 报告内容 (Markdown 格式)
        self.report_lines: List[str] = []
    
    def _add_line(self, line: str):
        """添加一行到报告"""
        self.report_lines.append(line)
    
    def _add_section(self, title: str):
        """添加一个章节标题到报告"""
        self.report_lines.append(f"\n## {title}\n")
    
    def load_graphs(self) -> bool:
        """加载图谱"""
        self._add_section("1. 加载图谱")
        print_section("1. 加载图谱")
        
        # 检查文件是否存在
        if not self.nstf_path.exists():
            msg = f"NSTF 图谱不存在: {self.nstf_path}"
            print_error(msg)
            self._add_line(f"❌ {msg}")
            return False
        print_ok(f"找到 NSTF 图谱: {self.nstf_path}")
        self._add_line(f"✅ 找到 NSTF 图谱: `{self.nstf_path}`")
        
        if not self.mem_path.exists():
            msg = f"Video Graph 不存在: {self.mem_path}"
            print_warn(msg)
            self._add_line(f"⚠️ {msg}")
        else:
            print_ok(f"找到 Video Graph: {self.mem_path}")
            self._add_line(f"✅ 找到 Video Graph: `{self.mem_path}`")
        
        # 加载 NSTF 图谱
        try:
            with open(self.nstf_path, 'rb') as f:
                self.nstf_graph = pickle.load(f)
            print_ok(f"NSTF 图谱加载成功")
            self._add_line(f"✅ NSTF 图谱加载成功")
        except Exception as e:
            msg = f"NSTF 图谱加载失败: {e}"
            print_error(msg)
            self._add_line(f"❌ {msg}")
            self.errors.append(f"加载失败: {e}")
            return False
        
        # 加载 Video Graph (可选)
        if self.mem_path.exists():
            try:
                with open(self.mem_path, 'rb') as f:
                    self.video_graph = pickle.load(f)
                print_ok(f"Video Graph 加载成功")
                self._add_line(f"✅ Video Graph 加载成功")
            except Exception as e:
                print_warn(f"Video Graph 加载失败: {e}")
                self._add_line(f"⚠️ Video Graph 加载失败: {e}")
        
        return True
    
    def analyze_top_level(self) -> None:
        """分析顶层结构"""
        self._add_section("2. 顶层结构分析")
        print_section("2. 顶层结构分析")
        
        expected_keys = {'video_name', 'dataset', 'procedure_nodes', 
                        'character_mapping', 'metadata', 'stats'}
        
        actual_keys = set(self.nstf_graph.keys())
        
        # 检查缺失的键
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        
        if missing:
            msg = f"缺失顶层字段: {missing}"
            print_error(msg)
            self._add_line(f"❌ {msg}")
            self.errors.append(f"缺失顶层字段: {missing}")
        else:
            print_ok("所有预期顶层字段都存在")
            self._add_line("✅ 所有预期顶层字段都存在")
        
        if extra:
            print_info(f"额外字段: {extra}")
            self._add_line(f"ℹ️ 额外字段: {extra}")
        
        # 基本信息
        video_name = self.nstf_graph.get('video_name', 'N/A')
        dataset = self.nstf_graph.get('dataset', 'N/A')
        print(f"\n  视频名称: {video_name}")
        print(f"  数据集: {dataset}")
        self._add_line(f"\n**基本信息:**")
        self._add_line(f"- 视频名称: `{video_name}`")
        self._add_line(f"- 数据集: `{dataset}`")
        
        # 元数据
        metadata = self.nstf_graph.get('metadata', {})
        version = metadata.get('version', 'N/A')
        print(f"  版本: {version}")
        self._add_line(f"- 版本: `{version}`")
        
        if version != EXPECTED_SCHEMA_VERSION:
            msg = f"版本不匹配，预期 {EXPECTED_SCHEMA_VERSION}，实际 {version}"
            print_warn(msg)
            self._add_line(f"⚠️ {msg}")
            self.warnings.append(f"版本不匹配: {version}")
        
        # Procedure 数量
        proc_nodes = self.nstf_graph.get('procedure_nodes', {})
        print(f"  Procedure 数量: {len(proc_nodes)}")
        self._add_line(f"- Procedure 数量: **{len(proc_nodes)}**")
        self.stats['num_procedures'] = len(proc_nodes)
        
        if len(proc_nodes) == 0:
            msg = "Procedure 数量为 0！图谱为空"
            print_error(msg)
            self._add_line(f"❌ {msg}")
            self.errors.append("Procedure 数量为 0")
    
    def analyze_procedures(self) -> None:
        """分析 Procedure 节点"""
        self._add_section("3. Procedure 节点分析")
        print_section("3. Procedure 节点分析")
        
        proc_nodes = self.nstf_graph.get('procedure_nodes', {})
        
        if not proc_nodes:
            print_error("无 Procedure 节点可分析")
            self._add_line("❌ 无 Procedure 节点可分析")
            return
        
        # 字段统计
        field_counter = Counter()
        proc_type_counter = Counter()
        
        # 详细统计
        steps_counts = []
        dag_nodes_counts = []
        dag_edges_counts = []
        episodic_counts = []
        embedding_issues = []
        
        for proc_id, proc in proc_nodes.items():
            # 检查必需字段
            for field in REQUIRED_PROC_FIELDS:
                if field in proc:
                    field_counter[field] += 1
            
            # proc_type
            proc_type = proc.get('proc_type', '')
            proc_type_counter[proc_type] += 1
            if proc_type and proc_type not in VALID_PROC_TYPES:
                self.warnings.append(f"{proc_id}: 无效 proc_type '{proc_type}'")
            
            # steps
            steps = proc.get('steps', [])
            steps_counts.append(len(steps))
            
            # dag
            dag = proc.get('dag', {})
            dag_nodes = dag.get('nodes', {})
            dag_edges = dag.get('edges', [])
            dag_nodes_counts.append(len(dag_nodes))
            dag_edges_counts.append(len(dag_edges))
            
            # episodic_links
            links = proc.get('episodic_links', [])
            episodic_counts.append(len(links))
            
            # embeddings
            embs = proc.get('embeddings', {})
            goal_emb = embs.get('goal_emb')
            step_emb = embs.get('step_emb')
            
            if goal_emb is None:
                embedding_issues.append(f"{proc_id}: goal_emb 缺失")
            elif isinstance(goal_emb, np.ndarray) and goal_emb.shape[0] != EXPECTED_EMBEDDING_DIM:
                embedding_issues.append(f"{proc_id}: goal_emb 维度 {goal_emb.shape} != {EXPECTED_EMBEDDING_DIM}")
            
            if step_emb is None:
                embedding_issues.append(f"{proc_id}: step_emb 缺失")
            elif isinstance(step_emb, np.ndarray) and step_emb.shape[0] != EXPECTED_EMBEDDING_DIM:
                embedding_issues.append(f"{proc_id}: step_emb 维度 {step_emb.shape} != {EXPECTED_EMBEDDING_DIM}")
        
        # 输出字段填充率
        print("\n  字段填充率:")
        self._add_line("\n### 字段填充率\n")
        self._add_line("| 字段 | 状态 | 填充数 | 比例 |")
        self._add_line("|------|------|--------|------|")
        total = len(proc_nodes)
        for field in REQUIRED_PROC_FIELDS:
            count = field_counter[field]
            pct = count / total * 100
            status = "✓" if count == total else "✗"
            color = Colors.GREEN if count == total else Colors.RED
            print(f"    {color}{status}{Colors.END} {field}: {count}/{total} ({pct:.0f}%)")
            status_emoji = "✅" if count == total else "❌"
            self._add_line(f"| {field} | {status_emoji} | {count}/{total} | {pct:.0f}% |")
            
            if count < total:
                self.errors.append(f"字段 '{field}' 只有 {count}/{total} 填充")
        
        # proc_type 分布
        print("\n  proc_type 分布:")
        self._add_line("\n### proc_type 分布\n")
        for pt, cnt in proc_type_counter.most_common():
            print(f"    {pt or '(空)': <10}: {cnt}")
            self._add_line(f"- `{pt or '(空)'}`: {cnt}")
        
        # steps 统计
        print(f"\n  steps 统计:")
        self._add_line("\n### Steps 统计\n")
        print(f"    总数: {sum(steps_counts)}")
        print(f"    范围: {min(steps_counts)} - {max(steps_counts)}")
        print(f"    平均: {sum(steps_counts)/len(steps_counts):.1f}")
        self._add_line(f"- 总数: **{sum(steps_counts)}**")
        self._add_line(f"- 范围: {min(steps_counts)} - {max(steps_counts)}")
        self._add_line(f"- 平均: {sum(steps_counts)/len(steps_counts):.1f}")
        
        if sum(steps_counts) == 0:
            print_error("    所有 Procedure 的 steps 都为空！")
            self._add_line("❌ 所有 Procedure 的 steps 都为空！")
            self.errors.append("所有 steps 都为空")
        elif min(steps_counts) == 0:
            empty_steps = steps_counts.count(0)
            print_warn(f"    {empty_steps}/{total} 个 Procedure 的 steps 为空")
            self._add_line(f"⚠️ {empty_steps}/{total} 个 Procedure 的 steps 为空")
            self.warnings.append(f"{empty_steps} 个 Procedure steps 为空")
        else:
            print_ok("    所有 Procedure 都有 steps")
            self._add_line("✅ 所有 Procedure 都有 steps")
        
        self.stats['steps'] = {
            'total': sum(steps_counts),
            'min': min(steps_counts),
            'max': max(steps_counts),
            'avg': sum(steps_counts)/len(steps_counts),
            'empty_count': steps_counts.count(0)
        }
        
        # DAG 统计
        print(f"\n  DAG 结构统计:")
        self._add_line("\n### DAG 结构统计\n")
        print(f"    nodes 数量: {min(dag_nodes_counts)} - {max(dag_nodes_counts)} (avg: {sum(dag_nodes_counts)/len(dag_nodes_counts):.1f})")
        print(f"    edges 数量: {min(dag_edges_counts)} - {max(dag_edges_counts)} (avg: {sum(dag_edges_counts)/len(dag_edges_counts):.1f})")
        self._add_line(f"- nodes 数量: {min(dag_nodes_counts)} - {max(dag_nodes_counts)} (avg: {sum(dag_nodes_counts)/len(dag_nodes_counts):.1f})")
        self._add_line(f"- edges 数量: {min(dag_edges_counts)} - {max(dag_edges_counts)} (avg: {sum(dag_edges_counts)/len(dag_edges_counts):.1f})")
        
        if sum(dag_nodes_counts) == 0:
            print_error("    所有 DAG nodes 都为空！")
            self._add_line("❌ 所有 DAG nodes 都为空！")
            self.errors.append("所有 DAG nodes 都为空")
        
        if sum(dag_edges_counts) == 0:
            print_error("    所有 DAG edges 都为空！")
            self._add_line("❌ 所有 DAG edges 都为空！")
            self.errors.append("所有 DAG edges 都为空")
        
        self.stats['dag'] = {
            'nodes_total': sum(dag_nodes_counts),
            'edges_total': sum(dag_edges_counts),
            'empty_dag_count': dag_nodes_counts.count(0)
        }
        
        # episodic_links 统计
        print(f"\n  episodic_links 统计:")
        self._add_line("\n### Episodic Links 统计\n")
        print(f"    数量范围: {min(episodic_counts)} - {max(episodic_counts)}")
        print(f"    平均: {sum(episodic_counts)/len(episodic_counts):.1f}")
        self._add_line(f"- 数量范围: {min(episodic_counts)} - {max(episodic_counts)}")
        self._add_line(f"- 平均: {sum(episodic_counts)/len(episodic_counts):.1f}")
        
        if min(episodic_counts) == 0:
            empty_links = episodic_counts.count(0)
            print_warn(f"    {empty_links}/{total} 个 Procedure 无 episodic_links")
            self._add_line(f"⚠️ {empty_links}/{total} 个 Procedure 无 episodic_links")
        
        self.stats['episodic_links'] = {
            'total': sum(episodic_counts),
            'min': min(episodic_counts),
            'max': max(episodic_counts),
            'avg': sum(episodic_counts)/len(episodic_counts)
        }
        
        # Embedding 问题
        if embedding_issues:
            print(f"\n  Embedding 问题 ({len(embedding_issues)} 个):")
            self._add_line(f"\n### Embedding 问题 ({len(embedding_issues)} 个)\n")
            for issue in embedding_issues[:5]:
                print_warn(f"    {issue}")
                self._add_line(f"- ⚠️ {issue}")
            if len(embedding_issues) > 5:
                print_info(f"    ... 还有 {len(embedding_issues)-5} 个问题")
                self._add_line(f"- ... 还有 {len(embedding_issues)-5} 个问题")
            self.errors.extend(embedding_issues)
        else:
            print_ok(f"  所有 embeddings 正常")
            self._add_line("✅ 所有 embeddings 正常")
    
    def analyze_dag_structure(self) -> None:
        """深入分析 DAG 结构"""
        self._add_section("4. DAG 结构详细分析")
        print_section("4. DAG 结构详细分析")
        
        proc_nodes = self.nstf_graph.get('procedure_nodes', {})
        
        dag_issues = []
        valid_dags = 0
        steps_dag_consistent = 0
        
        for proc_id, proc in proc_nodes.items():
            dag = proc.get('dag', {})
            nodes = dag.get('nodes', {})
            edges = dag.get('edges', [])
            steps = proc.get('steps', [])
            
            # 检查 START 和 GOAL 节点
            has_start = 'START' in nodes
            has_goal = 'GOAL' in nodes
            
            if not has_start:
                dag_issues.append(f"{proc_id}: 缺少 START 节点")
            if not has_goal:
                dag_issues.append(f"{proc_id}: 缺少 GOAL 节点")
            
            # V2.3.2: 检查 steps 与 dag.nodes 一致性
            step_ids_from_steps = set()
            for s in steps:
                if isinstance(s, dict):
                    step_ids_from_steps.add(s.get('step_id', ''))
            step_ids_from_dag = set(k for k in nodes.keys() if k not in ['START', 'GOAL'])
            
            if step_ids_from_steps == step_ids_from_dag:
                steps_dag_consistent += 1
            else:
                # 只在差异较大时报告（允许轻微差异）
                missing_in_dag = step_ids_from_steps - step_ids_from_dag
                extra_in_dag = step_ids_from_dag - step_ids_from_steps
                if missing_in_dag or extra_in_dag:
                    dag_issues.append(f"{proc_id}: steps 与 dag.nodes 不一致 (steps: {len(step_ids_from_steps)}, dag: {len(step_ids_from_dag)})")
            
            # 检查边的连通性
            if edges:
                from_nodes = set(e.get('from') for e in edges)
                to_nodes = set(e.get('to') for e in edges)
                
                # START 应该有出边
                if has_start and 'START' not in from_nodes:
                    dag_issues.append(f"{proc_id}: START 节点无出边")
                
                # GOAL 应该有入边
                if has_goal and 'GOAL' not in to_nodes:
                    dag_issues.append(f"{proc_id}: GOAL 节点无入边")
                
                # 检查边的概率
                for edge in edges:
                    prob = edge.get('probability', 0)
                    if prob <= 0 or prob > 1:
                        dag_issues.append(f"{proc_id}: 边概率异常 {prob}")
                        break
            
            if has_start and has_goal and len(nodes) >= 2 and len(edges) >= 1:
                valid_dags += 1
        
        # 输出结果
        total = len(proc_nodes)
        print(f"  有效 DAG 数量: {valid_dags}/{total}")
        self._add_line(f"- 有效 DAG 数量: **{valid_dags}/{total}**")
        
        print(f"  Steps/DAG 一致: {steps_dag_consistent}/{total}")
        self._add_line(f"- Steps/DAG 一致: **{steps_dag_consistent}/{total}**")
        
        if valid_dags == total:
            print_ok("所有 Procedure 都有有效的 DAG 结构")
            self._add_line("✅ 所有 Procedure 都有有效的 DAG 结构")
        elif valid_dags == 0:
            print_error("没有任何有效的 DAG 结构！")
            self._add_line("❌ 没有任何有效的 DAG 结构！")
            self.errors.append("无有效 DAG 结构")
        else:
            print_warn(f"{total - valid_dags} 个 DAG 结构不完整")
            self._add_line(f"⚠️ {total - valid_dags} 个 DAG 结构不完整")
        
        if dag_issues:
            print(f"\n  DAG 问题 ({len(dag_issues)} 个):")
            self._add_line(f"\n### DAG 问题 ({len(dag_issues)} 个)\n")
            for issue in dag_issues[:10]:
                print_warn(f"    {issue}")
                self._add_line(f"- ⚠️ {issue}")
            if len(dag_issues) > 10:
                print_info(f"    ... 还有 {len(dag_issues)-10} 个问题")
                self._add_line(f"- ... 还有 {len(dag_issues)-10} 个问题")
        
        self.stats['valid_dags'] = valid_dags
        self.stats['steps_dag_consistent'] = steps_dag_consistent
    
    def analyze_edge_statistics(self) -> None:
        """分析 DAG 边的转移统计和分支结构（V2.4 新增）"""
        self._add_section("4.5 边转移统计分析")
        print_section("4.5 边转移统计分析")
        
        proc_nodes = self.nstf_graph.get('procedure_nodes', {})
        
        if not proc_nodes:
            print_warn("无 Procedure 节点")
            self._add_line("⚠️ 无 Procedure 节点")
            return
        
        all_counts = []
        all_probs = []
        procs_with_uniform_count = 0
        procs_with_uniform_prob = 0
        procs_with_branching = 0  # 有分支结构的 DAG
        procs_linear = 0  # 线性结构的 DAG
        
        branching_examples = []
        
        for proc_id, proc in proc_nodes.items():
            edges = proc.get('dag', {}).get('edges', [])
            if not edges:
                continue
            
            counts = [e.get('count', 1) for e in edges]
            probs = [e.get('probability', 1.0) for e in edges]
            
            all_counts.extend(counts)
            all_probs.extend(probs)
            
            if all(c == 1 for c in counts):
                procs_with_uniform_count += 1
            if all(abs(p - 1.0) < 0.001 for p in probs):
                procs_with_uniform_prob += 1
            
            # 检查是否有分支结构（同一源节点有多个目标）
            from collections import Counter
            sources = [e.get('from') or e.get('from_step', '') for e in edges]
            source_counts = Counter(sources)
            has_branching = any(cnt > 1 for cnt in source_counts.values())
            
            if has_branching:
                procs_with_branching += 1
                if len(branching_examples) < 3:
                    branch_info = [(src, cnt) for src, cnt in source_counts.items() if cnt > 1]
                    branching_examples.append((proc_id, branch_info))
            else:
                procs_linear += 1
        
        total = len(proc_nodes)
        
        # 输出边计数统计
        print(f"\n  === 边计数统计 ===")
        self._add_line(f"\n### 边计数统计\n")
        
        if all_counts:
            print(f"  count 范围: {min(all_counts)} - {max(all_counts)}")
            print(f"  count 均值: {sum(all_counts)/len(all_counts):.2f}")
            print(f"  所有 count=1 的 Procedure: {procs_with_uniform_count}/{total}")
            self._add_line(f"- count 范围: {min(all_counts)} - {max(all_counts)}")
            self._add_line(f"- count 均值: {sum(all_counts)/len(all_counts):.2f}")
            self._add_line(f"- 所有 count=1 的 Procedure: {procs_with_uniform_count}/{total}")
            
            if procs_with_uniform_count == total:
                print_warn(f"  ⚠️ 所有 Procedure 的 count 都未更新（转移计数未累积）！")
                self._add_line(f"⚠️ 所有 Procedure 的 count 都未更新！")
                self.warnings.append("所有边的转移计数未被更新")
            elif procs_with_uniform_count > total * 0.8:
                print_warn(f"  ⚠️ 大部分 Procedure 的 count 未更新")
                self._add_line(f"⚠️ 大部分 Procedure 的 count 未更新")
        
        # 输出概率分布统计
        print(f"\n  === 概率分布统计 ===")
        self._add_line(f"\n### 概率分布统计\n")
        
        if all_probs:
            print(f"  所有 prob=1.0 的 Procedure: {procs_with_uniform_prob}/{total}")
            self._add_line(f"- 所有 prob=1.0 的 Procedure: {procs_with_uniform_prob}/{total}")
            
            if procs_with_uniform_prob == total:
                print_warn(f"  ⚠️ 所有 Procedure 的概率分布无差异！")
                self._add_line(f"⚠️ 所有 Procedure 的概率分布无差异！")
        
        # 输出分支结构统计
        print(f"\n  === DAG 分支结构统计 ===")
        self._add_line(f"\n### DAG 分支结构统计\n")
        
        print(f"  线性 DAG: {procs_linear}/{total}")
        print(f"  有分支的 DAG: {procs_with_branching}/{total}")
        self._add_line(f"- 线性 DAG: {procs_linear}/{total}")
        self._add_line(f"- 有分支的 DAG: **{procs_with_branching}/{total}**")
        
        if procs_with_branching == 0:
            print_warn(f"  ⚠️ 没有任何 DAG 有分支结构（所有 DAG 都是线性的）")
            self._add_line(f"⚠️ 没有任何 DAG 有分支结构！")
            self.warnings.append("所有 DAG 都是线性结构，无分支")
        elif procs_with_branching > 0:
            print_ok(f"  有 {procs_with_branching} 个 DAG 包含分支结构")
            self._add_line(f"✅ 有 {procs_with_branching} 个 DAG 包含分支结构")
            
            # 展示分支示例
            if branching_examples:
                print(f"\n  分支结构示例:")
                self._add_line(f"\n**分支结构示例:**")
                for proc_id, branches in branching_examples:
                    branch_str = ", ".join([f"{src}→{cnt}条边" for src, cnt in branches])
                    print(f"    - {proc_id}: {branch_str}")
                    self._add_line(f"- `{proc_id}`: {branch_str}")
        
        self.stats['edge_statistics'] = {
            'total_edges': len(all_counts),
            'count_range': (min(all_counts), max(all_counts)) if all_counts else (0, 0),
            'uniform_count_procs': procs_with_uniform_count,
            'uniform_prob_procs': procs_with_uniform_prob,
            'linear_dags': procs_linear,
            'branching_dags': procs_with_branching,
        }
    
    def analyze_episodic_coverage(self) -> None:
        """分析 episodic 覆盖率"""
        self._add_section("5. Episodic 覆盖率分析")
        print_section("5. Episodic 覆盖率分析")
        
        if self.video_graph is None:
            print_warn("Video Graph 未加载，跳过覆盖率分析")
            self._add_line("⚠️ Video Graph 未加载，跳过覆盖率分析")
            return
        
        proc_nodes = self.nstf_graph.get('procedure_nodes', {})
        
        # 收集所有引用的 clip IDs
        referenced_clips = set()
        for proc in proc_nodes.values():
            for link in proc.get('episodic_links', []):
                clip_id = link.get('clip_id')
                if clip_id is not None:
                    referenced_clips.add(int(clip_id))
        
        # 获取 video_graph 中的总 clip 数
        if hasattr(self.video_graph, 'text_nodes_by_clip'):
            total_clips = len(self.video_graph.text_nodes_by_clip)
            all_clips = set(self.video_graph.text_nodes_by_clip.keys())
        else:
            print_warn("Video Graph 无 text_nodes_by_clip 属性")
            self._add_line("⚠️ Video Graph 无 text_nodes_by_clip 属性")
            return
        
        # 计算覆盖率
        coverage = len(referenced_clips) / total_clips * 100 if total_clips > 0 else 0
        uncovered = all_clips - referenced_clips
        
        print(f"  Video Graph 总 clips: {total_clips}")
        print(f"  NSTF 引用的 clips: {len(referenced_clips)}")
        print(f"  覆盖率: {coverage:.1f}%")
        self._add_line(f"- Video Graph 总 clips: **{total_clips}**")
        self._add_line(f"- NSTF 引用的 clips: **{len(referenced_clips)}**")
        self._add_line(f"- 覆盖率: **{coverage:.1f}%**")
        
        if coverage < 30:
            print_error(f"  覆盖率过低 (<30%)！大量视频内容未被程序覆盖")
            self._add_line(f"❌ 覆盖率过低 (<30%)！大量视频内容未被程序覆盖")
            self.errors.append(f"Episodic 覆盖率过低: {coverage:.1f}%")
        elif coverage < 50:
            print_warn(f"  覆盖率较低 (<50%)")
            self._add_line(f"⚠️ 覆盖率较低 (<50%)")
            self.warnings.append(f"Episodic 覆盖率较低: {coverage:.1f}%")
        else:
            print_ok(f"  覆盖率 >= 50%")
            self._add_line(f"✅ 覆盖率 >= 50%")
        
        # 显示未覆盖的 clips
        if uncovered and len(uncovered) <= 20:
            print(f"  未覆盖的 clips: {sorted(uncovered)}")
            self._add_line(f"- 未覆盖的 clips: `{sorted(uncovered)}`")
        elif uncovered:
            print(f"  未覆盖的 clips: {sorted(list(uncovered)[:10])}... (共 {len(uncovered)} 个)")
            self._add_line(f"- 未覆盖的 clips: `{sorted(list(uncovered)[:10])}...` (共 {len(uncovered)} 个)")
        
        self.stats['episodic_coverage'] = {
            'total_clips': total_clips,
            'referenced_clips': len(referenced_clips),
            'coverage_pct': coverage
        }
    
    def analyze_goal_quality(self) -> None:
        """分析 Goal 质量（是否太抽象、是否有异常）"""
        self._add_section("6. Goal 质量分析")
        print_section("6. Goal 质量分析")
        
        proc_nodes = self.nstf_graph.get('procedure_nodes', {})
        
        # 关键词检测 - 太抽象的 goal
        vague_keywords = ['something', 'things', 'stuff', 'item', 'object', 'task']
        # 具体的 goal 应该包含
        specific_indicators = ['bottle', 'melon', 'groceries', 'cabinet', 'refrigerator', 
                               'trash', 'bin', 'knife', 'pot', 'pan', 'plate', 'bag', 
                               'counter', 'table', 'sink', 'broom', 'floor', 'chicken',
                               'egg', 'vegetable', 'fruit', 'meat', 'pen', 'notebook']
        # V2.3.2: 检测潜在的 LLM 幻觉/异常描述
        suspicious_patterns = ['jesus', 'god', 'devil', 'angel', 'heaven', 'hell',
                               'lorem ipsum', 'test123', 'example', 'placeholder']
        
        vague_goals = []
        specific_goals = []
        suspicious_goals = []
        all_goals = []
        
        for proc_id, proc in proc_nodes.items():
            goal = proc.get('goal', '')
            all_goals.append((proc_id, goal))
            
            goal_lower = goal.lower()
            
            # 检查是否太抽象
            if any(kw in goal_lower for kw in vague_keywords):
                vague_goals.append((proc_id, goal))
            
            # 检查是否具体
            if any(kw in goal_lower for kw in specific_indicators):
                specific_goals.append((proc_id, goal))
            
            # V2.3.2: 检查是否有可疑的 LLM 幻觉
            if any(kw in goal_lower for kw in suspicious_patterns):
                suspicious_goals.append((proc_id, goal))
        
        print(f"  总 Procedure 数: {len(all_goals)}")
        print(f"  模糊 Goal 数: {len(vague_goals)}")
        print(f"  具体 Goal 数: {len(specific_goals)}")
        self._add_line(f"- 总 Procedure 数: **{len(all_goals)}**")
        self._add_line(f"- 模糊 Goal 数: {len(vague_goals)}")
        self._add_line(f"- 具体 Goal 数: {len(specific_goals)}")
        
        # V2.3.2: 报告可疑的 Goal（可能是 LLM 幻觉）
        if suspicious_goals:
            print(f"\n  ⚠️ 可疑 Goals (可能是 LLM 幻觉/误识别):")
            self._add_line(f"\n### 可疑 Goals (可能是 LLM 幻觉)\n")
            for pid, goal in suspicious_goals:
                print_warn(f"    {pid}: {goal}")
                self._add_line(f"- ⚠️ `{pid}`: {goal}")
            self.warnings.append(f"{len(suspicious_goals)} 个 Goal 可能包含 LLM 幻觉")
        
        if vague_goals:
            print(f"\n  模糊 Goals (包含 'something/things' 等):")
            self._add_line(f"\n### 模糊 Goals (包含 'something/things' 等)\n")
            for pid, goal in vague_goals[:5]:
                print_warn(f"    {pid}: {goal}")
                self._add_line(f"- ⚠️ `{pid}`: {goal}")
        
        if len(specific_goals) == 0:
            print_error("  没有包含具体物品/位置的 Goal！")
            self._add_line("❌ 没有包含具体物品/位置的 Goal！")
            self.errors.append("Goal 缺乏具体物品/位置信息")
        elif len(specific_goals) < len(all_goals) * 0.3:
            print_warn(f"  只有 {len(specific_goals)}/{len(all_goals)} 个 Goal 包含具体信息")
            self._add_line(f"⚠️ 只有 {len(specific_goals)}/{len(all_goals)} 个 Goal 包含具体信息")
            self.warnings.append("大部分 Goal 太抽象")
        
        # 列出所有 goals
        print(f"\n  所有 Goals:")
        self._add_line(f"\n### 所有 Goals\n")
        for pid, goal in all_goals:
            print(f"    - {goal}")
            self._add_line(f"- {goal}")
        
        self.stats['goal_quality'] = {
            'total': len(all_goals),
            'vague': len(vague_goals),
            'specific': len(specific_goals)
        }
    
    def analyze_character_mapping(self) -> None:
        """分析 Character Mapping"""
        self._add_section("7. Character Mapping 分析")
        print_section("7. Character Mapping 分析")
        
        mapping = self.nstf_graph.get('character_mapping', {})
        
        print(f"  映射条目数: {len(mapping)}")
        self._add_line(f"- 映射条目数: **{len(mapping)}**")
        
        if not mapping:
            print_warn("  Character Mapping 为空")
            self._add_line("⚠️ Character Mapping 为空")
            self.warnings.append("Character Mapping 为空")
            return
        
        # 统计映射类型
        face_count = sum(1 for k in mapping.keys() if 'face' in k.lower())
        voice_count = sum(1 for k in mapping.keys() if 'voice' in k.lower())
        
        print(f"  face_* 映射: {face_count}")
        print(f"  voice_* 映射: {voice_count}")
        self._add_line(f"- face_* 映射: {face_count}")
        self._add_line(f"- voice_* 映射: {voice_count}")
        
        # 检查目标 person ID
        target_ids = set(mapping.values())
        print(f"  映射到的 person 数: {len(target_ids)}")
        print(f"  Person IDs: {sorted(target_ids)[:10]}...")
        self._add_line(f"- 映射到的 person 数: {len(target_ids)}")
        self._add_line(f"- Person IDs: `{sorted(target_ids)[:10]}...`")
        
        self.stats['character_mapping'] = {
            'total': len(mapping),
            'face_count': face_count,
            'voice_count': voice_count,
            'unique_persons': len(target_ids)
        }
    
    def show_procedure_details(self, num_samples: int = 3) -> None:
        """展示 Procedure 节点的完整详细信息"""
        self._add_section(f"8. Procedure 完整详情 (前 {num_samples} 个)")
        print_section(f"8. Procedure 完整详情 (前 {num_samples} 个)")
        
        proc_nodes = self.nstf_graph.get('procedure_nodes', {})
        
        if not proc_nodes:
            print_error("无 Procedure 节点")
            self._add_line("❌ 无 Procedure 节点")
            return
        
        for i, (proc_id, proc) in enumerate(list(proc_nodes.items())[:num_samples]):
            print(f"\n{Colors.BOLD}{'─'*60}{Colors.END}")
            print(f"{Colors.BOLD}{Colors.CYAN}Procedure {i+1}: {proc_id}{Colors.END}")
            print(f"{'─'*60}")
            self._add_line(f"\n### Procedure {i+1}: `{proc_id}`\n")
            
            # 基本信息
            print(f"\n  {Colors.BOLD}【基本信息】{Colors.END}")
            print(f"    type: {proc.get('type', 'N/A')}")
            print(f"    proc_type: {proc.get('proc_type', 'N/A')}")
            print(f"    goal: {proc.get('goal', 'N/A')}")
            self._add_line(f"**基本信息:**")
            self._add_line(f"- type: `{proc.get('type', 'N/A')}`")
            self._add_line(f"- proc_type: `{proc.get('proc_type', 'N/A')}`")
            self._add_line(f"- goal: {proc.get('goal', 'N/A')}")
            
            description = proc.get('description', 'N/A')
            if len(description) > 100:
                print(f"    description: {description[:100]}...")
                self._add_line(f"- description: {description[:100]}...")
            else:
                print(f"    description: {description}")
                self._add_line(f"- description: {description}")
            
            # Steps 详情
            print(f"\n  {Colors.BOLD}【Steps 详情】{Colors.END}")
            self._add_line(f"\n**Steps 详情:**")
            steps = proc.get('steps', [])
            if not steps:
                print_warn(f"    (空 - 无步骤)")
                self._add_line(f"- ⚠️ (空 - 无步骤)")
            else:
                print(f"    数量: {len(steps)}")
                self._add_line(f"- 数量: {len(steps)}")
                for j, step in enumerate(steps[:5]):
                    if isinstance(step, dict):
                        action = step.get('action', 'N/A')
                        obj = step.get('object', '')
                        loc = step.get('location', '')
                        step_str = f"action='{action}'"
                        if obj:
                            step_str += f", object='{obj}'"
                        if loc:
                            step_str += f", location='{loc}'"
                        print(f"    Step {j+1}: {{{step_str}}}")
                        self._add_line(f"- Step {j+1}: `{{{step_str}}}`")
                    else:
                        print(f"    Step {j+1}: {step}")
                        self._add_line(f"- Step {j+1}: {step}")
                if len(steps) > 5:
                    print(f"    ... 还有 {len(steps)-5} 个步骤")
                    self._add_line(f"- ... 还有 {len(steps)-5} 个步骤")
            
            # DAG 详情
            print(f"\n  {Colors.BOLD}【DAG 结构详情】{Colors.END}")
            self._add_line(f"\n**DAG 结构详情:**")
            dag = proc.get('dag', {})
            dag_nodes = dag.get('nodes', {})
            dag_edges = dag.get('edges', [])
            
            print(f"    节点数: {len(dag_nodes)}, 边数: {len(dag_edges)}")
            self._add_line(f"- 节点数: {len(dag_nodes)}, 边数: {len(dag_edges)}")
            
            if dag_nodes:
                print(f"\n    {Colors.BLUE}Nodes:{Colors.END}")
                self._add_line(f"\nNodes:")
                for node_id, node_data in list(dag_nodes.items())[:8]:
                    if isinstance(node_data, dict):
                        node_type = node_data.get('type', 'N/A')
                        label = node_data.get('label', 'N/A')
                        if len(label) > 50:
                            label = label[:50] + '...'
                        print(f"      [{node_id}]")
                        print(f"        type: {node_type}")
                        print(f"        label: {label}")
                        self._add_line(f"- `[{node_id}]`: type=`{node_type}`, label=\"{label}\"")
                        # 显示其他属性
                        for k, v in node_data.items():
                            if k not in ['type', 'label']:
                                v_str = str(v)
                                if len(v_str) > 50:
                                    v_str = v_str[:50] + '...'
                                print(f"        {k}: {v_str}")
                    else:
                        print(f"      [{node_id}]: {node_data}")
                        self._add_line(f"- `[{node_id}]`: {node_data}")
                if len(dag_nodes) > 8:
                    print(f"      ... 还有 {len(dag_nodes)-8} 个节点")
                    self._add_line(f"- ... 还有 {len(dag_nodes)-8} 个节点")
            else:
                print_warn(f"    (无节点)")
                self._add_line(f"- ⚠️ (无节点)")
            
            if dag_edges:
                print(f"\n    {Colors.BLUE}Edges:{Colors.END}")
                self._add_line(f"\nEdges:")
                for j, edge in enumerate(dag_edges[:6]):
                    if isinstance(edge, dict):
                        from_node = edge.get('from', 'N/A')
                        to_node = edge.get('to', 'N/A')
                        prob = edge.get('probability', 'N/A')
                        label = edge.get('label', '')
                        edge_str = f"{from_node} → {to_node} (prob={prob})"
                        if label:
                            edge_str += f", label='{label}'"
                        print(f"      Edge {j+1}: {edge_str}")
                        self._add_line(f"- Edge {j+1}: `{edge_str}`")
                    else:
                        print(f"      Edge {j+1}: {edge}")
                        self._add_line(f"- Edge {j+1}: {edge}")
                if len(dag_edges) > 6:
                    print(f"      ... 还有 {len(dag_edges)-6} 条边")
                    self._add_line(f"- ... 还有 {len(dag_edges)-6} 条边")
            else:
                print_warn(f"    (无边)")
                self._add_line(f"- ⚠️ (无边)")
            
            # Episodic Links 详情
            print(f"\n  {Colors.BOLD}【Episodic Links 详情】{Colors.END}")
            self._add_line(f"\n**Episodic Links 详情:**")
            links = proc.get('episodic_links', [])
            if not links:
                print_warn(f"    (空 - 无链接)")
                self._add_line(f"- ⚠️ (空 - 无链接)")
            else:
                print(f"    数量: {len(links)}")
                self._add_line(f"- 数量: {len(links)}")
                for j, link in enumerate(links[:4]):
                    clip_id = link.get('clip_id', 'N/A')
                    relevance = link.get('relevance', 'N/A')
                    similarity = link.get('similarity', 'N/A')
                    preview = link.get('content_preview', '')[:60]
                    print(f"    Link {j+1}:")
                    print(f"      clip_id: {clip_id}")
                    print(f"      relevance: {relevance}")
                    print(f"      similarity: {similarity}")
                    print(f"      preview: \"{preview}...\"")
                    self._add_line(f"- Link {j+1}: clip_id=`{clip_id}`, relevance=`{relevance}`, similarity=`{similarity}`")
                if len(links) > 4:
                    print(f"    ... 还有 {len(links)-4} 个链接")
                    self._add_line(f"- ... 还有 {len(links)-4} 个链接")
            
            # Embeddings 信息
            print(f"\n  {Colors.BOLD}【Embeddings 信息】{Colors.END}")
            self._add_line(f"\n**Embeddings 信息:**")
            embs = proc.get('embeddings', {})
            if not embs:
                print_warn(f"    (空)")
                self._add_line(f"- ⚠️ (空)")
            else:
                for emb_name, emb_data in embs.items():
                    if isinstance(emb_data, np.ndarray):
                        print(f"    {emb_name}: shape={emb_data.shape}, dtype={emb_data.dtype}")
                        self._add_line(f"- `{emb_name}`: shape=`{emb_data.shape}`, dtype=`{emb_data.dtype}`")
                        # 显示前几个值
                        vals = emb_data.flatten()[:5]
                        print(f"      前5值: [{', '.join(f'{v:.4f}' for v in vals)}...]")
                    elif isinstance(emb_data, str):
                        # 可能是字符串表示的数组
                        print(f"    {emb_name}: (string repr, len={len(emb_data)})")
                        self._add_line(f"- `{emb_name}`: (string repr, len={len(emb_data)})")
                    else:
                        print(f"    {emb_name}: type={type(emb_data).__name__}")
                        self._add_line(f"- `{emb_name}`: type=`{type(emb_data).__name__}`")
            
            # Metadata 信息
            print(f"\n  {Colors.BOLD}【Metadata 信息】{Colors.END}")
            self._add_line(f"\n**Metadata 信息:**")
            metadata = proc.get('metadata', {})
            if not metadata:
                print_warn(f"    (空)")
                self._add_line(f"- (空)")
            else:
                for k, v in metadata.items():
                    v_str = str(v)
                    if len(v_str) > 60:
                        v_str = v_str[:60] + '...'
                    print(f"    {k}: {v_str}")
                    self._add_line(f"- `{k}`: {v_str}")
            
            # Fusion Info (如果有)
            fusion = proc.get('fusion_info', {})
            if fusion:
                print(f"\n  {Colors.BOLD}【Fusion Info】{Colors.END}")
                self._add_line(f"\n**Fusion Info:**")
                for k, v in fusion.items():
                    v_str = str(v)
                    if len(v_str) > 60:
                        v_str = v_str[:60] + '...'
                    print(f"    {k}: {v_str}")
                    self._add_line(f"- `{k}`: {v_str}")
    
    def print_summary(self) -> None:
        """打印总结"""
        self._add_section("9. 诊断总结")
        print_section("9. 诊断总结")
        
        print(f"\n  {Colors.RED}错误 ({len(self.errors)} 个):{Colors.END}")
        self._add_line(f"\n### 错误 ({len(self.errors)} 个)\n")
        if self.errors:
            for err in self.errors[:10]:
                print(f"    ✗ {err}")
                self._add_line(f"- ❌ {err}")
            if len(self.errors) > 10:
                print(f"    ... 还有 {len(self.errors)-10} 个错误")
                self._add_line(f"- ... 还有 {len(self.errors)-10} 个错误")
        else:
            print("    无错误")
            self._add_line("✅ 无错误")
        
        print(f"\n  {Colors.YELLOW}警告 ({len(self.warnings)} 个):{Colors.END}")
        self._add_line(f"\n### 警告 ({len(self.warnings)} 个)\n")
        if self.warnings:
            for warn in self.warnings[:10]:
                print(f"    ⚠ {warn}")
                self._add_line(f"- ⚠️ {warn}")
            if len(self.warnings) > 10:
                print(f"    ... 还有 {len(self.warnings)-10} 个警告")
                self._add_line(f"- ... 还有 {len(self.warnings)-10} 个警告")
        else:
            print("    无警告")
            self._add_line("✅ 无警告")
        
        # 总体评估
        print(f"\n  {Colors.BOLD}总体评估:{Colors.END}")
        self._add_line(f"\n### 总体评估\n")
        if len(self.errors) == 0 and len(self.warnings) == 0:
            print(f"    {Colors.GREEN}✓ 图谱结构完整，无明显问题{Colors.END}")
            self._add_line("✅ **图谱结构完整，无明显问题**")
        elif len(self.errors) == 0:
            print(f"    {Colors.YELLOW}⚠ 图谱基本完整，但有 {len(self.warnings)} 个警告需要关注{Colors.END}")
            self._add_line(f"⚠️ **图谱基本完整，但有 {len(self.warnings)} 个警告需要关注**")
        elif len(self.errors) <= 3:
            print(f"    {Colors.YELLOW}⚠ 图谱存在 {len(self.errors)} 个问题，建议修复{Colors.END}")
            self._add_line(f"⚠️ **图谱存在 {len(self.errors)} 个问题，建议修复**")
        else:
            print(f"    {Colors.RED}✗ 图谱存在严重问题 ({len(self.errors)} 个错误)，需要重新构建{Colors.END}")
            self._add_line(f"❌ **图谱存在严重问题 ({len(self.errors)} 个错误)，需要重新构建**")
    
    def export_markdown_report(self, output_path: Path) -> None:
        """导出 Markdown 分析报告"""
        # 构建报告头部
        header = [
            f"# NSTF 图谱分析报告",
            f"",
            f"**视频:** `{self.video_name}`  ",
            f"**数据集:** `{self.dataset}`  ",
            f"**模式:** 增量模式 (incremental)  ",
            f"**分析时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**NSTF 路径:** `{self.nstf_path}`",
            f"",
            f"---",
            f""
        ]
        
        full_report = "\n".join(header + self.report_lines)
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        print(f"\n{Colors.GREEN}Markdown 报告已导出到: {output_path}{Colors.END}")
    
    def export_json_report(self, output_path: Path) -> None:
        """导出 JSON 分析报告"""
        report = {
            'video_name': self.video_name,
            'dataset': self.dataset,
            'mode': 'incremental',
            'analyzed_at': datetime.now().isoformat(),
            'nstf_path': str(self.nstf_path),
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': self.stats
        }
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"{Colors.GREEN}JSON 报告已导出到: {output_path}{Colors.END}")
    
    def run(self, num_detail_samples: int = 3, output_dir: Optional[Path] = None) -> bool:
        """运行完整分析
        
        Args:
            num_detail_samples: 展示的 Procedure 详情数量
            output_dir: 报告输出目录，默认为 analysis_graph/reports/
        
        Returns:
            bool: 是否无错误
        """
        print(f"\n{Colors.BOLD}NSTF 图谱分析工具 v2.4 (增量模式专用){Colors.END}")
        print(f"视频: {self.video_name} | 数据集: {self.dataset}")
        
        if not self.load_graphs():
            return False
        
        self.analyze_top_level()
        self.analyze_procedures()
        self.analyze_dag_structure()
        self.analyze_edge_statistics()  # V2.4 新增: 边转移统计和分支结构分析
        self.analyze_episodic_coverage()
        self.analyze_goal_quality()
        self.analyze_character_mapping()
        self.show_procedure_details(num_samples=num_detail_samples)
        self.print_summary()
        
        # 自动导出报告
        if output_dir is None:
            output_dir = REPORT_DIR
        
        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = f"{self.video_name}_{self.dataset}"
        
        md_path = output_dir / f"{base_name}_report.md"
        json_path = output_dir / f"{base_name}_report.json"
        
        self.export_markdown_report(md_path)
        self.export_json_report(json_path)
        
        return len(self.errors) == 0


def analyze_all_videos(dataset: str, output_dir: Optional[Path] = None) -> Dict[str, bool]:
    """分析指定数据集下的所有视频
    
    Args:
        dataset: 数据集名称 ('robot' 或 'web')
        output_dir: 报告输出目录
    
    Returns:
        Dict[str, bool]: 各视频的分析结果
    """
    nstf_dir = Path(f'data/nstf_graphs/{dataset}')
    
    if not nstf_dir.exists():
        print(f"{Colors.RED}错误: 目录不存在 {nstf_dir}{Colors.END}")
        return {}
    
    # 查找所有增量模式的 NSTF 图谱
    nstf_files = list(nstf_dir.glob('*_nstf.pkl'))
    
    if not nstf_files:
        print(f"{Colors.YELLOW}警告: 未找到增量模式的 NSTF 图谱{Colors.END}")
        return {}
    
    print(f"\n{Colors.BOLD}批量分析 {len(nstf_files)} 个 {dataset} 数据集的视频{Colors.END}\n")
    
    results = {}
    for nstf_file in sorted(nstf_files):
        # 提取视频名称
        video_name = nstf_file.stem.replace('_nstf', '')
        print(f"\n{'='*60}")
        print(f"分析: {video_name}")
        print(f"{'='*60}")
        
        analyzer = NSTFGraphAnalyzer(video_name=video_name, dataset=dataset)
        success = analyzer.run(output_dir=output_dir)
        results[video_name] = success
    
    # 打印汇总
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}批量分析完成{Colors.END}")
    print(f"{'='*60}")
    
    success_count = sum(1 for v in results.values() if v)
    print(f"成功: {success_count}/{len(results)}")
    
    if output_dir is None:
        output_dir = REPORT_DIR
    
    # 生成汇总报告
    summary_path = output_dir / f"{dataset}_summary.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"# NSTF 批量分析汇总 - {dataset}\n\n")
        f.write(f"**分析时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**总数:** {len(results)}\n")
        f.write(f"**成功:** {success_count}\n")
        f.write(f"**失败:** {len(results) - success_count}\n\n")
        
        f.write("## 详细结果\n\n")
        f.write("| 视频 | 状态 |\n")
        f.write("|------|------|\n")
        for video, success in sorted(results.items()):
            status = "✅ 成功" if success else "❌ 有问题"
            f.write(f"| {video} | {status} |\n")
    
    print(f"\n汇总报告已保存到: {summary_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='NSTF 图谱完整性分析工具 (增量模式专用)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m analysis_graph.analyze_nstf kitchen_03 --dataset robot
  python -m analysis_graph.analyze_nstf kitchen_03 --output custom_dir/
  python -m analysis_graph.analyze_nstf kitchen_03 --show-details 5
  python -m analysis_graph.analyze_nstf --all --dataset robot  # 分析所有视频
        """
    )
    
    parser.add_argument('video_name', nargs='?', help='视频名称 (使用 --all 时可省略)')
    parser.add_argument('--dataset', '-d', default='robot', 
                       choices=['robot', 'web'], help='数据集 (default: robot)')
    parser.add_argument('--all', '-a', action='store_true',
                       help='分析指定数据集下的所有视频')
    parser.add_argument('--output', '-o', help='输出报告目录 (默认: analysis_graph/reports/)')
    parser.add_argument('--show-details', '-s', type=int, default=3,
                       help='完整展示的 Procedure 数量 (default: 3)')
    
    args = parser.parse_args()
    
    # 确定输出目录
    output_dir = Path(args.output) if args.output else REPORT_DIR
    
    if args.all:
        # 批量分析
        results = analyze_all_videos(args.dataset, output_dir)
        success = all(results.values()) if results else False
    else:
        if not args.video_name:
            parser.error("请指定视频名称，或使用 --all 分析所有视频")
        
        analyzer = NSTFGraphAnalyzer(
            video_name=args.video_name,
            dataset=args.dataset
        )
        
        success = analyzer.run(num_detail_samples=args.show_details, output_dir=output_dir)
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
