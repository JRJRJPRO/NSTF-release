# -*- coding: utf-8 -*-
"""
DAG 融合模块

实现论文中描述的程序融合算法:
1. 节点对齐 (Node Alignment): 通过 embedding 相似度 + 最优二部匹配
2. 参数池化 (Parameter Pooling): 贝叶斯方式合并转移概率
3. 边保留 (Edge Preservation): 保留所有观测到的替代路径

参考论文: TWCS-KDD-25 Section 3.2 (SK-Gen Algorithm)
- Definition 3.3 (Symbolic Structure Fusion)
- Theorem 3.3 (Path Preservation)
- Theorem 3.4 (Transition Probability Convergence)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from scipy.optimize import linear_sum_assignment

from .utils import get_normalized_embedding, batch_get_normalized_embeddings, cosine_similarity


class DAGFusion:
    """DAG 融合器 - 实现论文中的 Symbolic Structure Fusion"""
    
    def __init__(
        self,
        similarity_threshold: float = 0.75,  # 节点对齐的相似度阈值
        ema_alpha: float = 0.3,  # EMA 更新权重 (用于增量更新)
        min_probability: float = 0.01,  # 最小边概率
        debug: bool = False,
    ):
        """
        Args:
            similarity_threshold: 两个 step 被认为"相似"的最低 cosine similarity
            ema_alpha: 增量更新时的 EMA 权重 (alpha * new + (1-alpha) * old)
            min_probability: 边概率的下限，避免概率为0
            debug: 是否输出调试信息
        """
        self.similarity_threshold = similarity_threshold
        self.ema_alpha = ema_alpha
        self.min_probability = min_probability
        self.debug = debug
    
    def should_fuse(self, proc1: Dict, proc2: Dict, goal_threshold: float = 0.80) -> bool:
        """
        判断两个 procedure 是否应该融合
        
        基于 goal embedding 的相似度判断
        
        Args:
            proc1, proc2: 两个 procedure 节点
            goal_threshold: goal 相似度阈值
        
        Returns:
            是否应该融合
        """
        # 获取 goal embeddings
        emb1 = self._get_goal_embedding(proc1)
        emb2 = self._get_goal_embedding(proc2)
        
        if emb1 is None or emb2 is None:
            # 无法获取 embedding，使用文本匹配
            goal1 = proc1.get('goal', '')
            goal2 = proc2.get('goal', '')
            return goal1.lower().strip() == goal2.lower().strip()
        
        similarity = cosine_similarity(emb1, emb2)
        
        if self.debug:
            print(f"    Goal similarity: {similarity:.3f} (threshold: {goal_threshold})")
        
        return similarity >= goal_threshold
    
    def _get_goal_embedding(self, proc: Dict) -> Optional[np.ndarray]:
        """获取 procedure 的 goal embedding"""
        # 尝试从预计算的 embeddings 中获取
        embeddings = proc.get('embeddings', {})
        if 'goal_emb' in embeddings:
            emb = embeddings['goal_emb']
            if isinstance(emb, np.ndarray):
                return emb
            return np.array(emb)
        
        # 否则计算
        goal = proc.get('goal', '')
        if goal:
            return get_normalized_embedding(goal)
        return None
    
    def fuse(self, proc1: Dict, proc2: Dict, observation_counts: Dict[str, int] = None) -> Dict:
        """
        融合两个 procedure
        
        实现论文 Definition 3.3 (Symbolic Structure Fusion):
        给定两个 NS-Nodes n_i = (id_i, c_i, p_i, S_i, F) 和 n_j = (id_j, c_j, p_j, S_j, F)
        融合操作 Fuse(n_i, n_j) 产生新节点 n_fused = (id_new, c_merged, p_merged, S_merged, F)
        
        包含三个子操作:
        1. Node Alignment: 使用 Hungarian algorithm 对齐步骤
        2. Parameter Pooling: 贝叶斯方式合并属性
        3. Edge Preservation: 保留所有观测到的路径
        
        Args:
            proc1: 第一个 procedure (作为基准)
            proc2: 第二个 procedure (待合并)
            observation_counts: 每个边的观测次数 {edge_key: count}
        
        Returns:
            融合后的 procedure
        """
        if observation_counts is None:
            observation_counts = {}
        
        if self.debug:
            print(f"  Fusing procedures:")
            print(f"    Proc1: {proc1.get('goal', 'N/A')[:50]}")
            print(f"    Proc2: {proc2.get('goal', 'N/A')[:50]}")
        
        # Step 1: Node Alignment (步骤对齐)
        alignment = self._align_steps(
            proc1.get('steps', []),
            proc2.get('steps', [])
        )
        
        if self.debug:
            print(f"    Alignment: {len(alignment['matched'])} matched, "
                  f"{len(alignment['only_proc1'])} only in proc1, "
                  f"{len(alignment['only_proc2'])} only in proc2")
        
        # Step 2: Merge Steps (合并步骤)
        merged_steps, step_id_mapping = self._merge_steps(
            proc1.get('steps', []),
            proc2.get('steps', []),
            alignment
        )
        
        # Step 3: Merge Edges with Probability Pooling (合并边并池化概率)
        merged_edges = self._merge_edges(
            proc1.get('edges', []),
            proc2.get('edges', []),
            step_id_mapping,
            observation_counts
        )
        
        # Step 4: Merge Episodic Links (合并事件链接)
        merged_links = self._merge_episodic_links(
            proc1.get('episodic_links', []),
            proc2.get('episodic_links', [])
        )
        
        # Step 5: Merge Goal Embedding (EMA 方式)
        merged_embedding = self._merge_embeddings(proc1, proc2)
        
        # Step 6: Merge Metadata
        merged_metadata = self._merge_metadata(proc1, proc2)
        
        # 构建融合后的 procedure
        fused_proc = {
            'proc_id': proc1.get('proc_id', 'fused_proc'),  # 保留第一个的 ID
            'type': 'procedure',
            'goal': self._merge_goals(proc1.get('goal', ''), proc2.get('goal', '')),
            'description': self._merge_descriptions(
                proc1.get('description', ''),
                proc2.get('description', '')
            ),
            'steps': merged_steps,
            'edges': merged_edges,
            'episodic_links': merged_links,
            'embeddings': {
                'goal_emb': merged_embedding
            },
            'metadata': merged_metadata,
            # 融合统计
            'fusion_info': {
                'source_procs': [proc1.get('proc_id'), proc2.get('proc_id')],
                'num_matched_steps': len(alignment['matched']),
                'num_new_steps': len(alignment['only_proc2']),
                'total_steps': len(merged_steps),
                'total_edges': len(merged_edges),
            }
        }
        
        if self.debug:
            print(f"    Fused result: {len(merged_steps)} steps, {len(merged_edges)} edges")
        
        return fused_proc
    
    def _align_steps(
        self,
        steps1: List[Dict],
        steps2: List[Dict]
    ) -> Dict[str, List]:
        """
        步骤对齐 - 使用 Hungarian Algorithm 最优二部匹配
        
        根据 action 的 embedding 相似度构建代价矩阵，
        然后使用 Hungarian algorithm 找到最优匹配
        
        Returns:
            {
                'matched': [(idx1, idx2, similarity), ...],  # 匹配的步骤对
                'only_proc1': [idx1, ...],  # 仅在 proc1 中的步骤
                'only_proc2': [idx2, ...],  # 仅在 proc2 中的步骤
            }
        """
        if not steps1 or not steps2:
            return {
                'matched': [],
                'only_proc1': list(range(len(steps1))),
                'only_proc2': list(range(len(steps2))),
            }
        
        # 提取 action 文本
        actions1 = [self._get_step_action(s) for s in steps1]
        actions2 = [self._get_step_action(s) for s in steps2]
        
        # 批量计算 embeddings
        all_actions = actions1 + actions2
        all_embeddings = batch_get_normalized_embeddings(all_actions)
        
        emb1 = all_embeddings[:len(actions1)]
        emb2 = all_embeddings[len(actions1):]
        
        # 构建相似度矩阵
        n1, n2 = len(steps1), len(steps2)
        similarity_matrix = np.zeros((n1, n2))
        
        for i in range(n1):
            for j in range(n2):
                similarity_matrix[i, j] = cosine_similarity(emb1[i], emb2[j])
        
        # 转换为代价矩阵 (Hungarian 最小化代价)
        cost_matrix = 1.0 - similarity_matrix
        
        # Hungarian Algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # 筛选有效匹配 (相似度 >= 阈值)
        matched = []
        matched_i = set()
        matched_j = set()
        
        for i, j in zip(row_ind, col_ind):
            sim = similarity_matrix[i, j]
            if sim >= self.similarity_threshold:
                matched.append((i, j, sim))
                matched_i.add(i)
                matched_j.add(j)
        
        # 未匹配的步骤
        only_proc1 = [i for i in range(n1) if i not in matched_i]
        only_proc2 = [j for j in range(n2) if j not in matched_j]
        
        return {
            'matched': matched,
            'only_proc1': only_proc1,
            'only_proc2': only_proc2,
        }
    
    def _get_step_action(self, step: Dict) -> str:
        """获取 step 的 action 文本"""
        if isinstance(step, dict):
            action = step.get('action', '')
            if isinstance(action, str):
                return action
            return str(action)
        return str(step)
    
    def _merge_steps(
        self,
        steps1: List[Dict],
        steps2: List[Dict],
        alignment: Dict
    ) -> Tuple[List[Dict], Dict[str, str]]:
        """
        合并步骤列表
        
        对于匹配的步骤: 合并属性 (取更高的 success_rate, 平均 duration)
        对于未匹配的步骤: 添加到结果中
        
        Returns:
            (merged_steps, step_id_mapping)
            step_id_mapping: {old_step_id: new_step_id} 用于边的重映射
        """
        merged_steps = []
        step_id_mapping = {}  # 用于映射旧 step_id 到新 step_id
        
        # 处理匹配的步骤对
        for idx1, idx2, sim in alignment['matched']:
            s1 = steps1[idx1] if idx1 < len(steps1) else {}
            s2 = steps2[idx2] if idx2 < len(steps2) else {}
            
            merged_step = self._merge_single_step(s1, s2, sim)
            new_step_id = merged_step.get('step_id', f'step_{len(merged_steps)+1}')
            
            # 记录映射
            old_id1 = s1.get('step_id', f'step_{idx1+1}')
            old_id2 = s2.get('step_id', f'step_{idx2+1}')
            step_id_mapping[f'proc1_{old_id1}'] = new_step_id
            step_id_mapping[f'proc2_{old_id2}'] = new_step_id
            
            merged_steps.append(merged_step)
        
        # 处理仅在 proc1 中的步骤
        for idx in alignment['only_proc1']:
            if idx < len(steps1):
                step = steps1[idx].copy() if isinstance(steps1[idx], dict) else {'action': str(steps1[idx])}
                old_id = step.get('step_id', f'step_{idx+1}')
                new_id = f'step_{len(merged_steps)+1}'
                step['step_id'] = new_id
                step_id_mapping[f'proc1_{old_id}'] = new_id
                merged_steps.append(step)
        
        # 处理仅在 proc2 中的步骤 (添加为新步骤)
        for idx in alignment['only_proc2']:
            if idx < len(steps2):
                step = steps2[idx].copy() if isinstance(steps2[idx], dict) else {'action': str(steps2[idx])}
                old_id = step.get('step_id', f'step_{idx+1}')
                new_id = f'step_{len(merged_steps)+1}'
                step['step_id'] = new_id
                step_id_mapping[f'proc2_{old_id}'] = new_id
                merged_steps.append(step)
        
        return merged_steps, step_id_mapping
    
    def _merge_single_step(self, s1: Dict, s2: Dict, similarity: float) -> Dict:
        """
        合并单个步骤的属性
        
        采用论文中的 Parameter Pooling 策略:
        - action: 保留第一个的 (或取更长的)
        - duration_seconds: 取平均值
        - success_rate: 取加权平均 (基于观测次数，如果有的话)
        - triggers/outcomes: 合并去重
        """
        # 合并 action (保留更详细的)
        action1 = s1.get('action', '')
        action2 = s2.get('action', '')
        merged_action = action1 if len(action1) >= len(action2) else action2
        
        # 合并 duration (平均)
        dur1 = s1.get('duration_seconds', 30)
        dur2 = s2.get('duration_seconds', 30)
        merged_duration = (dur1 + dur2) / 2
        
        # 合并 success_rate (加权平均，假设等权)
        sr1 = s1.get('success_rate', 0.9)
        sr2 = s2.get('success_rate', 0.9)
        merged_success_rate = (sr1 + sr2) / 2
        
        # 合并 triggers (去重)
        triggers1 = s1.get('triggers', [])
        triggers2 = s2.get('triggers', [])
        merged_triggers = list(set(triggers1) | set(triggers2))
        
        # 合并 outcomes (去重)
        outcomes1 = s1.get('outcomes', [])
        outcomes2 = s2.get('outcomes', [])
        merged_outcomes = list(set(outcomes1) | set(outcomes2))
        
        return {
            'step_id': s1.get('step_id', 'step_1'),  # 保留第一个的 ID
            'action': merged_action,
            'triggers': merged_triggers,
            'outcomes': merged_outcomes,
            'duration_seconds': merged_duration,
            'success_rate': merged_success_rate,
            'merge_similarity': similarity,  # 记录合并时的相似度
        }
    
    def _merge_edges(
        self,
        edges1: List[Dict],
        edges2: List[Dict],
        step_id_mapping: Dict[str, str],
        observation_counts: Dict[str, int]
    ) -> List[Dict]:
        """
        合并边并更新转移概率
        
        实现论文 Theorem 3.4 (Transition Probability Convergence):
        使用贝叶斯方式更新边的转移概率
        
        核心思想:
        - 相同的边: 根据观测次数加权合并概率
        - 新的边: 直接添加 (保留替代路径)
        """
        # 收集所有边 (重映射 step_id)
        edge_dict = {}  # {(from_step, to_step): edge_info}
        
        # 处理 proc1 的边
        for edge in edges1:
            from_step = edge.get('from_step', '')
            to_step = edge.get('to_step', '')
            
            # 重映射
            new_from = step_id_mapping.get(f'proc1_{from_step}', from_step)
            new_to = step_id_mapping.get(f'proc1_{to_step}', to_step)
            
            key = (new_from, new_to)
            if key not in edge_dict:
                edge_dict[key] = {
                    'from_step': new_from,
                    'to_step': new_to,
                    'probabilities': [],
                    'conditions': set(),
                    'observation_count': 0,
                }
            
            prob = edge.get('probability', 1.0)
            edge_dict[key]['probabilities'].append(prob)
            edge_dict[key]['observation_count'] += observation_counts.get(f'proc1_{from_step}_{to_step}', 1)
            
            cond = edge.get('condition', '')
            if cond:
                edge_dict[key]['conditions'].add(cond)
        
        # 处理 proc2 的边
        for edge in edges2:
            from_step = edge.get('from_step', '')
            to_step = edge.get('to_step', '')
            
            # 重映射
            new_from = step_id_mapping.get(f'proc2_{from_step}', from_step)
            new_to = step_id_mapping.get(f'proc2_{to_step}', to_step)
            
            key = (new_from, new_to)
            if key not in edge_dict:
                edge_dict[key] = {
                    'from_step': new_from,
                    'to_step': new_to,
                    'probabilities': [],
                    'conditions': set(),
                    'observation_count': 0,
                }
            
            prob = edge.get('probability', 1.0)
            edge_dict[key]['probabilities'].append(prob)
            edge_dict[key]['observation_count'] += observation_counts.get(f'proc2_{from_step}_{to_step}', 1)
            
            cond = edge.get('condition', '')
            if cond:
                edge_dict[key]['conditions'].add(cond)
        
        # 计算最终概率 (基于观测次数加权)
        merged_edges = []
        for key, info in edge_dict.items():
            probs = info['probabilities']
            obs_count = max(info['observation_count'], 1)
            
            # 贝叶斯方式: 使用观测次数作为权重
            # 简化实现: 取平均，然后根据观测次数调整置信度
            avg_prob = sum(probs) / len(probs) if probs else 1.0
            
            # 确保概率在合理范围内
            final_prob = max(self.min_probability, min(1.0, avg_prob))
            
            # 合并 conditions
            conditions = list(info['conditions'])
            condition_str = ' OR '.join(conditions) if conditions else ''
            
            merged_edges.append({
                'from_step': info['from_step'],
                'to_step': info['to_step'],
                'probability': final_prob,
                'condition': condition_str,
                'observation_count': obs_count,  # 保留观测次数用于后续更新
            })
        
        return merged_edges
    
    def _merge_episodic_links(
        self,
        links1: List[Dict],
        links2: List[Dict]
    ) -> List[Dict]:
        """合并事件链接 (去重)"""
        seen_clips = set()
        merged = []
        
        for link in links1 + links2:
            clip_id = link.get('clip_id')
            if clip_id is not None and clip_id not in seen_clips:
                seen_clips.add(clip_id)
                merged.append(link)
        
        # 按 clip_id 排序
        merged.sort(key=lambda x: x.get('clip_id', 0))
        return merged
    
    def _merge_embeddings(self, proc1: Dict, proc2: Dict) -> np.ndarray:
        """
        合并 goal embeddings
        
        使用 EMA (Exponential Moving Average) 方式:
        merged = alpha * proc2_emb + (1 - alpha) * proc1_emb
        
        这实现了论文中的 Memory Prototype 增量更新
        """
        emb1 = self._get_goal_embedding(proc1)
        emb2 = self._get_goal_embedding(proc2)
        
        if emb1 is None and emb2 is None:
            # 都没有，重新计算
            goal = proc1.get('goal', '') or proc2.get('goal', '')
            return get_normalized_embedding(goal) if goal else np.zeros(3072)
        
        if emb1 is None:
            return emb2
        if emb2 is None:
            return emb1
        
        # EMA 更新
        merged = self.ema_alpha * emb2 + (1 - self.ema_alpha) * emb1
        
        # 重新归一化
        merged = merged / (np.linalg.norm(merged) + 1e-8)
        
        return merged
    
    def _merge_goals(self, goal1: str, goal2: str) -> str:
        """合并 goal 描述 (保留更长/更详细的)"""
        if not goal1:
            return goal2
        if not goal2:
            return goal1
        
        # 保留更长的描述
        return goal1 if len(goal1) >= len(goal2) else goal2
    
    def _merge_descriptions(self, desc1: str, desc2: str) -> str:
        """合并 description"""
        if not desc1:
            return desc2
        if not desc2:
            return desc1
        
        # 如果差别不大，保留第一个
        if desc1.lower().strip() == desc2.lower().strip():
            return desc1
        
        # 否则合并
        return f"{desc1} | {desc2}"
    
    def _merge_metadata(self, proc1: Dict, proc2: Dict) -> Dict:
        """合并 metadata"""
        meta1 = proc1.get('metadata', {})
        meta2 = proc2.get('metadata', {})
        
        from datetime import datetime
        
        return {
            'created_at': meta1.get('created_at', datetime.now().isoformat()),
            'last_updated': datetime.now().isoformat(),
            'source': 'nstf_fusion',
            'original_sources': [
                meta1.get('source', 'unknown'),
                meta2.get('source', 'unknown'),
            ],
            'fusion_count': meta1.get('fusion_count', 0) + 1,
        }


class ProcedureFusionManager:
    """
    程序融合管理器
    
    管理多个 procedure 的融合，包括:
    1. 识别可融合的 procedure 对
    2. 执行融合操作
    3. 维护融合后的图谱
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.80,  # 判断是否融合的 goal 相似度阈值
        step_align_threshold: float = 0.75,  # 步骤对齐的相似度阈值
        debug: bool = False,
    ):
        self.similarity_threshold = similarity_threshold
        self.dag_fusion = DAGFusion(
            similarity_threshold=step_align_threshold,
            debug=debug,
        )
        self.debug = debug
        
        # 统计
        self.stats = {
            'procedures_before': 0,
            'procedures_after': 0,
            'total_fusions': 0,
        }
    
    def fuse_all(self, procedure_nodes: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        融合所有相似的 procedure
        
        使用贪心策略:
        1. 计算所有 procedure 对的 goal 相似度
        2. 按相似度降序排序
        3. 贪心地融合相似度最高的对
        
        Args:
            procedure_nodes: {proc_id: procedure_dict}
        
        Returns:
            融合后的 procedure_nodes
        """
        if not procedure_nodes or len(procedure_nodes) < 2:
            return procedure_nodes
        
        self.stats['procedures_before'] = len(procedure_nodes)
        
        # 转换为列表便于处理
        procs = list(procedure_nodes.values())
        proc_ids = list(procedure_nodes.keys())
        
        if self.debug:
            print(f"\n=== Procedure Fusion ===")
            print(f"Input: {len(procs)} procedures")
        
        # 计算所有 goal embeddings
        goals = [p.get('goal', '') for p in procs]
        goal_embeddings = batch_get_normalized_embeddings(goals)
        
        # 计算相似度矩阵
        n = len(procs)
        similarity_pairs = []
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = cosine_similarity(goal_embeddings[i], goal_embeddings[j])
                if sim >= self.similarity_threshold:
                    similarity_pairs.append((i, j, sim))
        
        # 按相似度降序排序
        similarity_pairs.sort(key=lambda x: -x[2])
        
        if self.debug:
            print(f"Found {len(similarity_pairs)} similar pairs (threshold: {self.similarity_threshold})")
        
        # 贪心融合
        fused_indices = set()  # 已被融合的 procedure 索引
        fused_procs = []  # 融合结果
        
        for i, j, sim in similarity_pairs:
            if i in fused_indices or j in fused_indices:
                continue
            
            if self.debug:
                print(f"  Fusing {proc_ids[i]} + {proc_ids[j]} (sim: {sim:.3f})")
            
            # 执行融合
            fused = self.dag_fusion.fuse(procs[i], procs[j])
            fused_procs.append(fused)
            fused_indices.add(i)
            fused_indices.add(j)
            self.stats['total_fusions'] += 1
        
        # 添加未融合的 procedure
        for i, proc in enumerate(procs):
            if i not in fused_indices:
                fused_procs.append(proc)
        
        # 重建 procedure_nodes dict
        result = {}
        for i, proc in enumerate(fused_procs):
            proc_id = proc.get('proc_id', f'proc_{i+1}')
            result[proc_id] = proc
        
        self.stats['procedures_after'] = len(result)
        
        if self.debug:
            print(f"Output: {len(result)} procedures")
            print(f"Fusions performed: {self.stats['total_fusions']}")
        
        return result
    
    def incremental_fuse(
        self,
        existing_procs: Dict[str, Dict],
        new_proc: Dict
    ) -> Tuple[Dict[str, Dict], bool]:
        """
        增量融合 - 将新 procedure 融合到现有图谱
        
        用于实时/流式更新场景
        
        Args:
            existing_procs: 现有的 procedure_nodes
            new_proc: 新的 procedure
        
        Returns:
            (updated_procs, was_fused)
            was_fused: 是否发生了融合 (False 表示直接添加)
        """
        if not existing_procs:
            new_id = new_proc.get('proc_id', 'proc_1')
            return {new_id: new_proc}, False
        
        # 找到最相似的现有 procedure
        new_goal = new_proc.get('goal', '')
        new_emb = get_normalized_embedding(new_goal) if new_goal else None
        
        if new_emb is None:
            # 无法计算 embedding，直接添加
            new_id = new_proc.get('proc_id', f'proc_{len(existing_procs)+1}')
            result = existing_procs.copy()
            result[new_id] = new_proc
            return result, False
        
        best_match_id = None
        best_match_sim = 0.0
        
        for proc_id, proc in existing_procs.items():
            proc_emb = self.dag_fusion._get_goal_embedding(proc)
            if proc_emb is not None:
                sim = cosine_similarity(new_emb, proc_emb)
                if sim > best_match_sim:
                    best_match_sim = sim
                    best_match_id = proc_id
        
        if self.debug:
            print(f"  Best match: {best_match_id} (sim: {best_match_sim:.3f})")
        
        result = existing_procs.copy()
        
        if best_match_sim >= self.similarity_threshold and best_match_id:
            # 融合
            fused = self.dag_fusion.fuse(existing_procs[best_match_id], new_proc)
            fused['proc_id'] = best_match_id  # 保持原 ID
            result[best_match_id] = fused
            self.stats['total_fusions'] += 1
            return result, True
        else:
            # 直接添加
            new_id = new_proc.get('proc_id', f'proc_{len(existing_procs)+1}')
            result[new_id] = new_proc
            return result, False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
