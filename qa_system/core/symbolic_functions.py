# -*- coding: utf-8 -*-
"""Symbolic query functions for procedure retrieval, step queries, and character analysis."""

import re
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ProcedureResult:
    """Procedure query result."""
    proc_id: str
    goal: str
    steps: List[str]
    episodic_evidence: Dict[int, str]  # clip_id -> content
    similarity: float
    match_type: str  # "goal", "step", "combined"


@dataclass
class StepQueryResult:
    """Step query result."""
    proc_id: str
    goal: str
    total_steps: int
    query_type: str  # "count", "first", "last", "after", "before", "all", "path"
    result: str
    full_sequence: List[str]
    paths: Optional[List[List[str]]] = None  # DAG multi-paths
    reference: Optional[str] = None


@dataclass
class CharacterResult:
    """Character analysis result."""
    character_id: str
    character_name: str
    involved_procedures: List[Dict]
    behavior_summary: str
    evidence_clips: List[int]


class ProcedureDAG:
    """DAG representation of a Procedure supporting linear and branching step sequences."""

    def __init__(self, proc_id: str, goal: str):
        self.proc_id = proc_id
        self.goal = goal

        self.nodes: Dict[str, Dict] = {}
        self.edges: Dict[Tuple[str, str], Dict] = {}

        self.entry_nodes: List[str] = []
        self.exit_nodes: List[str] = []

    def add_step(self, step_id: str, action: str, metadata: Dict = None):
        """Add a step node."""
        self.nodes[step_id] = {
            'action': action,
            'metadata': metadata or {},
        }

    def add_edge(self, from_step: str, to_step: str, condition: str = None):
        """Add an edge (transition between steps)."""
        self.edges[(from_step, to_step)] = {
            'condition': condition,
        }

    def build_from_steps(self, steps: List[Dict]):
        """Build DAG from NSTF graph steps list."""
        if not steps:
            return

        for i, step in enumerate(steps):
            step_id = f"step_{i}"
            action = step.get('action', '') if isinstance(step, dict) else str(step)
            self.add_step(step_id, action, step if isinstance(step, dict) else {})

        step_ids = list(self.nodes.keys())
        for i in range(len(step_ids) - 1):
            from_step = step_ids[i]
            to_step = step_ids[i + 1]

            step_data = steps[i] if isinstance(steps[i], dict) else {}
            condition = step_data.get('condition')

            self.add_edge(from_step, to_step, condition)

        if step_ids:
            self.entry_nodes = [step_ids[0]]
            self.exit_nodes = [step_ids[-1]]

    def enumerate_paths(self, max_paths: int = 10) -> List[List[str]]:
        """Enumerate all paths from entry to exit."""
        if not self.entry_nodes or not self.exit_nodes:
            if self.nodes:
                actions = [node['action'] for node in self.nodes.values() if node.get('action')]
                return [actions] if actions else []
            return []

        paths = []
        exit_set = set(self.exit_nodes)

        def dfs(current: str, path: List[str], visited: Set[str]):
            if len(paths) >= max_paths:
                return

            if current in visited:
                return

            if current not in self.nodes:
                return

            visited.add(current)
            action = self.nodes[current].get('action', '')
            if action:
                path.append(action)

            if current in exit_set:
                if path:
                    paths.append(path.copy())
            else:
                successors = [to_step for (from_step, to_step) in self.edges
                             if from_step == current]
                if not successors and path:
                    paths.append(path.copy())
                else:
                    for succ in successors:
                        dfs(succ, path.copy(), visited.copy())

        for entry in self.entry_nodes:
            dfs(entry, [], set())

        return paths if paths else [[]]

    def get_linear_sequence(self) -> List[str]:
        """Get linear step sequence (main path)."""
        paths = self.enumerate_paths(max_paths=1)
        return paths[0] if paths else []

    def find_step_by_content(self, content: str) -> Optional[str]:
        """Find step ID by fuzzy content match."""
        content_lower = content.lower()

        for step_id, node in self.nodes.items():
            action = node['action'].lower()
            if content_lower in action or action in content_lower:
                return step_id

        return None


class SymbolicFunctions:
    """Symbolic function wrapper providing unified interface for three core query functions."""

    def __init__(self, video_graph=None, nstf_graph: Dict = None):
        self.video_graph = video_graph
        self.nstf_graph = nstf_graph

        self._dag_cache: Dict[str, ProcedureDAG] = {}

    def set_graphs(self, video_graph=None, nstf_graph: Dict = None):
        """Update graph references."""
        if video_graph:
            self.video_graph = video_graph
        if nstf_graph:
            self.nstf_graph = nstf_graph
            self._dag_cache.clear()

    # ==================== Core Symbolic Functions ====================

    def get_procedure_with_evidence(
        self,
        proc_id: str,
        include_evidence: bool = True
    ) -> ProcedureResult:
        """Symbolic function 1: Get Procedure with episodic evidence."""
        proc_nodes = self.nstf_graph.get('procedure_nodes', {}) if self.nstf_graph else {}
        proc = proc_nodes.get(proc_id, {})

        steps = []
        for step in proc.get('steps', []):
            if isinstance(step, dict):
                action = step.get('action', '')
                if action:
                    steps.append(action)

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
            similarity=0.0,
            match_type='procedure',
        )

    def query_step_sequence(
        self,
        proc_id: str,
        query: str,
        use_dag: bool = True
    ) -> StepQueryResult:
        """Symbolic function 2: Temporal/step query (supports DAG multi-path)."""
        proc_nodes = self.nstf_graph.get('procedure_nodes', {}) if self.nstf_graph else {}
        proc = proc_nodes.get(proc_id, {})

        dag = self._get_or_build_dag(proc_id, proc)

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

        if any(kw in query_lower for kw in ['how many', 'count']):
            result.query_type = 'count'
            result.result = f'{len(linear_seq)} steps'

        elif any(kw in query_lower for kw in ['first', 'begin', 'start']):
            result.query_type = 'first'
            result.result = linear_seq[0]

        elif any(kw in query_lower for kw in ['last', 'final', 'end']):
            result.query_type = 'last'
            result.result = linear_seq[-1]

        elif any(kw in query_lower for kw in ['after', 'then', 'next']):
            result.query_type = 'after'
            ref_action = self._find_reference_action(query, linear_seq)
            if ref_action and ref_action['index'] < len(linear_seq) - 1:
                result.result = linear_seq[ref_action['index'] + 1]
                result.reference = ref_action['action']
            else:
                result.result = linear_seq[-1]

        elif any(kw in query_lower for kw in ['before', 'previous']):
            result.query_type = 'before'
            ref_action = self._find_reference_action(query, linear_seq)
            if ref_action and ref_action['index'] > 0:
                result.result = linear_seq[ref_action['index'] - 1]
                result.reference = ref_action['action']
            else:
                result.result = linear_seq[0]

        elif any(kw in query_lower for kw in ['path', 'alternative', 'other way']):
            result.query_type = 'path'
            if all_paths and len(all_paths) > 1:
                path_strs = [' -> '.join(p) for p in all_paths]
                result.result = f"Found {len(all_paths)} alternative paths:\n" + \
                               '\n'.join(f"  Path {i+1}: {p}" for i, p in enumerate(path_strs))
            else:
                result.result = ' -> '.join(linear_seq)
        else:
            result.query_type = 'all'
            result.result = ' -> '.join(linear_seq)

        return result

    def aggregate_character_behaviors(
        self,
        character_id: str,
        name_resolver=None
    ) -> CharacterResult:
        """Symbolic function 3: Character behavior pattern aggregation."""
        proc_nodes = self.nstf_graph.get('procedure_nodes', {}) if self.nstf_graph else {}

        character_name = character_id
        if name_resolver:
            character_name = name_resolver.get_character_name(character_id)

        involved_procs = []
        evidence_clips = set()

        for proc_id, proc in proc_nodes.items():
            episodic_links = proc.get('episodic_links', [])

            proc_involves_character = False
            proc_clips = []

            for link in episodic_links:
                clip_id = link.get('clip_id')
                if clip_id is None:
                    continue

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

        summary_parts = []
        if involved_procs:
            summary_parts.append(f"{character_name} is involved in {len(involved_procs)} procedure(s):")
            for proc in involved_procs:
                summary_parts.append(f"  - {proc['goal']} ({proc['proc_type']})")

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

    # ==================== Helper Methods ====================

    def _get_or_build_dag(self, proc_id: str, proc: Dict) -> ProcedureDAG:
        """Get or build DAG for a Procedure."""
        if proc_id in self._dag_cache:
            return self._dag_cache[proc_id]

        dag = ProcedureDAG(proc_id, proc.get('goal', 'Unknown'))
        dag.build_from_steps(proc.get('steps', []))

        self._dag_cache[proc_id] = dag
        return dag

    def _get_clip_content(self, clip_id: int) -> str:
        """Get clip content."""
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
        """Find reference action from query."""
        query_lower = query.lower()

        for i, step in enumerate(steps):
            step_lower = step.lower()
            query_words = set(query_lower.split())
            step_words = set(step_lower.split())
            overlap = query_words & step_words - {'the', 'a', 'an', 'is', 'are', 'to', 'of', 'and', 'or'}

            if len(overlap) >= 2:
                return {'index': i, 'action': step}

        return None

    def _find_common_themes(self, texts: List[str]) -> List[str]:
        """Find common theme words from a list of texts."""
        if not texts:
            return []

        word_counts = defaultdict(int)
        stopwords = {'the', 'a', 'an', 'is', 'are', 'to', 'of', 'and', 'or', 'for', 'in', 'on', 'at'}

        for text in texts:
            words = re.findall(r'\w+', text.lower())
            unique_words = set(words) - stopwords
            for word in unique_words:
                if len(word) > 2:
                    word_counts[word] += 1

        threshold = max(2, len(texts) // 2)
        common = [word for word, count in word_counts.items() if count >= threshold]

        return common[:5]

    # ==================== Formatting ====================

    def format_procedure_result(self, result: ProcedureResult) -> str:
        """Format Procedure result for prompt."""
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
        """Format step query result for prompt."""
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
        """Format character analysis result for prompt."""
        lines = [
            f"--- Character Analysis: {result.character_name} ---",
            result.behavior_summary,
        ]

        if result.evidence_clips:
            lines.append(f"\nEvidence clips: {result.evidence_clips}")

        return '\n'.join(lines)
