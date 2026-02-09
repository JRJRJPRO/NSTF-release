# -*- coding: utf-8 -*-
"""
IncrementalNSTFBuilder - 增量 NSTF 构建器

主实验方案，支持 Procedure 更新/融合

核心逻辑:
1. 逐 clip 处理
2. 检测当前 clip 是否包含程序性知识
3. 用 ProcedureMatcher 判断是否与已有 Procedure 匹配
4. 匹配则合并（增加 episodic_links），否则创建新 Procedure

优势:
- 多个 clips 的相似程序性知识融合到一个 Procedure
- 检索时只需匹配一个 Procedure 就能获得更多证据
- 减少冗余，提高检索效率
"""

import os
import sys
import json
import pickle
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

# 统一环境设置
from env_setup import setup_all, NSTF_MODEL_DIR
setup_all()

from .extractor import ProcedureExtractor
from .character_resolver import CharacterResolver
from .episodic_linker import EpisodicLinker
from .procedure_matcher import ProcedureMatcher
from .dag_fusion import DAGFusion, ProcedureFusionManager
from .utils import get_normalized_embedding, batch_get_normalized_embeddings, cosine_similarity


class IncrementalNSTFBuilder:
    """增量 NSTF 构建器"""
    
    def __init__(
        self,
        data_dir: str = None,
        output_dir: str = None,
        config_path: str = None,
        debug: bool = False,
    ):
        """
        Args:
            data_dir: 数据目录，默认 NSTF_MODEL/data
            output_dir: 输出目录，默认 data/nstf_graphs
            config_path: 配置文件路径
            debug: 是否输出调试信息
        """
        # 路径
        self.module_dir = Path(__file__).parent
        self.nstf_model_dir = self.module_dir.parent
        
        self.data_dir = Path(data_dir) if data_dir else self.nstf_model_dir / 'data'
        self.output_dir = Path(output_dir) if output_dir else self.data_dir / 'nstf_graphs'
        
        self.debug = debug
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 提取器（用于单 clip 检测）
        self.extractor = ProcedureExtractor(
            llm_model=self.config.get('llm_model', 'gemini-2.5-flash'),
            batch_size=1,  # 增量模式每次处理一个 clip
            max_content_chars=self.config.get('max_content_chars', 150),
            api_delay=self.config.get('api_delay_seconds', 1),
        )
        
        # 匹配器（判断是否合并）
        self.matcher = ProcedureMatcher(
            match_threshold=self.config.get('match_threshold', 0.70),
            debug=debug,
        )
        
        # 链接器（用于更新 episodic_links）
        self.linker = EpisodicLinker(
            verify_threshold=self.config.get('verify_threshold', 0.35),
            discover_threshold=self.config.get('discover_threshold', 0.35),
            max_links_per_proc=self.config.get('max_links_per_proc', 10),
            debug=debug,
        )
        
        # DAG 融合管理器
        self.fusion_manager = ProcedureFusionManager(
            similarity_threshold=self.config.get('fusion_similarity_threshold', 0.80),
            step_align_threshold=self.config.get('step_align_threshold', 0.75),
            debug=debug,
        )
        
        # Character 解析器（每次 build 时初始化）
        self.character_resolver: Optional[CharacterResolver] = None
        
        # Embedding 模型
        self.embedding_model = self.config.get('embedding_model', 'text-embedding-3-large')
        self._embedding_api = None
        
        # 统计
        self.stats = {
            'videos_processed': 0,
            'clips_processed': 0,
            'procedures_created': 0,
            'procedures_merged': 0,
        }
    
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置"""
        if config_path is None:
            config_path = self.module_dir / 'config' / 'default.json'
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @property
    def embedding_api(self):
        if self._embedding_api is None:
            from mmagent.utils.chat_api import get_embedding_with_retry
            self._embedding_api = get_embedding_with_retry
        return self._embedding_api
    
    def load_baseline_graph(self, video_name: str, dataset: str):
        """加载 baseline 图谱"""
        graph_path = self.data_dir / 'memory_graphs' / dataset / f'{video_name}.pkl'
        if not graph_path.exists():
            return None
        with open(graph_path, 'rb') as f:
            return pickle.load(f)
    
    def get_sorted_clips(self, graph) -> List[int]:
        """获取按时间排序的 clip IDs"""
        if hasattr(graph, 'text_nodes_by_clip'):
            return sorted(graph.text_nodes_by_clip.keys())
        return []
    
    def get_clip_content(self, graph, clip_id: int) -> Dict:
        """获取单个 clip 的内容"""
        if not hasattr(graph, 'text_nodes_by_clip'):
            return {'clip_id': clip_id, 'content': '', 'raw_content': ''}
        
        node_ids = graph.text_nodes_by_clip.get(clip_id, [])
        clip_texts = []
        
        for nid in node_ids:
            node = graph.nodes.get(nid)
            if node and hasattr(node, 'metadata'):
                contents = node.metadata.get('contents', [])
                clip_texts.extend(contents)
        
        combined = ' '.join(clip_texts)
        
        # 应用 Character 解析
        if self.character_resolver:
            resolved = self.character_resolver.resolve(combined)
        else:
            resolved = combined
        
        return {
            'clip_id': clip_id,
            'content': resolved,
            'raw_content': combined
        }
    
    def create_procedure_node(
        self, 
        detected: Dict, 
        clip_id: int, 
        clip_content: Dict,
        proc_id: str
    ) -> Dict:
        """
        创建新的 Procedure 节点（V2.3 符合论文规范）
        
        包含:
        - 双层 Index Vectors (goal_emb, step_emb)
        - 完整 DAG 结构 (START/GOAL 节点)
        - 具体的 objects, locations, participants
        """
        import numpy as np
        
        goal = detected.get('goal', '')
        if isinstance(goal, dict):
            goal = goal.get('name', str(goal))
        goal = str(goal)
        
        description = detected.get('description', '')
        
        # V2.3.2: 验证并规范化 proc_type（必须是单一有效值）
        raw_proc_type = detected.get('type', 'task')
        VALID_PROC_TYPES = {'task', 'habit', 'trait', 'social'}
        if isinstance(raw_proc_type, str) and '|' in raw_proc_type:
            # 处理 "task|social" 这样的无效组合，取第一个有效值
            parts = raw_proc_type.split('|')
            proc_type = next((p.strip() for p in parts if p.strip() in VALID_PROC_TYPES), 'task')
        elif raw_proc_type in VALID_PROC_TYPES:
            proc_type = raw_proc_type
        else:
            proc_type = 'task'  # 默认值
        
        raw_steps = detected.get('steps', [])
        edges = detected.get('edges', [])
        
        # 规范化 steps 结构，确保包含 README 要求的所有字段
        steps = []
        for i, s in enumerate(raw_steps):
            if isinstance(s, dict):
                step = {
                    'step_id': s.get('step_id', f'step_{i+1}'),
                    'action': s.get('action', ''),
                    'object': s.get('object', ''),
                    'location': s.get('location', ''),
                    'actor': s.get('actor', ''),
                    'triggers': s.get('triggers', []),
                    'outcomes': s.get('outcomes', []),
                    'duration_seconds': s.get('duration_seconds', 0)
                }
                steps.append(step)
            elif isinstance(s, str) and s:
                steps.append({
                    'step_id': f'step_{i+1}',
                    'action': s,
                    'object': '',
                    'location': '',
                    'actor': '',
                    'triggers': [],
                    'outcomes': [],
                    'duration_seconds': 0
                })
        
        # V2.3: 提取具体的物品、位置、参与者
        objects = detected.get('objects', detected.get('key_objects', []))
        locations = detected.get('locations', detected.get('key_locations', []))
        participants = detected.get('participants', [])
        
        # ========== 双层 Index Vectors ==========
        # 1. goal_emb: φ(goal) - 包含具体物品和位置
        goal_text = f"{goal}. {description}" if description else goal
        # 添加物品和位置到 embedding 文本以提高检索精度
        if objects:
            goal_text += f" Objects: {', '.join(objects[:5])}"
        if locations:
            goal_text += f" Locations: {', '.join(locations[:5])}"
        goal_emb = get_normalized_embedding(goal_text)
        
        # 2. step_emb: Mean(φ(s) for s in steps)
        step_actions = []
        for s in steps:
            if isinstance(s, dict):
                action = s.get('action', '')
                if action:
                    # 包含 object 和 location 以提高精度
                    full_action = action
                    if s.get('object'):
                        full_action += f" with {s['object']}"
                    if s.get('location'):
                        full_action += f" at {s['location']}"
                    step_actions.append(full_action)
            elif isinstance(s, str) and s:
                step_actions.append(s)
        
        if step_actions:
            step_embs = batch_get_normalized_embeddings(step_actions)
            step_emb = np.mean(step_embs, axis=0)
            step_emb = step_emb / (np.linalg.norm(step_emb) + 1e-8)
        else:
            step_emb = goal_emb.copy()
        
        # ========== 构建完整 DAG ==========
        dag = self._construct_dag(steps, edges)
        
        return {
            'proc_id': proc_id,
            'type': 'procedure',
            'goal': goal,
            'description': description,
            'proc_type': proc_type,
            'steps': steps,
            'edges': edges,
            'dag': dag,  # 完整 DAG 结构
            # V2.3: 新增具体信息字段
            'objects': objects,
            'locations': locations,
            'participants': participants,
            'episodic_links': [{
                'clip_id': clip_id,
                'relevance': 'source',
                'similarity': 1.0,
                'content_preview': clip_content['content'][:100]
            }],
            'embeddings': {
                'goal_emb': goal_emb,   # 论文: i_goal = φ(c)
                'step_emb': step_emb,   # 论文: i_step = Mean(φ(s))
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'source': 'incremental_nstf',
                'observation_count': 1,
                'source_clips': [clip_id],
                'version': '2.3.2'  # V2.3.2: 完整字段规范
            }
        }
    
    def _construct_dag(self, steps: list, edges: list) -> Dict:
        """构建完整的 Procedural DAG（含 START/GOAL）"""
        nodes = {
            'START': {'type': 'control', 'attributes': {}},
            'GOAL': {'type': 'control', 'attributes': {}}
        }
        
        step_ids = []
        for i, s in enumerate(steps):
            if isinstance(s, dict):
                step_id = s.get('step_id', f'step_{i+1}')
                # 构建 attributes 包含所有额外信息
                attributes = {
                    'object': s.get('object', ''),
                    'location': s.get('location', ''),
                    'actor': s.get('actor', ''),
                    'triggers': s.get('triggers', []),
                    'outcomes': s.get('outcomes', []),
                    'duration_seconds': s.get('duration_seconds', 0)
                }
                nodes[step_id] = {
                    'type': 'action',
                    'action': s.get('action', ''),
                    'attributes': attributes
                }
                step_ids.append(step_id)
            elif isinstance(s, str):
                step_id = f'step_{i+1}'
                nodes[step_id] = {
                    'type': 'action',
                    'action': s,
                    'attributes': {'object': '', 'location': '', 'actor': '', 'triggers': [], 'outcomes': [], 'duration_seconds': 0}
                }
                step_ids.append(step_id)
        
        # 构建边
        dag_edges = []
        if edges:
            for e in edges:
                dag_edges.append({
                    'from': e.get('from_step', e.get('from', '')),
                    'to': e.get('to_step', e.get('to', '')),
                    'count': e.get('count', 1),
                    'probability': e.get('probability', 1.0),
                    'condition': e.get('condition', None)
                })
        elif step_ids:
            # 自动构建线性 DAG
            dag_edges.append({'from': 'START', 'to': step_ids[0], 'count': 1, 'probability': 1.0, 'condition': None})
            for i in range(len(step_ids) - 1):
                dag_edges.append({'from': step_ids[i], 'to': step_ids[i+1], 'count': 1, 'probability': 1.0, 'condition': None})
            dag_edges.append({'from': step_ids[-1], 'to': 'GOAL', 'count': 1, 'probability': 1.0, 'condition': None})
        
        return {'nodes': nodes, 'edges': dag_edges}
    
    def update_procedure(
        self, 
        proc: Dict, 
        clip_id: int, 
        clip_content: Dict,
        detected: Dict
    ):
        """
        更新已有 Procedure（带锚点约束 EMA）
        
        论文规范:
        - EMA 更新 Index Vectors
        - 锚点约束防止语义漂移
        - 更新 DAG 转移计数
        """
        # 使用锚点约束 EMA 更新
        self.update_with_anchored_ema(
            proc, 
            clip_id, 
            clip_content, 
            detected,
            beta=self.config.get('ema_beta', 0.9),
            drift_threshold=self.config.get('drift_threshold', 0.7),
            anchor_weight=self.config.get('anchor_weight', 0.3),
            update_clip_content=clip_content  # V2.4: 传递 clip_content 用于边计数更新
        )
    
    def update_with_anchored_ema(
        self,
        proc: Dict,
        clip_id: int,
        clip_content: Dict,
        detected: Dict,
        beta: float = 0.9,
        drift_threshold: float = 0.7,
        anchor_weight: float = 0.3,
        update_clip_content: Dict = None  # V2.4: 用于边计数更新
    ):
        """
        带锚点约束的增量更新（论文规范实现）
        
        改进点:
        1. 保留原始 embedding 作为锚点
        2. 监测漂移程度
        3. 超过阈值时拉回锚点方向
        4. V2.4: 基于内容相似度更新边转移计数
        
        Args:
            proc: 要更新的 Procedure
            clip_id: 当前 clip ID
            clip_content: {'clip_id', 'content', 'raw_content'}
            detected: 检测到的程序信息
            beta: EMA 权重（默认 0.9）
            drift_threshold: 允许的最小锚点相似度
            anchor_weight: 漂移时的锚点拉回权重
            update_clip_content: 用于边计数更新的 clip 内容
        """
        import numpy as np
        
        # ========== 1. 获取或创建锚点 ==========
        embeddings = proc.get('embeddings', {})
        
        # goal_emb 锚点
        if 'anchor_goal_emb' not in embeddings:
            if 'goal_emb' in embeddings:
                embeddings['anchor_goal_emb'] = embeddings['goal_emb'].copy()
            else:
                # 首次没有 goal_emb，生成一个
                goal_text = f"{proc.get('goal', '')}. {proc.get('description', '')}"
                embeddings['anchor_goal_emb'] = get_normalized_embedding(goal_text)
                embeddings['goal_emb'] = embeddings['anchor_goal_emb'].copy()
        
        # step_emb 锚点
        if 'anchor_step_emb' not in embeddings and 'step_emb' in embeddings:
            embeddings['anchor_step_emb'] = embeddings['step_emb'].copy()
        
        proc['embeddings'] = embeddings
        
        # ========== 2. 计算新观测的 embedding ==========
        new_content_emb = get_normalized_embedding(clip_content['content'])
        
        # ========== 3. EMA 更新 goal_emb（带锚点约束）==========
        old_goal_emb = embeddings['goal_emb']
        anchor_goal_emb = embeddings['anchor_goal_emb']
        
        # 标准 EMA
        new_goal_emb = beta * old_goal_emb + (1 - beta) * new_content_emb
        new_goal_emb = new_goal_emb / (np.linalg.norm(new_goal_emb) + 1e-8)
        
        # 锚点约束检查
        goal_drift_sim = cosine_similarity(new_goal_emb, anchor_goal_emb)
        
        if goal_drift_sim < drift_threshold:
            # 漂移过大，拉回锚点方向
            if self.debug:
                print(f"    ⚠️ Goal drift detected: sim={goal_drift_sim:.3f} < {drift_threshold}")
            new_goal_emb = anchor_weight * anchor_goal_emb + (1 - anchor_weight) * new_goal_emb
            new_goal_emb = new_goal_emb / (np.linalg.norm(new_goal_emb) + 1e-8)
            
            # 记录漂移事件
            if 'drift_events' not in proc.get('metadata', {}):
                proc['metadata']['drift_events'] = []
            proc['metadata']['drift_events'].append({
                'clip_id': clip_id,
                'type': 'goal',
                'drift_sim': float(goal_drift_sim),
                'corrected': True
            })
        
        embeddings['goal_emb'] = new_goal_emb
        
        # ========== 4. EMA 更新 step_emb（如果有新的 steps）==========
        new_steps = detected.get('steps', [])
        if new_steps and 'step_emb' in embeddings:
            # 提取 step actions
            step_actions = []
            for s in new_steps:
                if isinstance(s, dict):
                    action = s.get('action', '')
                    if action:
                        step_actions.append(action)
                elif isinstance(s, str):
                    step_actions.append(s)
            
            if step_actions:
                new_step_embs = batch_get_normalized_embeddings(step_actions)
                new_step_emb = np.mean(new_step_embs, axis=0)
                new_step_emb = new_step_emb / (np.linalg.norm(new_step_emb) + 1e-8)
                
                old_step_emb = embeddings['step_emb']
                updated_step_emb = beta * old_step_emb + (1 - beta) * new_step_emb
                updated_step_emb = updated_step_emb / (np.linalg.norm(updated_step_emb) + 1e-8)
                
                # 锚点约束
                if 'anchor_step_emb' in embeddings:
                    anchor_step_emb = embeddings['anchor_step_emb']
                    step_drift_sim = cosine_similarity(updated_step_emb, anchor_step_emb)
                    
                    if step_drift_sim < drift_threshold:
                        if self.debug:
                            print(f"    ⚠️ Step drift detected: sim={step_drift_sim:.3f} < {drift_threshold}")
                        updated_step_emb = anchor_weight * anchor_step_emb + (1 - anchor_weight) * updated_step_emb
                        updated_step_emb = updated_step_emb / (np.linalg.norm(updated_step_emb) + 1e-8)
                
                embeddings['step_emb'] = updated_step_emb
        
        # ========== 5. 更新 DAG 转移计数（V2.4 改进：传递 clip_content）==========
        self._update_dag_edge_counts(proc, detected, update_clip_content or clip_content)
        
        # ========== 6. 添加 episodic_link ==========
        similarity = float(np.dot(old_goal_emb, new_content_emb))
        proc['episodic_links'].append({
            'clip_id': clip_id,
            'relevance': 'update',
            'similarity': round(similarity, 4),
            'anchor_similarity': round(float(goal_drift_sim), 4),
            'content_preview': clip_content['content'][:100]
        })
        
        # ========== 7. 更新元数据 ==========
        proc['metadata']['observation_count'] = proc['metadata'].get('observation_count', 0) + 1
        proc['metadata']['updated_at'] = datetime.now().isoformat()
        if 'source_clips' not in proc['metadata']:
            proc['metadata']['source_clips'] = []
        proc['metadata']['source_clips'].append(clip_id)
        
        # 如果新步骤更详细，更新 steps 和 DAG（保持一致性）
        if new_steps and len(new_steps) > len(proc.get('steps', [])):
            # 规范化新步骤
            normalized_steps = []
            for i, s in enumerate(new_steps):
                if isinstance(s, dict):
                    step = {
                        'step_id': s.get('step_id', f'step_{i+1}'),
                        'action': s.get('action', ''),
                        'object': s.get('object', ''),
                        'location': s.get('location', ''),
                        'actor': s.get('actor', ''),
                        'triggers': s.get('triggers', []),
                        'outcomes': s.get('outcomes', []),
                        'duration_seconds': s.get('duration_seconds', 0)
                    }
                    normalized_steps.append(step)
                elif isinstance(s, str) and s:
                    normalized_steps.append({
                        'step_id': f'step_{i+1}',
                        'action': s,
                        'object': '',
                        'location': '',
                        'actor': '',
                        'triggers': [],
                        'outcomes': [],
                        'duration_seconds': 0
                    })
            
            proc['steps'] = normalized_steps
            # 同步重建 DAG 以保持 steps 和 dag.nodes 一致
            new_edges = detected.get('edges', [])
            proc['dag'] = self._construct_dag(normalized_steps, new_edges)
            if self.debug:
                print(f"    Updated steps: {len(normalized_steps)} steps, DAG rebuilt")
    
    def _update_dag_edge_counts(self, proc: Dict, detected: Dict, clip_content: Dict = None):
        """
        更新 DAG 边的转移计数（V2.4 改进版）
        
        论文公式:
        N_ij ← N_ij + 1
        P(v_j|v_i) = N_ij / Σ_k N_ik
        
        改进: 使用内容相似度推断观测到了哪些步骤，然后更新对应边的计数
        """
        dag = proc.get('dag')
        if not dag:
            return
        
        edges = dag.get('edges', [])
        nodes = dag.get('nodes', {})
        if not edges:
            return
        
        # 方法1: 使用 detected 中的 edges（如果有非线性结构）
        new_edges = detected.get('edges', [])
        if new_edges and self._has_branching(new_edges):
            for new_edge in new_edges:
                from_step = new_edge.get('from_step') or new_edge.get('from', '')
                to_step = new_edge.get('to_step') or new_edge.get('to', '')
                self._increment_edge_count(edges, from_step, to_step)
        else:
            # 方法2: 基于内容相似度推断观测到的步骤（V2.4 核心改进）
            observed_steps = self._infer_observed_steps(nodes, detected, clip_content)
            
            if observed_steps:
                # 更新 START -> first_observed
                self._increment_edge_count(edges, 'START', observed_steps[0])
                
                # 更新 observed[i] -> observed[i+1]
                for i in range(len(observed_steps) - 1):
                    self._increment_edge_count(edges, observed_steps[i], observed_steps[i+1])
                
                # 更新 last_observed -> GOAL
                self._increment_edge_count(edges, observed_steps[-1], 'GOAL')
        
        # 重新计算所有边的概率
        self._recompute_edge_probabilities(dag)
    
    def _has_branching(self, edges: List[Dict]) -> bool:
        """检查边列表是否有分支结构（同一源节点有多个目标）"""
        from collections import Counter
        sources = [e.get('from_step') or e.get('from', '') for e in edges]
        source_counts = Counter(sources)
        return any(count > 1 for count in source_counts.values())
    
    def _infer_observed_steps(self, nodes: Dict, detected: Dict, clip_content: Dict = None) -> List[str]:
        """
        基于内容相似度推断当前观测涉及的步骤
        
        策略:
        1. 如果 detected 有 steps，尝试映射到已有节点
        2. 如果有 clip_content，用相似度匹配
        3. 返回按顺序排列的观测步骤 ID
        """
        step_node_ids = [k for k in nodes.keys() if k not in ['START', 'GOAL']]
        if not step_node_ids:
            return []
        
        # 策略1: 从 detected.steps 提取并映射
        new_steps = detected.get('steps', [])
        if new_steps:
            # 提取新 steps 的 action 文本
            new_actions = []
            for s in new_steps:
                if isinstance(s, dict):
                    action = s.get('action', '')
                    if action:
                        new_actions.append(action)
            
            if new_actions:
                # 计算与已有节点的相似度
                from .utils import batch_get_normalized_embeddings, cosine_similarity
                
                # 获取已有节点的 action
                existing_actions = []
                existing_ids = []
                for sid in step_node_ids:
                    node_data = nodes.get(sid, {})
                    action = node_data.get('action', '')
                    if action:
                        existing_actions.append(action)
                        existing_ids.append(sid)
                
                if existing_actions and new_actions:
                    # 批量计算 embeddings
                    all_texts = existing_actions + new_actions
                    all_embs = batch_get_normalized_embeddings(all_texts)
                    
                    existing_embs = all_embs[:len(existing_actions)]
                    new_embs = all_embs[len(existing_actions):]
                    
                    # 找出每个新 action 最匹配的已有节点
                    observed = []
                    MATCH_THRESHOLD = 0.5  # 从 0.6 降低到 0.5 以增加匹配成功率
                    
                    for new_emb in new_embs:
                        best_sim = -1
                        best_id = None
                        for i, ex_emb in enumerate(existing_embs):
                            sim = cosine_similarity(new_emb, ex_emb)
                            if sim > best_sim:
                                best_sim = sim
                                best_id = existing_ids[i]
                        
                        if best_id and best_sim >= MATCH_THRESHOLD and best_id not in observed:
                            observed.append(best_id)
                    
                    if observed:
                        # 按 step_id 的数字排序
                        observed.sort(key=lambda x: int(x.split('_')[1]) if '_' in x and x.split('_')[1].isdigit() else 0)
                        return observed
        
        # 策略2: 使用 clip_content 的相似度（如果策略1 失败）
        if clip_content and clip_content.get('content'):
            from .utils import get_normalized_embedding, cosine_similarity
            clip_emb = get_normalized_embedding(clip_content['content'])
            
            # 计算与每个步骤的相似度
            step_sims = []
            for sid in step_node_ids:
                node_data = nodes.get(sid, {})
                action = node_data.get('action', '')
                if action:
                    action_emb = get_normalized_embedding(action)
                    sim = cosine_similarity(clip_emb, action_emb)
                    step_sims.append((sid, sim))
            
            # 选择相似度高于阈值的步骤
            OBSERVE_THRESHOLD = 0.5
            observed = [sid for sid, sim in step_sims if sim >= OBSERVE_THRESHOLD]
            
            if observed:
                observed.sort(key=lambda x: int(x.split('_')[1]) if '_' in x and x.split('_')[1].isdigit() else 0)
                return observed
        
        return []
    
    def _increment_edge_count(self, edges: List[Dict], from_step: str, to_step: str):
        """增加指定边的计数"""
        for edge in edges:
            edge_from = edge.get('from') or edge.get('from_step', '')
            edge_to = edge.get('to') or edge.get('to_step', '')
            
            if edge_from == from_step and edge_to == to_step:
                edge['count'] = edge.get('count', 1) + 1
                return True
        return False
    
    def _recompute_edge_probabilities(self, dag: Dict):
        """重新计算边的转移概率"""
        edges = dag.get('edges', [])
        
        # 按源节点分组计算总计数
        from_counts = {}
        for edge in edges:
            from_step = edge.get('from') or edge.get('from_step', '')
            count = edge.get('count', 1)
            from_counts[from_step] = from_counts.get(from_step, 0) + count
        
        # 更新概率
        for edge in edges:
            from_step = edge.get('from') or edge.get('from_step', '')
            count = edge.get('count', 1)
            total = from_counts.get(from_step, 1)
            edge['probability'] = count / total if total > 0 else 1.0
    
    def build(
        self,
        video_name: str,
        dataset: str = 'web',
        max_clips: int = None,
    ) -> Optional[Dict]:
        """
        增量构建 NSTF 图谱
        
        逐 clip 处理，检测程序性知识，判断是否合并
        """
        print(f"\n{'='*60}")
        print(f"[Incremental] 处理: {video_name} ({dataset})")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # 1. 加载 baseline 图谱
        graph = self.load_baseline_graph(video_name, dataset)
        if graph is None:
            print(f"  ✗ 图谱不存在")
            return None
        
        # 2. 初始化 CharacterResolver
        self.character_resolver = CharacterResolver(graph, debug=self.debug)
        if self.debug:
            print(f"  Character mapping: {self.character_resolver.mapping}")
        
        # 3. 获取所有 clips
        clips = self.get_sorted_clips(graph)
        if max_clips:
            clips = clips[:max_clips]
        print(f"  处理 {len(clips)} 个 clips...")
        
        # 4. 初始化 NSTF 图谱
        nstf_graph = {
            'video_name': video_name,
            'dataset': dataset,
            'procedure_nodes': {},
            'character_mapping': self.character_resolver.mapping,
            'metadata': {
                'version': '2.3.2',
                'build_mode': 'incremental',
                'created_at': datetime.now().isoformat(),
            }
        }
        
        proc_counter = 0
        skipped_count = 0
        detected_count = 0
        
        # 5. 逐 clip 处理
        for i, clip_id in enumerate(clips):
            clip_content = self.get_clip_content(graph, clip_id)
            
            # 进度显示（移到循环开头，确保每次都显示）
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{len(clips)} clips (检测到: {detected_count}, 跳过: {skipped_count})")
            
            if not clip_content['content'].strip():
                skipped_count += 1
                continue
            
            # 检测当前 clip 是否包含程序性知识
            detected = self.extractor.detect_in_clip(clip_content)
            
            if not detected:
                skipped_count += 1
                continue
            
            detected_count += 1
            self.stats['clips_processed'] += 1
            
            if self.debug:
                print(f"\n  Clip {clip_id}: 检测到程序 - {detected.get('goal', '')[:40]}...")
            
            # 尝试匹配已有 Procedure
            matched_proc = self.matcher.match_existing(nstf_graph, detected)
            
            if matched_proc:
                # 合并到已有 Procedure
                self.update_procedure(matched_proc, clip_id, clip_content, detected)
                self.stats['procedures_merged'] += 1
                if self.debug:
                    print(f"    → 合并到: {matched_proc['proc_id']}")
            else:
                # 创建新 Procedure
                proc_counter += 1
                proc_id = f"{video_name}_proc_{proc_counter}"
                new_proc = self.create_procedure_node(detected, clip_id, clip_content, proc_id)
                nstf_graph['procedure_nodes'][proc_id] = new_proc
                self.stats['procedures_created'] += 1
                if self.debug:
                    print(f"    → 创建新: {proc_id}")
            
            time.sleep(0.3)  # API 限流（降低延迟）
        
        # 清除缓存
        self.linker.clear_cache()
        self.matcher.clear_log()
        
        self.stats['videos_processed'] += 1
        
        # 6. DAG 融合 - 对相似的 Procedure 进行结构融合
        proc_nodes = nstf_graph['procedure_nodes']
        if len(proc_nodes) >= 2 and self.config.get('enable_fusion', True):
            print(f"  融合相似的 DAG...")
            procedures_before = len(proc_nodes)
            fused_nodes = self.fusion_manager.fuse_all(proc_nodes)
            nstf_graph['procedure_nodes'] = fused_nodes
            proc_nodes = fused_nodes
            procedures_after = len(proc_nodes)
            if self.debug or procedures_before != procedures_after:
                print(f"    融合: {procedures_before} → {procedures_after} procedures")
        
        # 7. 构建统计信息
        total_links = sum(len(p.get('episodic_links', [])) for p in proc_nodes.values())
        fusion_stats = self.fusion_manager.get_stats()
        
        nstf_graph['stats'] = {
            'total_procedures': len(proc_nodes),
            'total_links': total_links,
            'avg_links_per_proc': total_links / len(proc_nodes) if proc_nodes else 0,
            'merges': self.stats['procedures_merged'],
            'creates': self.stats['procedures_created'],
            'dag_fusions': fusion_stats.get('total_fusions', 0),
        }
        
        nstf_graph['metadata']['version'] = '2.3.2'  # V2.3.2: 完整字段规范
        nstf_graph['metadata']['fusion_enabled'] = self.config.get('enable_fusion', True)
        
        print(f"\n  === Build Statistics ===")
        print(f"  Procedures: {len(proc_nodes)} (created: {self.stats['procedures_created']}, merged: {self.stats['procedures_merged']}, dag_fused: {fusion_stats.get('total_fusions', 0)})")
        print(f"  Total links: {total_links}")
        print(f"  Avg links/proc: {nstf_graph['stats']['avg_links_per_proc']:.1f}")
        
        # 7. 保存
        output_subdir = self.output_dir / dataset
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        # 默认输出为 _nstf.pkl（incremental 是默认模式）
        output_path = output_subdir / f'{video_name}_nstf.pkl'
        with open(output_path, 'wb') as f:
            pickle.dump(nstf_graph, f)
        
        print(f"  ✓ 保存到: {output_path}")
        print(f"  耗时: {time.time() - start_time:.1f}秒")
        
        return nstf_graph
    
    def build_batch(
        self,
        video_names: List[str],
        dataset: str = 'web',
        max_clips: int = None,
    ):
        """批量增量构建"""
        print(f"将处理 {len(video_names)} 个视频")
        
        for video_name in video_names:
            try:
                self.build(video_name, dataset, max_clips)
                time.sleep(2)
            except Exception as e:
                print(f"  ✗ 失败: {e}")
                import traceback
                if self.debug:
                    traceback.print_exc()
        
        self.print_stats()
    
    def print_stats(self):
        """打印统计"""
        print(f"\n{'='*60}")
        print(f"增量构建完成")
        print(f"{'='*60}")
        print(f"处理视频数: {self.stats['videos_processed']}")
        print(f"处理 clips 数: {self.stats['clips_processed']}")
        print(f"创建 Procedure: {self.stats['procedures_created']}")
        print(f"合并次数: {self.stats['procedures_merged']}")
        if self.stats['procedures_created'] + self.stats['procedures_merged'] > 0:
            merge_rate = self.stats['procedures_merged'] / (self.stats['procedures_created'] + self.stats['procedures_merged'])
            print(f"合并率: {merge_rate:.1%}")
