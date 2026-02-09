# -*- coding: utf-8 -*-
"""
Symbolic Functions - 论文 4.3.2 Logic Layer 核心实现

三种 Symbolic 查询函数：
1. get_procedure_with_evidence(): 核心检索 + episodic 证据追溯
2. query_step_sequence(): 时序/步骤查询 (DAG 多路径支持)
3. aggregate_character_behaviors(): 人物行为模式聚合

DAG 多路径支持:
- Procedure 的 steps 可能存在分支 (alternative paths)
- 支持路径枚举和条件查询
"""

import re
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ProcedureResult:
    """Procedure 查询结果"""
    proc_id: str
    goal: str
    steps: List[str]
    episodic_evidence: Dict[int, str]  # clip_id -> content
    similarity: float
    match_type: str  # "goal", "step", "combined"


@dataclass
class StepQueryResult:
    """步骤查询结果"""
    proc_id: str
    goal: str
    total_steps: int
    query_type: str  # "count", "first", "last", "after", "before", "all", "path"
    result: str
    full_sequence: List[str]
    paths: Optional[List[List[str]]] = None  # DAG 多路径
    reference: Optional[str] = None  # 参考动作


@dataclass
class CharacterResult:
    """人物分析结果"""
    character_id: str
    character_name: str
    involved_procedures: List[Dict]
    behavior_summary: str
    evidence_clips: List[int]


class ProcedureDAG:
    """
    Procedure 的有向无环图表示
    
    支持:
    - 线性步骤序列
    - 分支路径 (如: step1 -> step2a OR step2b -> step3)
    - 条件分支 (如: if X then step2a else step2b)
    """
    
    def __init__(self, proc_id: str, goal: str):
        self.proc_id = proc_id
        self.goal = goal
        
        # 节点: step_id -> step_content
        self.nodes: Dict[str, Dict] = {}
        
        # 边: (from_step, to_step) -> edge_info
        self.edges: Dict[Tuple[str, str], Dict] = {}
        
        # 入口和出口节点
        self.entry_nodes: List[str] = []
        self.exit_nodes: List[str] = []
    
    def add_step(self, step_id: str, action: str, metadata: Dict = None):
        """添加步骤节点"""
        self.nodes[step_id] = {
            'action': action,
            'metadata': metadata or {},
        }
    
    def add_edge(self, from_step: str, to_step: str, condition: str = None):
        """添加边（步骤间的转移）"""
        self.edges[(from_step, to_step)] = {
            'condition': condition,  # 如 "without X", "if Y"
        }
    
    def build_from_steps(self, steps: List[Dict]):
        """
        从 NSTF 图谱的 steps 列表构建 DAG
        
        支持两种格式:
        1. 简单列表: [{"action": "step1"}, {"action": "step2"}, ...]
        2. 带分支: [{"action": "step1", "next": ["step2a", "step2b"]}, ...]
        """
        if not steps:
            return
        
        # 创建节点
        for i, step in enumerate(steps):
            step_id = f"step_{i}"
            action = step.get('action', '') if isinstance(step, dict) else str(step)
            self.add_step(step_id, action, step if isinstance(step, dict) else {})
        
        # 创建边（默认线性连接）
        step_ids = list(self.nodes.keys())
        for i in range(len(step_ids) - 1):
            from_step = step_ids[i]
            to_step = step_ids[i + 1]
            
            # 检查是否有条件分支
            step_data = steps[i] if isinstance(steps[i], dict) else {}
            condition = step_data.get('condition')
            
            self.add_edge(from_step, to_step, condition)
        
        # 设置入口和出口
        if step_ids:
            self.entry_nodes = [step_ids[0]]
            self.exit_nodes = [step_ids[-1]]
    
    def enumerate_paths(self, max_paths: int = 10) -> List[List[str]]:
        """
        枚举所有从入口到出口的路径
        
        Returns:
            路径列表，每个路径是 action 字符串的列表
        """
        if not self.entry_nodes or not self.exit_nodes:
            # 如果没有显式的入口/出口，尝试返回线性序列
            if self.nodes:
                actions = [node['action'] for node in self.nodes.values() if node.get('action')]
                return [actions] if actions else []
            return []
        
        paths = []
        exit_set = set(self.exit_nodes)  # 优化查找
        
        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(paths) >= max_paths:
                return
            
            if current in visited:
                return  # 避免环
            
            if current not in self.nodes:
                return  # 节点不存在
            
            visited.add(current)
            action = self.nodes[current].get('action', '')
            if action:  # 只添加非空 action
                path.append(action)
            
            if current in exit_set:
                if path:  # 确保路径非空
                    paths.append(path.copy())
            else:
                # 获取后继节点
                successors = [to_step for (from_step, to_step) in self.edges 
                             if from_step == current]
                if not successors and path:
                    # 没有后继节点但有路径，视为终点
                    paths.append(path.copy())
                else:
                    for succ in successors:
                        dfs(succ, path.copy(), visited.copy())
        
        for entry in self.entry_nodes:
            dfs(entry, [], set())
        
        return paths if paths else [[]]  # 确保至少返回空列表而非空
    
    def get_linear_sequence(self) -> List[str]:
        """获取线性步骤序列（主路径）"""
        paths = self.enumerate_paths(max_paths=1)
        return paths[0] if paths else []
    
    def find_step_by_content(self, content: str) -> Optional[str]:
        """通过内容模糊匹配找到步骤 ID"""
        content_lower = content.lower()
        
        for step_id, node in self.nodes.items():
            action = node['action'].lower()
            if content_lower in action or action in content_lower:
                return step_id
        
        return None


class SymbolicFunctions:
    """
    Symbolic 函数封装
    
    提供三种核心查询函数的统一接口
    """
    
    def __init__(self, video_graph=None, nstf_graph: Dict = None):
        """
        Args:
            video_graph: M3-Agent VideoGraph 实例
            nstf_graph: NSTF 图谱字典
        """
        self.video_graph = video_graph
        self.nstf_graph = nstf_graph
        
        # DAG 缓存
        self._dag_cache: Dict[str, ProcedureDAG] = {}
    
    def set_graphs(self, video_graph=None, nstf_graph: Dict = None):
        """更新图谱引用"""
        if video_graph:
            self.video_graph = video_graph
        if nstf_graph:
            self.nstf_graph = nstf_graph
            self._dag_cache.clear()  # 清空 DAG 缓存
    
    # ==================== 核心 Symbolic 函数 ====================
    
    def get_procedure_with_evidence(
        self,
        proc_id: str,
        include_evidence: bool = True
    ) -> ProcedureResult:
        """
        Symbolic 函数 1: 获取 Procedure 及其 episodic 证据
        
        Args:
            proc_id: Procedure ID
            include_evidence: 是否包含 episodic 证据
            
        Returns:
            ProcedureResult
        """
        proc_nodes = self.nstf_graph.get('procedure_nodes', {}) if self.nstf_graph else {}
        proc = proc_nodes.get(proc_id, {})
        
        # 提取步骤
        steps = []
        for step in proc.get('steps', []):
            if isinstance(step, dict):
                action = step.get('action', '')
                if action:
                    steps.append(action)
        
        # 提取证据
        evidence = {}
        if include_evidence:
            for link in proc.get('episodic_links', []):
                clip_id = link.get('clip_id')
                if clip_id is not None:
                    content = self._get_clip_content(clip_id)
                    if content:
                        evidence[clip_id] = content
        
        return ProcedureResult(
            proc_id=proc_id,
            goal=proc.get('goal', 'Unknown'),
            steps=steps,
            episodic_evidence=evidence,
            similarity=0.0,  # 由外部设置
            match_type='procedure',
        )
    
    def query_step_sequence(
        self,
        proc_id: str,
        query: str,
        use_dag: bool = True
    ) -> StepQueryResult:
        """
        Symbolic 函数 2: 时序/步骤查询 (支持 DAG 多路径)
        
        Args:
            proc_id: Procedure ID
            query: 原始查询（用于推断查询类型）
            use_dag: 是否使用 DAG 表示
            
        Returns:
            StepQueryResult
        """
        proc_nodes = self.nstf_graph.get('procedure_nodes', {}) if self.nstf_graph else {}
        proc = proc_nodes.get(proc_id, {})
        
        # 获取或构建 DAG
        dag = self._get_or_build_dag(proc_id, proc)
        
        # 获取线性序列和所有路径
        linear_seq = dag.get_linear_sequence()
        all_paths = dag.enumerate_paths() if use_dag else [linear_seq]
        
        result = StepQueryResult(
            proc_id=proc_id,
            goal=proc.get('goal', 'Unknown'),
            total_steps=len(linear_seq),
            query_type='all',
            result='',
            full_sequence=linear_seq,
            paths=all_paths if len(all_paths) > 1 else None,
        )
        
        if not linear_seq:
            result.result = 'No steps found'
            return result
        
        query_lower = query.lower()
        
        # 判断查询类型并计算结果
        if any(kw in query_lower for kw in ['how many', 'count', '多少步', '几步']):
            result.query_type = 'count'
            result.result = f'{len(linear_seq)} steps'
            
        elif any(kw in query_lower for kw in ['first', 'begin', 'start', '第一', '开始']):
            result.query_type = 'first'
            result.result = linear_seq[0]
            
        elif any(kw in query_lower for kw in ['last', 'final', 'end', '最后', '结束']):
            result.query_type = 'last'
            result.result = linear_seq[-1]
            
        elif any(kw in query_lower for kw in ['after', 'then', 'next', '之后', '然后']):
            result.query_type = 'after'
            ref_action = self._find_reference_action(query, linear_seq)
            if ref_action and ref_action['index'] < len(linear_seq) - 1:
                result.result = linear_seq[ref_action['index'] + 1]
                result.reference = ref_action['action']
            else:
                result.result = linear_seq[-1]
                
        elif any(kw in query_lower for kw in ['before', 'previous', '之前']):
            result.query_type = 'before'
            ref_action = self._find_reference_action(query, linear_seq)
            if ref_action and ref_action['index'] > 0:
                result.result = linear_seq[ref_action['index'] - 1]
                result.reference = ref_action['action']
            else:
                result.result = linear_seq[0]
                
        elif any(kw in query_lower for kw in ['path', 'alternative', 'other way', '路径', '其他方式']):
            result.query_type = 'path'
            if all_paths and len(all_paths) > 1:
                path_strs = [' → '.join(p) for p in all_paths]
                result.result = f"Found {len(all_paths)} alternative paths:\n" + \
                               '\n'.join(f"  Path {i+1}: {p}" for i, p in enumerate(path_strs))
            else:
                result.result = ' → '.join(linear_seq)
        else:
            # 默认返回所有步骤
            result.query_type = 'all'
            result.result = ' → '.join(linear_seq)
        
        return result
    
    def aggregate_character_behaviors(
        self,
        character_id: str,
        name_resolver=None
    ) -> CharacterResult:
        """
        Symbolic 函数 3: 人物行为模式聚合
        
        Args:
            character_id: 人物 ID (如 "character_0")
            name_resolver: 名称解析器（可选）
            
        Returns:
            CharacterResult
        """
        proc_nodes = self.nstf_graph.get('procedure_nodes', {}) if self.nstf_graph else {}
        
        # 解析人物名称
        character_name = character_id
        if name_resolver:
            character_name = name_resolver.get_character_name(character_id)
        
        involved_procs = []
        evidence_clips = set()
        
        # 遍历所有 Procedure，找到涉及该人物的
        for proc_id, proc in proc_nodes.items():
            episodic_links = proc.get('episodic_links', [])
            
            proc_involves_character = False
            proc_clips = []
            
            for link in episodic_links:
                clip_id = link.get('clip_id')
                if clip_id is None:
                    continue
                
                # 检查该 clip 的内容是否涉及该人物
                clip_content = self._get_clip_content(clip_id)
                if character_id in clip_content:
                    proc_involves_character = True
                    proc_clips.append(clip_id)
            
            if proc_involves_character:
                involved_procs.append({
                    'proc_id': proc_id,
                    'goal': proc.get('goal', 'Unknown'),
                    'proc_type': proc.get('proc_type', 'task'),
                    'clips': proc_clips,
                })
                evidence_clips.update(proc_clips)
        
        # 生成行为摘要
        summary_parts = []
        if involved_procs:
            summary_parts.append(f"{character_name} is involved in {len(involved_procs)} procedure(s):")
            for proc in involved_procs:
                summary_parts.append(f"  - {proc['goal']} ({proc['proc_type']})")
            
            # 尝试推断行为模式
            if len(involved_procs) >= 2:
                goals = [p['goal'] for p in involved_procs]
                common_words = self._find_common_themes(goals)
                if common_words:
                    summary_parts.append(
                        f"Behavior pattern: Frequently involved in {', '.join(common_words)}-related activities."
                    )
        else:
            summary_parts.append(f"No procedure information found for {character_name}.")
        
        return CharacterResult(
            character_id=character_id,
            character_name=character_name,
            involved_procedures=involved_procs,
            behavior_summary='\n'.join(summary_parts),
            evidence_clips=sorted(evidence_clips),
        )
    
    # ==================== 辅助方法 ====================
    
    def _get_or_build_dag(self, proc_id: str, proc: Dict) -> ProcedureDAG:
        """获取或构建 Procedure 的 DAG 表示"""
        if proc_id in self._dag_cache:
            return self._dag_cache[proc_id]
        
        dag = ProcedureDAG(proc_id, proc.get('goal', 'Unknown'))
        dag.build_from_steps(proc.get('steps', []))
        
        self._dag_cache[proc_id] = dag
        return dag
    
    def _get_clip_content(self, clip_id: int) -> str:
        """获取 clip 内容"""
        if not self.video_graph:
            return ""
        
        if hasattr(self.video_graph, 'text_nodes_by_clip'):
            if clip_id not in self.video_graph.text_nodes_by_clip:
                return ""
            
            node_ids = self.video_graph.text_nodes_by_clip[clip_id]
            contents = []
            
            for nid in node_ids:
                node = self.video_graph.nodes.get(nid)
                if node and hasattr(node, 'metadata'):
                    node_contents = node.metadata.get('contents', [])
                    contents.extend(node_contents)
            
            return ' '.join(str(c) for c in contents)
        
        return ""
    
    def _find_reference_action(self, query: str, steps: List[str]) -> Optional[Dict]:
        """从查询中找到参考动作"""
        query_lower = query.lower()
        
        for i, step in enumerate(steps):
            step_lower = step.lower()
            # 简单的词重叠匹配
            query_words = set(query_lower.split())
            step_words = set(step_lower.split())
            overlap = query_words & step_words - {'the', 'a', 'an', 'is', 'are', 'to', 'of', 'and', 'or'}
            
            if len(overlap) >= 2:
                return {'index': i, 'action': step}
        
        return None
    
    def _find_common_themes(self, texts: List[str]) -> List[str]:
        """从文本列表中找出共同主题词"""
        if not texts:
            return []
        
        # 统计词频
        word_counts = defaultdict(int)
        stopwords = {'the', 'a', 'an', 'is', 'are', 'to', 'of', 'and', 'or', 'for', 'in', 'on', 'at'}
        
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            unique_words = set(words) - stopwords
            for word in unique_words:
                if len(word) > 2:
                    word_counts[word] += 1
        
        # 找出在多个文本中出现的词
        threshold = max(2, len(texts) // 2)
        common = [word for word, count in word_counts.items() if count >= threshold]
        
        return common[:5]  # 最多返回 5 个
    
    # ==================== 格式化输出 ====================
    
    def format_procedure_result(self, result: ProcedureResult) -> str:
        """格式化 Procedure 结果为 prompt 文本"""
        lines = [
            f"--- Procedure (Relevance: {result.similarity:.2f}, matched by {result.match_type}) ---",
            f"Goal: {result.goal}",
        ]
        
        for i, step in enumerate(result.steps, 1):
            lines.append(f"Step {i}: {step}")
        
        if result.episodic_evidence:
            lines.append("\n[Evidence from episodic memory]:")
            for clip_id, content in result.episodic_evidence.items():
                lines.append(f"  Clip {clip_id}: {content[:200]}...")
        
        return '\n'.join(lines)
    
    def format_step_query_result(self, result: StepQueryResult) -> str:
        """格式化步骤查询结果为 prompt 文本"""
        lines = [
            f"--- Procedure: {result.goal} ---",
            f"Query Type: {result.query_type}",
            f"Total Steps: {result.total_steps}",
        ]
        
        if result.reference:
            lines.append(f"Reference Action: {result.reference}")
        
        lines.append(f"Result: {result.result}")
        
        if result.paths and len(result.paths) > 1:
            lines.append(f"\n[Alternative paths available: {len(result.paths)}]")
        
        return '\n'.join(lines)
    
    def format_character_result(self, result: CharacterResult) -> str:
        """格式化人物分析结果为 prompt 文本"""
        lines = [
            f"--- Character Analysis: {result.character_name} ---",
            result.behavior_summary,
        ]
        
        if result.evidence_clips:
            lines.append(f"\nEvidence clips: {result.evidence_clips}")
        
        return '\n'.join(lines)
