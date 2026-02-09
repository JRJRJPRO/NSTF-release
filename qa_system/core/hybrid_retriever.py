# -*- coding: utf-8 -*-
"""
Hybrid Retriever - 论文 4.3 Hybrid Retrieval and Reasoning 完整实现

核心流程:
1. Query Classification (4.3.1)
2. Multi-Granularity Retrieval
3. Type-Aware Re-ranking (新增)
4. Symbolic Functions (4.3.2)

支持三种模式:
- baseline: M3-Agent 原始检索
- nstf_full: 完整 NSTF 检索 + Logic Layer
- ablation_*: 消融实验变体

特性:
- 统一使用 CacheManager 管理缓存
- 使用 NameResolver 解析人名
- 支持 DAG 多路径的 Procedure
- Type-Aware Re-ranking 提升相关性
"""

import os
import re
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# 统一环境设置
from env_setup import setup_all
setup_all()

# 基础模块
from mmagent.retrieve import search as baseline_search
from mmagent.utils.general import load_video_graph
from mmagent.utils.chat_api import parallel_get_embedding

# 本地模块
from .cache_manager import cache
from .query_classifier import QueryClassifier, QueryType, ClassificationResult
from .name_resolver import NameResolver, create_resolver
from .symbolic_functions import (
    SymbolicFunctions, 
    ProcedureResult, 
    StepQueryResult, 
    CharacterResult
)


@dataclass
class RetrievalConfig:
    """检索配置基类"""
    threshold: float = 0.3
    topk: int = 10
    include_episodic_evidence: bool = True


@dataclass
class BaselineConfig(RetrievalConfig):
    """Baseline 模式配置"""
    threshold: float = 0.3
    topk: int = 10
    mem_wise: bool = False


@dataclass
class NSTFConfig(RetrievalConfig):
    """NSTF 模式配置"""
    threshold: float = 0.35          # Procedure 匹配阈值（多粒度加权后）
    min_confidence: float = 0.30     # 最低置信度（低于此值触发 fallback）
    max_procedures: int = 3          # 最大返回 Procedure 数
    topk_baseline: int = 10          # Fallback 时的 baseline topk
    threshold_baseline: float = 0.3  # Baseline 阈值
    include_episodic_evidence: bool = True
    use_reranking: bool = False      # 暂时关闭 Re-ranking（未实现）
    use_dag_paths: bool = True       # 是否使用 DAG 多路径
    factual_hybrid: bool = True     # Factual 问题暂时不使用混合检索（避免复杂度）


@dataclass
class RetrievalResult:
    """检索结果"""
    memories: Dict[str, Any]
    clips: List[int]
    metadata: Dict[str, Any]
    

class HybridRetriever:
    """
    混合检索器 - 统一管理 Baseline/NSTF/Ablation 模式
    
    遵循论文 4.3 的完整流程:
    1. Query Classification
    2. Multi-Granularity Retrieval  
    3. Type-Aware Re-ranking
    4. Symbolic Functions
    """
    
    def __init__(
        self,
        mode: str = "baseline",
        baseline_config: BaselineConfig = None,
        nstf_config: NSTFConfig = None,
    ):
        """
        Args:
            mode: 运行模式
                - "baseline": M3-Agent 原始检索
                - "nstf_full": 完整 NSTF
                - "ablation_prototype": 无结构
                - "ablation_structure": 有结构无推理
            baseline_config: Baseline 配置
            nstf_config: NSTF 配置
        """
        self.mode = mode
        self.baseline_config = baseline_config or BaselineConfig()
        self.nstf_config = nstf_config or NSTFConfig()
        
        # 组件
        self.query_classifier = QueryClassifier()
        self.symbolic_functions = SymbolicFunctions()
        self.name_resolver: Optional[NameResolver] = None
        
        # 当前图谱引用
        self._current_video_graph = None
        self._current_nstf_graph = None
    
    def search(
        self,
        mem_path: str,
        query: str,
        current_clips: List = None,
        nstf_path: Optional[str] = None,
        before_clip: Optional[int] = None,
    ) -> RetrievalResult:
        """
        执行混合检索
        
        Args:
            mem_path: 视频图谱路径
            query: 查询文本
            current_clips: 当前已检索的 clips
            nstf_path: NSTF 图谱路径（可选）
            before_clip: 时间截断点（可选）
            
        Returns:
            RetrievalResult 包含 memories, clips, metadata
        """
        if current_clips is None:
            current_clips = []
        
        # 1. 加载图谱
        video_graph = self._load_video_graph(mem_path)
        if before_clip is not None:
            video_graph.truncate_memory_by_clip(before_clip, False)
        video_graph.refresh_equivalences()
        
        self._current_video_graph = video_graph
        
        # 初始化 NameResolver
        self.name_resolver = NameResolver(video_graph)
        
        # 2. 实体 ID 查询特殊处理
        if self._contains_entity_id(query):
            return self._handle_entity_id_query(video_graph, query, before_clip)
        
        # 3. 根据模式分发
        if self.mode == "baseline":
            return self._search_baseline(video_graph, query, current_clips, before_clip)
        
        elif self.mode == "nstf_full":
            nstf_graph = self._load_nstf_graph(nstf_path) if nstf_path else None
            return self._search_nstf_full(
                video_graph, nstf_graph, query, current_clips, before_clip
            )
        
        elif self.mode.startswith("ablation_"):
            nstf_graph = self._load_nstf_graph(nstf_path) if nstf_path else None
            ablation_type = self.mode.replace("ablation_", "")
            return self._search_ablation(
                video_graph, nstf_graph, query, current_clips, 
                ablation_type, before_clip
            )
        
        else:
            # 默认使用 baseline
            return self._search_baseline(video_graph, query, current_clips, before_clip)
    
    # ==================== 模式实现 ====================
    
    def _search_baseline(
        self,
        video_graph,
        query: str,
        current_clips: List,
        before_clip: Optional[int]
    ) -> RetrievalResult:
        """Baseline 检索 (M3-Agent 原始)"""
        config = self.baseline_config
        
        memories, current_clips, _ = baseline_search(
            video_graph, query, current_clips,
            threshold=config.threshold,
            topk=config.topk,
            before_clip=before_clip
        )
        
        return RetrievalResult(
            memories=memories,
            clips=current_clips,
            metadata={
                'mode': 'baseline',
                'retriever': 'M3-Agent',
            }
        )
    
    def _search_nstf_full(
        self,
        video_graph,
        nstf_graph: Optional[Dict],
        query: str,
        current_clips: List,
        before_clip: Optional[int]
    ) -> RetrievalResult:
        """
        完整 NSTF 检索
        
        流程:
        1. Query Classification
        2. Multi-Granularity Procedure 匹配
        3. Type-Aware Re-ranking
        4. Symbolic Function 调用
        5. Episodic Evidence 追溯
        """
        config = self.nstf_config
        metadata = {'mode': 'nstf_full', 'retriever': 'HybridRetriever'}
        
        # 如果没有 NSTF 图谱，fallback 到 baseline
        if nstf_graph is None:
            return self._fallback_to_baseline(
                video_graph, query, current_clips, before_clip,
                reason="No NSTF graph available"
            )
        
        self._current_nstf_graph = nstf_graph
        self.symbolic_functions.set_graphs(video_graph, nstf_graph)
        self.name_resolver = NameResolver(video_graph, nstf_graph)
        
        # Step 1: Query Classification
        classification = self.query_classifier.classify(query)
        metadata['query_type'] = classification.query_type.value
        metadata['classification_confidence'] = classification.confidence
        metadata['classification_method'] = classification.method
        
        # Step 2: Multi-Granularity Procedure 匹配
        proc_embeddings = self._get_procedure_embeddings(nstf_graph)
        
        if not proc_embeddings:
            return self._fallback_to_baseline(
                video_graph, query, current_clips, before_clip,
                reason="No procedure embeddings"
            )
        
        matched_procs = self._search_procedures(query, proc_embeddings)
        
        # 检查是否有有效匹配
        if not matched_procs or matched_procs[0]['similarity'] < config.min_confidence:
            return self._fallback_to_baseline(
                video_graph, query, current_clips, before_clip,
                reason=f"Top sim {matched_procs[0]['similarity'] if matched_procs else 0:.3f} < min_confidence"
            )
        
        # Step 3: Type-Aware Re-ranking
        if config.use_reranking:
            matched_procs = self._apply_reranking(
                matched_procs, classification.query_type, nstf_graph
            )
        
        metadata['matched_procedures'] = [
            {
                'proc_id': p['proc_id'], 
                'similarity': p['similarity'], 
                'match_type': p['match_type']
            }
            for p in matched_procs[:config.max_procedures]
        ]
        
        # Step 4: 根据 Query Type 调用 Symbolic Function
        memories = {}
        
        if classification.query_type == QueryType.PROCEDURAL:
            # 时序查询
            step_result = self.symbolic_functions.query_step_sequence(
                matched_procs[0]['proc_id'], 
                query,
                use_dag=config.use_dag_paths
            )
            memories['NSTF_StepQuery'] = self.symbolic_functions.format_step_query_result(step_result)
            metadata['symbolic_function'] = 'query_step_sequence'
            
        elif classification.query_type == QueryType.CHARACTER:
            # 人物理解
            character_id = self._extract_character_from_query(query, video_graph)
            if character_id:
                char_result = self.symbolic_functions.aggregate_character_behaviors(
                    character_id, self.name_resolver
                )
                memories['NSTF_CharacterAnalysis'] = self.symbolic_functions.format_character_result(char_result)
                metadata['symbolic_function'] = 'aggregate_character_behaviors'
                metadata['character_id'] = character_id
            else:
                # 无法提取人物，使用标准 Procedure 检索
                self._add_procedure_memories(memories, matched_procs, nstf_graph, config, video_graph)
                metadata['symbolic_function'] = 'get_procedure_with_evidence'
                
        elif classification.query_type == QueryType.CONSTRAINT:
            # 约束查询 - 可能需要多路径
            self._add_procedure_memories(memories, matched_procs, nstf_graph, config, video_graph)
            metadata['symbolic_function'] = 'get_procedure_with_evidence'
            
            # 如果是 DAG，添加路径信息
            if config.use_dag_paths:
                for proc in matched_procs[:config.max_procedures]:
                    step_result = self.symbolic_functions.query_step_sequence(
                        proc['proc_id'], query, use_dag=True
                    )
                    if step_result.paths and len(step_result.paths) > 1:
                        memories[f'NSTF_Paths_{proc["proc_id"]}'] = (
                            f"Alternative paths available: {len(step_result.paths)}"
                        )
        else:
            # 默认: Factual 查询 - 使用混合检索
            if config.factual_hybrid:
                # 先用 baseline 向量搜索，获取相关的 episodic memories
                baseline_memories, current_clips, _ = baseline_search(
                    video_graph, query, current_clips,
                    threshold=config.threshold_baseline,
                    topk=config.topk_baseline,
                    before_clip=before_clip
                )
                memories.update(baseline_memories)
                metadata['symbolic_function'] = 'hybrid_factual'
                metadata['baseline_clips'] = len(baseline_memories)
            
            # 如果有高质量的 Procedure 匹配，也添加进来
            if matched_procs and matched_procs[0]['similarity'] >= config.threshold:
                self._add_procedure_memories(memories, matched_procs, nstf_graph, config, video_graph)
                if 'symbolic_function' not in metadata or metadata['symbolic_function'] == 'hybrid_factual':
                    metadata['symbolic_function'] = 'hybrid_factual_with_proc'
            elif not config.factual_hybrid:
                # 如果没开启混合模式，还是用原来的逻辑
                self._add_procedure_memories(memories, matched_procs, nstf_graph, config, video_graph)
                metadata['symbolic_function'] = 'get_procedure_with_evidence'
        
        # Step 5: 追溯 Episodic Evidence
        evidence_clips = {}  # 初始化避免 UnboundLocalError
        if config.include_episodic_evidence:
            evidence_clips = self._extract_episodic_evidence(
                matched_procs[:config.max_procedures],
                nstf_graph,
                video_graph
            )
            for clip_id, clip_content in evidence_clips.items():
                # 使用 NameResolver 替换人名
                resolved_content = self.name_resolver.resolve_text(clip_content)
                memories[f'clip_{clip_id}'] = resolved_content
                if clip_id not in current_clips:
                    current_clips.append(clip_id)
        
        metadata['num_evidence_clips'] = len(evidence_clips)
        metadata['decision'] = 'use_nstf'
        
        return RetrievalResult(
            memories=memories,
            clips=current_clips,
            metadata=metadata
        )
    
    def _search_ablation(
        self,
        video_graph,
        nstf_graph: Optional[Dict],
        query: str,
        current_clips: List,
        ablation_type: str,
        before_clip: Optional[int]
    ) -> RetrievalResult:
        """消融实验检索"""
        metadata = {'mode': f'ablation_{ablation_type}', 'retriever': 'HybridRetriever'}
        
        if nstf_graph is None:
            return self._fallback_to_baseline(
                video_graph, query, current_clips, before_clip,
                reason="No NSTF graph for ablation"
            )
        
        if ablation_type == "prototype":
            # 消融 A: 无结构，只用向量相似度
            return self._ablation_prototype(video_graph, nstf_graph, query, current_clips, before_clip)
        
        elif ablation_type == "structure":
            # 消融 B: 有结构无推理
            return self._ablation_structure(video_graph, nstf_graph, query, current_clips, before_clip)
        
        else:
            # 未知消融类型，fallback
            return self._fallback_to_baseline(
                video_graph, query, current_clips, before_clip,
                reason=f"Unknown ablation type: {ablation_type}"
            )
    
    def _ablation_prototype(
        self,
        video_graph,
        nstf_graph: Dict,
        query: str,
        current_clips: List,
        before_clip: Optional[int]
    ) -> RetrievalResult:
        """消融 A: 纯向量检索（无 Procedure 结构）"""
        config = self.nstf_config
        
        # 直接用 baseline 向量检索，但用 NSTF 的阈值
        memories, current_clips, _ = baseline_search(
            video_graph, query, current_clips,
            threshold=config.threshold,
            topk=config.topk_baseline,
            before_clip=before_clip
        )
        
        return RetrievalResult(
            memories=memories,
            clips=current_clips,
            metadata={
                'mode': 'ablation_prototype',
                'decision': 'prototype_only',
            }
        )
    
    def _ablation_structure(
        self,
        video_graph,
        nstf_graph: Dict,
        query: str,
        current_clips: List,
        before_clip: Optional[int]
    ) -> RetrievalResult:
        """消融 B: 有结构无推理（返回 Procedure 但不调用 Symbolic）"""
        config = self.nstf_config
        
        proc_embeddings = self._get_procedure_embeddings(nstf_graph)
        
        if not proc_embeddings:
            return self._fallback_to_baseline(
                video_graph, query, current_clips, before_clip,
                reason="No procedure embeddings for structure ablation"
            )
        
        matched_procs = self._search_procedures(query, proc_embeddings)
        
        if not matched_procs:
            return self._fallback_to_baseline(
                video_graph, query, current_clips, before_clip,
                reason="No procedures matched"
            )
        
        memories = {}
        self._add_procedure_memories(memories, matched_procs, nstf_graph, config, video_graph)
        
        # 不调用 Symbolic 函数，直接返回结构
        return RetrievalResult(
            memories=memories,
            clips=current_clips,
            metadata={
                'mode': 'ablation_structure',
                'decision': 'structure_only',
                'matched_procedures': [p['proc_id'] for p in matched_procs[:config.max_procedures]],
            }
        )
    
    # ==================== Type-Aware Re-ranking ====================
    
    def _apply_reranking(
        self,
        matched_procs: List[Dict],
        query_type: QueryType,
        nstf_graph: Dict
    ) -> List[Dict]:
        """
        Type-Aware Re-ranking
        
        根据 query_type 调整 Procedure 排序:
        - PROCEDURAL: 优先多步骤的 Procedure
        - CHARACTER: 优先人物相关的 Procedure
        - CONSTRAINT: 优先有分支路径的 Procedure
        - FACTUAL: 保持原始相似度排序
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        
        def get_rerank_score(proc_match: Dict) -> float:
            """计算 re-ranking 分数"""
            base_score = proc_match['similarity']
            proc = proc_nodes.get(proc_match['proc_id'], {})
            
            boost = 0.0
            
            if query_type == QueryType.PROCEDURAL:
                # 步骤数加成
                num_steps = len(proc.get('steps', []))
                if num_steps >= 3:
                    boost += 0.05
                if num_steps >= 5:
                    boost += 0.03
                    
            elif query_type == QueryType.CHARACTER:
                # 人物关联加成
                episodic_links = proc.get('episodic_links', [])
                if len(episodic_links) >= 2:
                    boost += 0.05
                    
            elif query_type == QueryType.CONSTRAINT:
                # 有备选方案加成
                proc_type = proc.get('proc_type', '')
                if 'alternative' in proc_type.lower():
                    boost += 0.08
            
            return base_score + boost
        
        # 重新排序
        for proc in matched_procs:
            proc['rerank_score'] = get_rerank_score(proc)
        
        matched_procs.sort(key=lambda x: x['rerank_score'], reverse=True)
        return matched_procs
    
    # ==================== 辅助方法 ====================
    
    def _contains_entity_id(self, query: str) -> bool:
        """检测查询是否包含实体 ID"""
        return "character id" in query
    
    def _handle_entity_id_query(
        self,
        video_graph,
        query: str,
        before_clip: Optional[int]
    ) -> RetrievalResult:
        """处理实体 ID 查询"""
        memories, _, _ = baseline_search(
            video_graph, query, [],
            mem_wise=True, topk=20,
            before_clip=before_clip
        )
        return RetrievalResult(
            memories=memories,
            clips=[],
            metadata={'mode': 'entity_id_query'}
        )
    
    def _fallback_to_baseline(
        self,
        video_graph,
        query: str,
        current_clips: List,
        before_clip: Optional[int],
        reason: str
    ) -> RetrievalResult:
        """
        Fallback 到 baseline 检索
        
        V2.4 改进:
        - 使用更宽松的阈值确保有结果返回
        - 标记 use_baseline_prompt 让 runner 使用简单 prompt
        """
        config = self.nstf_config
        
        # V2.4: 使用更宽松的阈值，确保返回结果
        # 原始 baseline 的默认阈值是 0.3，这里降到 0.25
        fallback_threshold = min(config.threshold_baseline, 0.25)
        
        memories, current_clips, _ = baseline_search(
            video_graph, query, current_clips,
            threshold=fallback_threshold,
            topk=config.topk_baseline,
            before_clip=before_clip
        )
        
        return RetrievalResult(
            memories=memories,
            clips=current_clips,
            metadata={
                'mode': self.mode,
                'decision': 'fallback',
                'fallback_reason': reason,
                # V2.4: 标记使用 baseline prompt
                # 当 NSTF 匹配失败时，复杂的 NSTF prompt 会误导 LLM
                'use_baseline_prompt': True,
            }
        )
    
    def _load_video_graph(self, mem_path: str):
        """加载视频图谱（使用 CacheManager）"""
        return cache.get_video_graph(mem_path, load_video_graph)
    
    def _load_nstf_graph(self, nstf_path: str) -> Optional[Dict]:
        """加载 NSTF 图谱（使用 CacheManager）"""
        def loader(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return cache.get_nstf_graph(nstf_path, loader)
    
    def _get_procedure_embeddings(self, nstf_graph: Dict) -> Dict:
        """获取 Procedure embeddings（使用 CacheManager）"""
        graph_id = id(nstf_graph)
        
        # 尝试从缓存获取
        cached = cache.get_embeddings(f"proc_emb_{graph_id}")
        if cached:
            return cached
        
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        if not proc_nodes:
            return {}
        
        texts = []
        text_info = []
        
        for proc_id, proc in proc_nodes.items():
            # Goal embedding
            goal = proc.get('goal', '')
            if goal and goal.strip():
                texts.append(goal)
                text_info.append((proc_id, 'goal'))
            
            # Steps combined embedding
            steps = proc.get('steps', [])
            if steps:
                actions = [s.get('action', '') for s in steps 
                          if isinstance(s, dict) and s.get('action')]
                combined = '. '.join(actions)
                if combined.strip():
                    texts.append(combined)
                    text_info.append((proc_id, 'steps'))
        
        if not texts:
            return {}
        
        # 批量计算 embedding
        all_embs, _ = parallel_get_embedding("text-embedding-3-large", texts)
        
        # 组织结果
        result = {}
        for i, emb in enumerate(all_embs):
            proc_id, emb_type = text_info[i]
            if proc_id not in result:
                result[proc_id] = {}
            
            vec = np.array(emb)
            vec = vec / (np.linalg.norm(vec) + 1e-8)
            result[proc_id][f'{emb_type}_emb'] = vec
        
        # 保存到缓存
        cache.set_embeddings(f"proc_emb_{graph_id}", result)
        return result
    
    def _search_procedures(
        self,
        query: str,
        proc_embeddings: Dict,
        alpha: float = 0.4
    ) -> List[Dict]:
        """
        多粒度 Procedure 检索
        
        论文公式 (4.3.2):
        score(q, N) = α·sim(φ(q), i_goal) + (1-α)·sim(φ(q), i_step)
        
        Args:
            query: 查询文本
            proc_embeddings: Procedure embeddings 字典
            alpha: goal vs steps 权重 (论文默认 0.3)
        """
        # 计算 query embedding
        query_embs, _ = parallel_get_embedding("text-embedding-3-large", [query])
        query_vec = np.array(query_embs[0])
        query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        
        results = []
        config = self.nstf_config
        
        for proc_id, embs in proc_embeddings.items():
            goal_sim = 0.0
            steps_sim = 0.0
            has_goal = 'goal_emb' in embs
            has_steps = 'steps_emb' in embs
            
            if has_goal:
                goal_sim = float(np.dot(query_vec, embs['goal_emb']))
            if has_steps:
                steps_sim = float(np.dot(query_vec, embs['steps_emb']))
            
            # 论文公式: 加权平均得分
            # 重要: 如果只有 goal_emb (steps为空), 直接用 goal_sim 作为分数
            # 如果只有 steps_emb (无goal), 直接用 steps_sim 作为分数
            # 如果两者都有, 使用加权平均
            if has_goal and has_steps:
                combined_score = alpha * goal_sim + (1 - alpha) * steps_sim
            elif has_goal:
                combined_score = goal_sim  # 只有 goal, 不惩罚缺失的 steps
            elif has_steps:
                combined_score = steps_sim  # 只有 steps, 不惩罚缺失的 goal
            else:
                combined_score = 0.0  # 都没有, 跳过
            
            # 确定主要匹配类型（用于元数据）
            if has_goal and has_steps:
                match_type = 'goal' if goal_sim >= steps_sim else 'steps'
            elif has_goal:
                match_type = 'goal_only'
            elif has_steps:
                match_type = 'steps_only'
            else:
                match_type = 'none'
            
            # 根据阈值过滤
            if combined_score >= config.threshold:
                results.append({
                    'proc_id': proc_id,
                    'similarity': combined_score,
                    'goal_sim': goal_sim,
                    'steps_sim': steps_sim,
                    'match_type': match_type,
                })
            elif combined_score >= config.min_confidence:
                # 低于阈值但高于最低置信度，标记为 combined
                results.append({
                    'proc_id': proc_id,
                    'similarity': combined_score,
                    'goal_sim': goal_sim,
                    'steps_sim': steps_sim,
                    'match_type': 'combined',
                })
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    
    def _add_procedure_memories(
        self,
        memories: Dict,
        matched_procs: List[Dict],
        nstf_graph: Dict,
        config: NSTFConfig,
        video_graph = None
    ):
        """
        添加 Procedure 到 memories（带人名解析）
        
        重要改进: 直接返回 episodic_links 关联的完整 clip 内容，
        而不只是 preview，以提高 LLM 回答准确率
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        lines = []
        
        # 检查是否有真实人名可用
        has_real_names = False
        if self.name_resolver:
            mappings = self.name_resolver.get_all_mappings()
            # 检查是否有真实人名（非 ID 格式）
            has_real_names = any(
                not v.startswith(('character_', 'person_', 'face_', 'voice_'))
                for v in mappings.values()
            )
        
        if not has_real_names:
            lines.append("[Note: Real names are not available in this video. 'character_X' refers to distinct individuals identified by face/voice recognition. Do not ask about their real names.]")
            lines.append("")
        
        for i, match in enumerate(matched_procs[:config.max_procedures], 1):
            proc_id = match['proc_id']
            proc = proc_nodes.get(proc_id, {})
            
            lines.append(f"--- Procedure {i} (Relevance: {match['similarity']:.2f}, matched by {match['match_type']}) ---")
            
            # Goal - 进行人名解析
            goal = proc.get('goal', 'Unknown')
            if self.name_resolver:
                goal = self.name_resolver.resolve_text(goal)
            lines.append(f"Goal: {goal}")
            
            # Description - 包含更详细的上下文信息
            description = proc.get('description', '')
            if description:
                if self.name_resolver:
                    description = self.name_resolver.resolve_text(description)
                lines.append(f"Context: {description}")
            
            # Steps - 进行人名解析
            steps = proc.get('steps', [])
            for j, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    action = step.get('action', '')
                    if action:
                        if self.name_resolver:
                            action = self.name_resolver.resolve_text(action)
                        lines.append(f"Step {j}: {action}")
            
            # Episodic links - 返回完整的 clip 内容而不只是 preview
            episodic_links = proc.get('episodic_links', [])
            if episodic_links and video_graph:
                lines.append("")
                lines.append("=== Video Evidence (from linked episodic memories) ===")
                
                # 限制最多 2 个 clip，防止 token 溢出
                clips_added = 0
                max_clips = 2
                max_content_len = 800  # 每个 clip 最多 800 字符
                
                for link in episodic_links[:5]:
                    if clips_added >= max_clips:
                        break
                        
                    clip_id = link.get('clip_id')
                    if clip_id is None:
                        continue
                    
                    # 确保 clip_id 是整数类型
                    try:
                        clip_id = int(clip_id)
                    except (ValueError, TypeError):
                        continue
                    
                    # 从 video_graph 获取完整的 clip 内容
                    full_content = self._get_clip_full_content(video_graph, clip_id)
                    if full_content:
                        # 截断过长的内容
                        if len(full_content) > max_content_len:
                            full_content = full_content[:max_content_len] + "...[truncated]"
                        
                        if self.name_resolver:
                            full_content = self.name_resolver.resolve_text(full_content)
                        sim = link.get('similarity', 0)
                        lines.append(f"[CLIP_{clip_id}] (relevance: {sim:.2f})")
                        lines.append(full_content)
                        lines.append("")
                        clips_added += 1
                
                # 如果没有获取到任何内容，回退到 preview
                if clips_added == 0:
                    for link in episodic_links[:2]:
                        preview = link.get('content_preview', '')
                        if preview:
                            if self.name_resolver:
                                preview = self.name_resolver.resolve_text(preview)
                            lines.append(f"  - {preview}")
                            
            elif episodic_links:
                # 没有 video_graph 时回退到 preview
                lines.append("Evidence from video:")
                for link in episodic_links[:2]:
                    preview = link.get('content_preview', '')
                    if preview:
                        if self.name_resolver:
                            preview = self.name_resolver.resolve_text(preview)
                        lines.append(f"  - {preview}")
            
            lines.append("")
        
        memories['NSTF_Procedures'] = '\n'.join(lines)
    
    def _get_clip_full_content(self, video_graph, clip_id: int) -> str:
        """从 video_graph 获取单个 clip 的完整内容"""
        if not hasattr(video_graph, 'text_nodes_by_clip'):
            return ''
        
        # 确保 clip_id 是整数
        try:
            clip_id = int(clip_id)
        except (ValueError, TypeError):
            return ''
        
        if clip_id not in video_graph.text_nodes_by_clip:
            return ''
        
        node_ids = video_graph.text_nodes_by_clip[clip_id]
        contents = []
        
        for nid in node_ids:
            node = video_graph.nodes.get(nid)
            if node and hasattr(node, 'metadata'):
                node_contents = node.metadata.get('contents', [])
                contents.extend(str(c) for c in node_contents)
        
        return ' '.join(contents)
    
    def _extract_episodic_evidence(
        self,
        matched_procs: List[Dict],
        nstf_graph: Dict,
        video_graph
    ) -> Dict[int, str]:
        """提取 episodic 证据"""
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        clip_ids = set()
        
        for match in matched_procs:
            proc = proc_nodes.get(match['proc_id'], {})
            for link in proc.get('episodic_links', []):
                clip_id = link.get('clip_id')
                if clip_id is not None:
                    clip_ids.add(clip_id)
        
        evidence = {}
        
        if hasattr(video_graph, 'text_nodes_by_clip'):
            for clip_id in clip_ids:
                if clip_id not in video_graph.text_nodes_by_clip:
                    continue
                
                node_ids = video_graph.text_nodes_by_clip[clip_id]
                contents = []
                
                for nid in node_ids:
                    node = video_graph.nodes.get(nid)
                    if node and hasattr(node, 'metadata'):
                        node_contents = node.metadata.get('contents', [])
                        contents.extend(str(c) for c in node_contents)
                
                if contents:
                    evidence[clip_id] = ' '.join(contents)
        
        return evidence
    
    def _extract_character_from_query(self, query: str, video_graph) -> Optional[str]:
        """从查询中提取人物 ID"""
        # 直接匹配 character_X 格式
        match = re.search(r'character_\d+', query, re.IGNORECASE)
        if match:
            return match.group(0)
        
        # 匹配 face_X 或 voice_X
        match = re.search(r'(face|voice)_\d+', query, re.IGNORECASE)
        if match:
            tag = match.group(0)
            if hasattr(video_graph, 'reverse_character_mappings'):
                return video_graph.reverse_character_mappings.get(tag)
        
        return None
    
    def clear_cache(self):
        """清除缓存"""
        cache.clear_all()
    
    @property
    def mode_name(self) -> str:
        """当前模式名称"""
        return self.mode


def create_retriever(
    mode: str = "baseline",
    **kwargs
) -> HybridRetriever:
    """
    工厂函数：创建 HybridRetriever 实例
    
    Args:
        mode: "baseline", "nstf_full", "ablation_prototype", "ablation_structure"
        **kwargs: 传递给配置的参数
        
    Returns:
        HybridRetriever 实例
    """
    baseline_config = BaselineConfig(
        threshold=kwargs.get('threshold_baseline', 0.3),
        topk=kwargs.get('topk', 10),
    )
    
    nstf_config = NSTFConfig(
        threshold=kwargs.get('threshold', 0.40),
        min_confidence=kwargs.get('min_confidence', 0.35),
        max_procedures=kwargs.get('max_procedures', 3),
        topk_baseline=kwargs.get('topk', 10),
        threshold_baseline=kwargs.get('threshold_baseline', 0.3),
        use_reranking=kwargs.get('use_reranking', True),
        use_dag_paths=kwargs.get('use_dag_paths', True),
        factual_hybrid=kwargs.get('factual_hybrid', True),
    )
    
    return HybridRetriever(
        mode=mode,
        baseline_config=baseline_config,
        nstf_config=nstf_config,
    )
