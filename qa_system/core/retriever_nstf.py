# -*- coding: utf-8 -*-
"""
NSTF检索器 - 基于Procedure的增强检索

特性:
1. 多粒度Procedure匹配 (goal + steps)
2. episodic_links证据追溯
3. 三种Symbolic查询函数:
   - get_procedure_with_evidence(): 核心检索
   - query_step_sequence(): 时序查询
   - aggregate_character_behaviors(): 人物行为聚合
4. 智能fallback到baseline

基于 Stage 1/2 实验验证:
- threshold=0.30 (从0.40降低，提高命中率)
- min_confidence=0.25 (极低置信度也触发fallback)
- 不使用back_translate (实验证明无效)
"""

import re
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# 统一环境设置
from env_setup import setup_all
setup_all()

from mmagent.utils.chat_api import parallel_get_embedding
from mmagent.retrieve import search as baseline_search
from mmagent.utils.general import load_video_graph


class NSTFRetriever:
    """
    NSTF检索器
    
    检索流程:
    1. 计算query与Procedure的多粒度相似度 (goal + steps)
    2. 如果命中 (sim >= threshold)，返回Procedure结构 + episodic证据
    3. 如果未命中 (sim < min_confidence)，fallback到baseline
    """
    
    def __init__(
        self,
        threshold: float = 0.30,              # 降低后的阈值 (Stage 1验证)
        min_confidence: float = 0.25,         # 最低置信度
        max_procedures: int = 3,              # 最大返回Procedure数
        topk_baseline: int = 10,              # Fallback时的baseline topk
        threshold_baseline: float = 0.3,      # Baseline阈值
        include_episodic_evidence: bool = True,  # 是否返回episodic证据
    ):
        self.threshold = threshold
        self.min_confidence = min_confidence
        self.max_procedures = max_procedures
        self.topk_baseline = topk_baseline
        self.threshold_baseline = threshold_baseline
        self.include_episodic_evidence = include_episodic_evidence
        
        # 缓存
        self._graph_cache: Dict[str, Any] = {}
        self._nstf_cache: Dict[str, Any] = {}
        self._embedding_cache: Dict[str, Dict] = {}  # Procedure embedding缓存
    
    def search(
        self,
        mem_path: str,
        query: str,
        current_clips: List = None,
        nstf_path: Optional[str] = None,
        before_clip: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], List, Dict]:
        """
        NSTF检索主入口
        
        Args:
            mem_path: 视频图谱路径
            query: 查询文本
            current_clips: 当前已检索的clips
            nstf_path: NSTF图谱路径（可选）
            before_clip: 时间截断点（可选）
            
        Returns:
            (memories, updated_clips, metadata)
            metadata包含: decision, matched_procedures, fallback_reason等
        """
        if current_clips is None:
            current_clips = []
        
        # 加载视频图谱
        video_graph = self._load_video_graph(mem_path)
        if before_clip is not None:
            video_graph.truncate_memory_by_clip(before_clip, False)
        video_graph.refresh_equivalences()
        
        # 加载NSTF图谱
        nstf_graph = self._load_nstf_graph(nstf_path) if nstf_path else None
        
        metadata = {
            'decision': 'unknown',
            'retriever': 'nstf_level',
        }
        
        # 如果没有NSTF图谱，直接fallback到baseline
        if nstf_graph is None:
            memories, current_clips, _ = baseline_search(
                video_graph, query, current_clips,
                threshold=self.threshold_baseline,
                topk=self.topk_baseline,
                before_clip=before_clip
            )
            metadata['decision'] = 'fallback'
            metadata['fallback_reason'] = 'No NSTF graph available'
            return memories, current_clips, metadata
        
        # NSTF检索流程
        proc_embeddings = self._get_procedure_embeddings(nstf_graph, nstf_path)
        
        if not proc_embeddings:
            # 没有有效的Procedure embedding
            memories, current_clips, _ = baseline_search(
                video_graph, query, current_clips,
                threshold=self.threshold_baseline,
                topk=self.topk_baseline,
                before_clip=before_clip
            )
            metadata['decision'] = 'fallback'
            metadata['fallback_reason'] = 'No procedure embeddings'
            return memories, current_clips, metadata
        
        # 多粒度Procedure检索
        matched_procs = self._search_procedures(query, proc_embeddings)
        
        # 判断是否使用NSTF
        if not matched_procs or matched_procs[0]['similarity'] < self.min_confidence:
            # Fallback到baseline
            memories, current_clips, _ = baseline_search(
                video_graph, query, current_clips,
                threshold=self.threshold_baseline,
                topk=self.topk_baseline,
                before_clip=before_clip
            )
            metadata['decision'] = 'fallback'
            if not matched_procs:
                metadata['fallback_reason'] = 'No procedures above threshold'
            else:
                metadata['fallback_reason'] = f'Top sim {matched_procs[0]["similarity"]:.3f} < min_confidence {self.min_confidence}'
            return memories, current_clips, metadata
        
        # 使用NSTF - 根据问题类型选择Symbolic函数
        metadata['decision'] = 'use_nstf'
        metadata['matched_procedures'] = [
            {'proc_id': p['proc_id'], 'similarity': p['similarity'], 'match_type': p['match_type']}
            for p in matched_procs[:self.max_procedures]
        ]
        
        # 分类问题类型
        query_type = self._classify_query(query)
        metadata['query_type'] = query_type
        
        memories = {}
        
        if query_type == 'temporal':
            # 时序查询：使用query_step_sequence()
            step_result = self.query_step_sequence(
                matched_procs[0]['proc_id'], 
                nstf_graph, 
                query
            )
            memories['NSTF_StepQuery'] = self._format_step_query_result(step_result)
            metadata['symbolic_function'] = 'query_step_sequence'
            
        elif query_type == 'character':
            # 人物理解：使用aggregate_character_behaviors()
            # 从query中提取人物ID
            character_id = self._extract_character_from_query(query, video_graph)
            if character_id:
                char_result = self.aggregate_character_behaviors(
                    character_id, 
                    nstf_graph, 
                    video_graph
                )
                memories['NSTF_CharacterAnalysis'] = self._format_character_result(char_result)
                metadata['symbolic_function'] = 'aggregate_character_behaviors'
                metadata['character_id'] = character_id
            else:
                # 无法提取人物，fallback到普通Procedure检索
                proc_info = self._format_procedures_for_prompt(
                    matched_procs[:self.max_procedures], 
                    nstf_graph
                )
                memories['NSTF_Procedures'] = proc_info
                metadata['symbolic_function'] = 'get_procedure_with_evidence'
        else:
            # 默认：使用get_procedure_with_evidence()
            proc_info = self._format_procedures_for_prompt(
                matched_procs[:self.max_procedures], 
                nstf_graph
            )
            memories['NSTF_Procedures'] = proc_info
            metadata['symbolic_function'] = 'get_procedure_with_evidence'
        
        # 追溯episodic证据（所有模式都需要）
        if self.include_episodic_evidence:
            evidence_clips = self._extract_episodic_evidence(
                matched_procs[:self.max_procedures],
                nstf_graph,
                video_graph
            )
            for clip_id, clip_content in evidence_clips.items():
                memories[f'clip_{clip_id}'] = clip_content
                if clip_id not in current_clips:
                    current_clips.append(clip_id)
        
        metadata['num_evidence_clips'] = len(memories) - 1
        
        return memories, current_clips, metadata
    
    # ==================== 三种Symbolic函数 ====================
    
    def query_step_sequence(
        self, 
        proc_id: str, 
        nstf_graph: Dict,
        query: str
    ) -> Dict[str, Any]:
        """
        Symbolic函数2: 时序/步骤查询
        
        用于回答:
        - "有多少步?" → 返回步骤数
        - "第一步/最后一步是什么?" → 返回特定步骤
        - "X之后做了什么?" → 找到X，返回下一步
        
        Args:
            proc_id: Procedure ID
            nstf_graph: NSTF图谱
            query: 原始查询（用于推断查询类型）
            
        Returns:
            {
                'proc_id': str,
                'goal': str,
                'total_steps': int,
                'query_type': str,  # 'count', 'first', 'last', 'after', 'before', 'all'
                'result': str,      # 查询结果
                'full_sequence': List[str],  # 完整步骤序列
            }
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        proc = proc_nodes.get(proc_id, {})
        
        steps = proc.get('steps', [])
        step_actions = []
        for s in steps:
            if isinstance(s, dict):
                action = s.get('action', '')
                if action:
                    step_actions.append(action)
        
        result = {
            'proc_id': proc_id,
            'goal': proc.get('goal', 'Unknown'),
            'total_steps': len(step_actions),
            'full_sequence': step_actions,
            'query_type': 'all',
            'result': None,
        }
        
        if not step_actions:
            result['result'] = 'No steps found'
            return result
        
        query_lower = query.lower()
        
        # 判断查询类型
        if any(kw in query_lower for kw in ['how many', 'count', '多少步', '几步']):
            result['query_type'] = 'count'
            result['result'] = f'{len(step_actions)} steps'
            
        elif any(kw in query_lower for kw in ['first', 'begin', 'start', '第一', '开始']):
            result['query_type'] = 'first'
            result['result'] = step_actions[0]
            
        elif any(kw in query_lower for kw in ['last', 'final', 'end', '最后', '结束']):
            result['query_type'] = 'last'
            result['result'] = step_actions[-1]
            
        elif any(kw in query_lower for kw in ['after', 'then', 'next', '之后', '然后']):
            result['query_type'] = 'after'
            # 尝试找到参考动作
            ref_action = self._find_reference_action(query, step_actions)
            if ref_action and ref_action['index'] < len(step_actions) - 1:
                result['result'] = step_actions[ref_action['index'] + 1]
                result['reference'] = ref_action['action']
            else:
                result['result'] = step_actions[-1] if step_actions else 'Unknown'
                
        elif any(kw in query_lower for kw in ['before', 'previous', '之前']):
            result['query_type'] = 'before'
            ref_action = self._find_reference_action(query, step_actions)
            if ref_action and ref_action['index'] > 0:
                result['result'] = step_actions[ref_action['index'] - 1]
                result['reference'] = ref_action['action']
            else:
                result['result'] = step_actions[0] if step_actions else 'Unknown'
        else:
            # 默认返回所有步骤
            result['query_type'] = 'all'
            result['result'] = ' → '.join(step_actions)
        
        return result
    
    def aggregate_character_behaviors(
        self,
        character_id: str,
        nstf_graph: Dict,
        video_graph
    ) -> Dict[str, Any]:
        """
        Symbolic函数3: 人物行为模式聚合
        
        用于回答: "Bob熟悉做饭吗?" "character_0有什么习惯?"
        
        Args:
            character_id: 人物ID (如 "character_0")
            nstf_graph: NSTF图谱
            video_graph: 视频图谱
            
        Returns:
            {
                'character': str,
                'involved_procedures': List[Dict],  # 涉及的Procedure列表
                'behavior_summary': str,            # 行为模式摘要
                'evidence_clips': List[int],        # 证据clip列表
            }
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        
        involved_procs = []
        evidence_clips = set()
        
        # 遍历所有Procedure，找到涉及该人物的
        for proc_id, proc in proc_nodes.items():
            episodic_links = proc.get('episodic_links', [])
            
            # 检查该Procedure的episodic_links是否涉及该人物
            proc_involves_character = False
            proc_clips = []
            
            for link in episodic_links:
                clip_id = link.get('clip_id')
                if clip_id is None:
                    continue
                
                # 检查该clip的内容是否涉及该人物
                clip_content = self._get_clip_content(video_graph, clip_id)
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
        if involved_procs:
            proc_types = [p['proc_type'] for p in involved_procs]
            goals = [p['goal'] for p in involved_procs]
            
            type_counts = {}
            for t in proc_types:
                type_counts[t] = type_counts.get(t, 0) + 1
            
            summary_parts = [f"{character_id} is involved in {len(involved_procs)} procedure(s):"]
            for proc in involved_procs:
                summary_parts.append(f"  - {proc['goal']} ({proc['proc_type']})")
            
            # 尝试推断行为模式
            if len(involved_procs) >= 2:
                common_words = self._find_common_themes(goals)
                if common_words:
                    summary_parts.append(f"Behavior pattern: Frequently involved in {', '.join(common_words)}-related activities.")
        else:
            summary_parts = [f"No procedure information found for {character_id}."]
        
        return {
            'character': character_id,
            'involved_procedures': involved_procs,
            'behavior_summary': '\n'.join(summary_parts),
            'evidence_clips': sorted(evidence_clips),
        }
    
    # ==================== 辅助方法 ====================
    
    def _classify_query(self, query: str) -> str:
        """分类问题类型: temporal, character, or procedure"""
        query_lower = query.lower()
        
        # 时序问题关键词
        temporal_keywords = [
            'after', 'before', 'then', 'next', 'first', 'last', 'step',
            'how many steps', 'sequence', 'order',
            '之后', '之前', '然后', '第一步', '最后', '步骤', '顺序'
        ]
        if any(kw in query_lower for kw in temporal_keywords):
            return 'temporal'
        
        # 人物理解关键词
        character_keywords = [
            'familiar', 'usually', 'habit', 'often', 'good at', 'skilled',
            'frequently', 'tend to', 'pattern', 'behavior',
            '熟悉', '习惯', '擅长', '经常', '行为', '模式'
        ]
        if any(kw in query_lower for kw in character_keywords):
            return 'character'
        
        return 'procedure'
    
    def _extract_character_from_query(self, query: str, video_graph) -> Optional[str]:
        """从查询中提取人物ID"""
        # 方法1: 直接匹配 character_X
        match = re.search(r'character_(\d+)', query.lower())
        if match:
            return f'character_{match.group(1)}'
        
        # 方法2: 尝试从video_graph的character_mappings中匹配人名
        if hasattr(video_graph, 'character_name_to_id'):
            for name, char_id in video_graph.character_name_to_id.items():
                if name.lower() in query.lower():
                    return char_id
        
        # 方法3: 匹配常见人名模式
        # 如果query中有人名但没有mapping，返回None
        return None
    
    def _find_reference_action(self, query: str, step_actions: List[str]) -> Optional[Dict]:
        """从查询中找到参考的动作"""
        query_lower = query.lower()
        
        for i, action in enumerate(step_actions):
            # 检查action中的关键词是否出现在query中
            action_words = action.lower().split()
            for word in action_words:
                if len(word) > 3 and word in query_lower:  # 忽略短词
                    return {'action': action, 'index': i}
        
        return None
    
    def _find_common_themes(self, goals: List[str]) -> List[str]:
        """从目标列表中找出共同主题"""
        # 简单实现：找高频词
        word_counts = {}
        stop_words = {'the', 'a', 'an', 'to', 'for', 'of', 'in', 'on', 'with', 'and'}
        
        for goal in goals:
            words = goal.lower().split()
            for word in words:
                if word not in stop_words and len(word) > 3:
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # 返回出现多次的词
        common = [w for w, c in word_counts.items() if c >= 2]
        return common[:3]  # 最多返回3个
    
    def _get_clip_content(self, video_graph, clip_id: int) -> str:
        """获取clip的内容"""
        if not hasattr(video_graph, 'text_nodes_by_clip'):
            return ''
        
        if clip_id not in video_graph.text_nodes_by_clip:
            return ''
        
        node_ids = video_graph.text_nodes_by_clip[clip_id]
        contents = []
        
        for nid in node_ids:
            node = video_graph.nodes.get(nid)
            if node and hasattr(node, 'metadata'):
                node_contents = node.metadata.get('contents', [])
                contents.extend(node_contents)
        
        return ' '.join(contents)
    
    def _format_step_query_result(self, result: Dict) -> str:
        """格式化时序查询结果"""
        lines = [
            "[Step Sequence Query]",
            f"Procedure: {result['goal']}",
            f"Total Steps: {result['total_steps']}",
            f"Query Type: {result['query_type']}",
        ]
        
        if result.get('reference'):
            lines.append(f"Reference: {result['reference']}")
        
        lines.append(f"Answer: {result['result']}")
        
        if result['total_steps'] > 0:
            sequence = ' → '.join(result['full_sequence'])
            lines.append(f"Full Sequence: {sequence}")
        
        return '\n'.join(lines)
    
    def _format_character_result(self, result: Dict) -> str:
        """格式化人物聚合结果"""
        lines = [
            "[Character Behavior Analysis]",
            f"Character: {result['character']}",
            "",
            result['behavior_summary'],
        ]
        
        if result['evidence_clips']:
            lines.append(f"\nEvidence from clips: {result['evidence_clips']}")
        
        return '\n'.join(lines)
    
    def _search_procedures(
        self, 
        query: str, 
        proc_embeddings: Dict
    ) -> List[Dict]:
        """
        多粒度Procedure检索
        
        同时检索goal和steps embedding，取最高相似度
        """
        # 计算query embedding
        query_embs, _ = parallel_get_embedding("text-embedding-3-large", [query])
        query_vec = np.array(query_embs[0])
        query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        
        results = []
        for proc_id, emb_dict in proc_embeddings.items():
            best_sim = -1
            best_type = None
            
            # 检查goal和steps embedding
            for emb_type in ['goal_emb', 'steps_emb']:
                if emb_type in emb_dict:
                    proc_vec = emb_dict[emb_type]
                    sim = float(np.dot(query_vec, proc_vec))
                    if sim > best_sim:
                        best_sim = sim
                        best_type = emb_type.replace('_emb', '')
            
            # 只保留超过threshold的
            if best_sim >= self.threshold:
                results.append({
                    'proc_id': proc_id,
                    'similarity': best_sim,
                    'match_type': best_type,
                })
        
        # 按相似度降序排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    
    def _format_procedures_for_prompt(
        self, 
        matched_procs: List[Dict], 
        nstf_graph: Dict
    ) -> str:
        """
        格式化Procedure为prompt文本
        
        格式:
        --- Procedure 1 (Relevance: 0.45) ---
        Goal: Preparing for a birthday party
        Step 1: Arrange childcare
        Step 2: Tidy the party area
        ...
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        lines = []
        
        for i, match in enumerate(matched_procs, 1):
            proc_id = match['proc_id']
            proc = proc_nodes.get(proc_id, {})
            
            lines.append(f"--- Procedure {i} (Relevance: {match['similarity']:.2f}, matched by {match['match_type']}) ---")
            lines.append(f"Goal: {proc.get('goal', 'Unknown')}")
            
            # 格式化steps
            steps = proc.get('steps', [])
            for j, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    action = step.get('action', '')
                    if action:
                        lines.append(f"Step {j}: {action}")
            
            lines.append("")  # 空行分隔
        
        return '\n'.join(lines)
    
    def _extract_episodic_evidence(
        self,
        matched_procs: List[Dict],
        nstf_graph: Dict,
        video_graph
    ) -> Dict[int, str]:
        """
        从matched procedures提取episodic证据
        
        通过episodic_links追溯到原始clip内容
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        clip_ids = set()
        
        # 收集所有相关的clip_id
        for match in matched_procs:
            proc = proc_nodes.get(match['proc_id'], {})
            for link in proc.get('episodic_links', []):
                clip_id = link.get('clip_id')
                if clip_id is not None:
                    clip_ids.add(clip_id)
        
        # 从video_graph获取clip内容
        # 修复 bug: 使用正确的 API text_nodes_by_clip
        evidence = {}
        
        # 正确方式: 通过 text_nodes_by_clip 获取 clip 对应的节点
        if hasattr(video_graph, 'text_nodes_by_clip'):
            for clip_id in clip_ids:
                if clip_id not in video_graph.text_nodes_by_clip:
                    continue
                
                node_ids = video_graph.text_nodes_by_clip[clip_id]
                clip_contents = []
                
                for nid in node_ids:
                    node = video_graph.nodes.get(nid)
                    if node and hasattr(node, 'metadata'):
                        # 从 metadata.contents 获取内容
                        contents = node.metadata.get('contents', [])
                        clip_contents.extend(contents)
                
                if clip_contents:
                    evidence[clip_id] = ' '.join(clip_contents)
        
        # Fallback: 尝试其他方式
        if not evidence and hasattr(video_graph, 'get_node_content'):
            for clip_id in clip_ids:
                try:
                    content = video_graph.get_node_content(f'clip_{clip_id}')
                    if content:
                        evidence[clip_id] = content
                except:
                    pass
        
        return evidence
    
    def _load_video_graph(self, mem_path: str):
        """加载视频图谱（带缓存）"""
        if mem_path not in self._graph_cache:
            self._graph_cache[mem_path] = load_video_graph(mem_path)
        return self._graph_cache[mem_path]
    
    def _load_nstf_graph(self, nstf_path: str) -> Optional[Dict]:
        """加载NSTF图谱（带缓存）"""
        if nstf_path is None:
            return None
            
        if nstf_path not in self._nstf_cache:
            try:
                with open(nstf_path, 'rb') as f:
                    self._nstf_cache[nstf_path] = pickle.load(f)
            except Exception as e:
                print(f"  ⚠️ 加载NSTF图谱失败 ({nstf_path}): {e}")
                self._nstf_cache[nstf_path] = None
        
        return self._nstf_cache[nstf_path]
    
    def _get_procedure_embeddings(self, nstf_graph: Dict, nstf_path: str) -> Dict:
        """
        获取/计算Procedure embeddings (带缓存)
        
        对每个Procedure计算:
        - goal_emb: goal文本的embedding
        - steps_emb: 所有步骤action连接后的embedding
        """
        if nstf_path in self._embedding_cache:
            return self._embedding_cache[nstf_path]
        
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        if not proc_nodes:
            return {}
        
        texts = []
        text_info = []  # (proc_id, emb_type)
        
        for proc_id, proc in proc_nodes.items():
            # Goal embedding
            goal = proc.get('goal', '')
            if goal and goal.strip():
                texts.append(goal)
                text_info.append((proc_id, 'goal'))
            
            # Steps combined embedding
            steps = proc.get('steps', [])
            if steps:
                actions = [s.get('action', '') for s in steps if isinstance(s, dict) and s.get('action')]
                combined = '. '.join(actions)
                if combined.strip():
                    texts.append(combined)
                    text_info.append((proc_id, 'steps'))
        
        if not texts:
            self._embedding_cache[nstf_path] = {}
            return {}
        
        # 批量计算embedding
        all_embs, _ = parallel_get_embedding("text-embedding-3-large", texts)
        
        # 组织结果
        result = {}
        for i, emb in enumerate(all_embs):
            proc_id, emb_type = text_info[i]
            if proc_id not in result:
                result[proc_id] = {}
            
            vec = np.array(emb)
            vec = vec / (np.linalg.norm(vec) + 1e-8)  # 归一化
            result[proc_id][f'{emb_type}_emb'] = vec
        
        self._embedding_cache[nstf_path] = result
        return result
    
    def clear_cache(self):
        """清除所有缓存"""
        self._graph_cache.clear()
        self._nstf_cache.clear()
        self._embedding_cache.clear()
    
    @property
    def mode_name(self) -> str:
        """返回模式名称"""
        return "NSTF-Level"
