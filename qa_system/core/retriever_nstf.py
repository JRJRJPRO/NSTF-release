# -*- coding: utf-8 -*-
"""
NSTF检索器 - 基于Procedure的增强检索

特性:
1. 多粒度Procedure匹配 (goal + steps)
2. episodic_links证据追溯
3. 智能fallback到baseline

基于 Stage 1/2 实验验证:
- threshold=0.30 (从0.40降低，提高命中率)
- min_confidence=0.25 (极低置信度也触发fallback)
- 不使用back_translate (实验证明无效)
"""

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
        
        # 使用NSTF
        metadata['decision'] = 'use_nstf'
        metadata['matched_procedures'] = [
            {'proc_id': p['proc_id'], 'similarity': p['similarity'], 'match_type': p['match_type']}
            for p in matched_procs[:self.max_procedures]
        ]
        
        memories = {}
        
        # 1. 添加Procedure结构化信息
        proc_info = self._format_procedures_for_prompt(
            matched_procs[:self.max_procedures], 
            nstf_graph
        )
        memories['NSTF_Procedures'] = proc_info
        
        # 2. 可选：追溯episodic证据
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
        
        metadata['num_evidence_clips'] = len(memories) - 1  # 减去NSTF_Procedures
        
        return memories, current_clips, metadata
    
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
