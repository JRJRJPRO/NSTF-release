# -*- coding: utf-8 -*-
"""
NSTF 图谱构建器

V2.2.2 版本更新:
- 集成 CharacterResolver 解析 character ID
- 添加 extract_all_episodic 方法（应用 character 解析）
- 使用公共 embedding 工具函数
- 集成 EpisodicLinker 自动发现和验证链接
"""

import os
import sys
import json
import pickle
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 统一环境设置
from env_setup import setup_all, NSTF_MODEL_DIR
setup_all()

from .extractor import ProcedureExtractor
from .character_resolver import CharacterResolver
from .episodic_linker import EpisodicLinker
from .dag_fusion import DAGFusion, ProcedureFusionManager
from .utils import get_normalized_embedding, batch_get_normalized_embeddings


class NSTFBuilder:
    """NSTF 图谱构建器"""
    
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
        
        # 提取器
        self.extractor = ProcedureExtractor(
            llm_model=self.config.get('llm_model', 'gemini-2.5-flash'),
            batch_size=self.config.get('batch_size', 40),
            max_content_chars=self.config.get('max_content_chars', 150),
            api_delay=self.config.get('api_delay_seconds', 1),
        )
        
        # EpisodicLinker（Phase 1 新增）
        self.episodic_linker = EpisodicLinker(
            verify_threshold=self.config.get('verify_threshold', 0.35),
            discover_threshold=self.config.get('discover_threshold', 0.50),
            max_links_per_proc=self.config.get('max_links_per_proc', 10),
            debug=debug,
        )
        
        # ProcedureFusionManager（DAG 融合）
        self.fusion_manager = ProcedureFusionManager(
            similarity_threshold=self.config.get('fusion_similarity_threshold', 0.80),
            step_align_threshold=self.config.get('step_align_threshold', 0.75),
            debug=debug,
        )
        
        # Character 解析器（每次 build 时初始化）
        self.character_resolver: Optional[CharacterResolver] = None
        
        # Embedding
        self.embedding_model = self.config.get('embedding_model', 'text-embedding-3-large')
        self._embedding_api = None
        
        # 统计
        self.stats = {
            'videos_processed': 0,
            'procedures_extracted': 0,
            'total_steps': 0,
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
        """加载baseline图谱"""
        graph_path = self.data_dir / 'memory_graphs' / dataset / f'{video_name}.pkl'
        if not graph_path.exists():
            return None
        with open(graph_path, 'rb') as f:
            return pickle.load(f)
    
    def extract_episodic_contents(self, graph, max_clips: int = None) -> List[Dict]:
        """从图谱中提取episodic节点内容（旧方法，保持兼容）"""
        contents = []
        
        for node_id, node in graph.nodes.items():
            if getattr(node, 'type', '') == 'episodic':
                metadata = getattr(node, 'metadata', {})
                clip_id = metadata.get('timestamp', 0)
                content_list = metadata.get('contents', [])
                
                if content_list:
                    contents.append({
                        'clip_id': clip_id,
                        'content': content_list[0] if content_list else '',
                        'node_id': node_id
                    })
        
        contents.sort(key=lambda x: x['clip_id'])
        
        if max_clips:
            contents = contents[:max_clips]
        
        return contents
    
    def extract_all_episodic(self, graph) -> List[Dict]:
        """
        提取所有 episodic 内容，并应用 CharacterResolver 替换 ID
        
        重要：必须在返回前调用 character_resolver.resolve()
        否则内容仍然是 <character_2>，后续匹配会有问题
        
        Returns:
            包含 clip_id, content, raw_content 的字典列表
        """
        all_contents = []
        
        # 使用 text_nodes_by_clip 获取每个 clip 的内容
        if hasattr(graph, 'text_nodes_by_clip'):
            for clip_id in sorted(graph.text_nodes_by_clip.keys()):
                node_ids = graph.text_nodes_by_clip[clip_id]
                clip_texts = []
                
                for nid in node_ids:
                    node = graph.nodes.get(nid)
                    if node and hasattr(node, 'metadata'):
                        contents = node.metadata.get('contents', [])
                        clip_texts.extend(contents)
                
                if clip_texts:
                    # 合并内容
                    combined = ' '.join(clip_texts)
                    
                    # 应用 CharacterResolver 替换 ID（关键步骤!）
                    if self.character_resolver:
                        resolved = self.character_resolver.resolve(combined)
                    else:
                        resolved = combined
                    
                    all_contents.append({
                        'clip_id': clip_id,
                        'content': resolved,
                        'raw_content': combined  # 保留原始内容便于调试
                    })
        else:
            # Fallback 到旧方法
            old_contents = self.extract_episodic_contents(graph)
            for item in old_contents:
                combined = item['content']
                if self.character_resolver:
                    resolved = self.character_resolver.resolve(combined)
                else:
                    resolved = combined
                all_contents.append({
                    'clip_id': item['clip_id'],
                    'content': resolved,
                    'raw_content': combined
                })
        
        if self.debug:
            print(f"  提取了 {len(all_contents)} 个clips的episodic内容")
            # 检查是否还有未替换的 character ID
            unresolved_count = 0
            for item in all_contents:
                if self.character_resolver and self.character_resolver.has_unresolved_ids(item['content']):
                    unresolved_count += 1
            if unresolved_count > 0:
                print(f"  ⚠️ 有 {unresolved_count} 个clips包含未解析的 character ID")
        
        return all_contents
    
    def create_procedure_node(self, structure: Dict, proc_id: str) -> Dict:
        """
        创建 Procedure 节点（V2.3.1 完全符合论文规范）
        
        论文要求的双层 Index Vectors:
        - goal_emb: φ(goal) - goal 文本的 embedding
        - step_emb: Mean(φ(s) for s in steps) - 所有 step 的平均 embedding
        
        V2.3.1 新增:
        - objects: 涉及的具体物品
        - locations: 涉及的具体位置
        - participants: 参与者
        """
        import numpy as np
        
        goal = structure.get('goal', proc_id)
        # 确保 goal 是字符串
        if isinstance(goal, dict):
            goal = goal.get('name', str(goal))
        goal = str(goal)
        
        description = structure.get('description', '')
        if isinstance(description, dict):
            description = str(description)
        
        raw_steps = structure.get('steps', [])
        
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
        
        # V2.3.1: 提取具体的物品、位置、参与者
        objects = structure.get('objects', structure.get('key_objects', []))
        locations = structure.get('locations', structure.get('key_locations', []))
        participants = structure.get('participants', [])
        
        # 提取 step actions（包含 object 和 location）
        step_actions = []
        for s in steps:
            if isinstance(s, dict):
                action = s.get('action', '')
                if isinstance(action, str) and action:
                    # 包含 object 和 location 以提高精度
                    full_action = action
                    if s.get('object'):
                        full_action += f" with {s['object']}"
                    if s.get('location'):
                        full_action += f" at {s['location']}"
                    step_actions.append(full_action)
            elif isinstance(s, str) and s:
                step_actions.append(s)
        
        # ========== 双层 Index Vectors (论文核心!) ==========
        # 1. goal_emb: φ(goal) - 包含具体物品和位置
        goal_text = f"{goal}. {description}" if description else goal
        if objects:
            goal_text += f" Objects: {', '.join(objects[:5])}"
        if locations:
            goal_text += f" Locations: {', '.join(locations[:5])}"
        
        try:
            goal_embedding, _ = self.embedding_api(self.embedding_model, goal_text)
            goal_emb = np.array(goal_embedding)
            goal_emb = goal_emb / (np.linalg.norm(goal_emb) + 1e-8)
        except Exception as e:
            print(f"    Goal embedding 生成失败: {e}")
            goal_emb = np.zeros(3072)
        
        # 2. step_emb: Mean(φ(s) for s in steps)
        if step_actions:
            try:
                step_embeddings = batch_get_normalized_embeddings(step_actions)
                step_emb = np.mean(step_embeddings, axis=0)
                step_emb = step_emb / (np.linalg.norm(step_emb) + 1e-8)
            except Exception as e:
                print(f"    Step embeddings 生成失败: {e}")
                step_emb = goal_emb.copy()  # fallback: 使用 goal_emb
        else:
            # 无 steps 时 fallback 到 goal_emb
            step_emb = goal_emb.copy()
        
        # ========== 构建完整的 DAG 结构 ==========
        dag = self._construct_dag(steps, structure.get('edges', []))
        
        return {
            'proc_id': proc_id,
            'type': 'procedure',
            'goal': goal,
            'description': description,
            'proc_type': structure.get('proc_type', structure.get('type', 'task')),
            'steps': steps,
            'dag': dag,  # 完整的 DAG 结构（含 START/GOAL）
            'edges': structure.get('edges', []),  # 保留兼容性
            # V2.3.1: 新增具体信息字段
            'objects': objects,
            'locations': locations,
            'participants': participants,
            'episodic_links': structure.get('episodic_links', []),
            'embeddings': {
                'goal_emb': goal_emb,   # 论文: i_goal = φ(c)
                'step_emb': step_emb,   # 论文: i_step = Mean(φ(s))
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'observation_count': 1,
                'source_clips': structure.get('source_clips', []),
                'source': 'nstf_extraction',
                'version': '2.3.2'  # V2.3.2: 完整字段规范
            }
        }
    
    def _construct_dag(self, steps: List, edges: List) -> Dict:
        """
        构建完整的 Procedural DAG (论文规范)
        
        论文要求: G = (V, E, A)
        - V: 节点集合，包含 START 和 GOAL
        - E: 有向边集合，带转移计数 N_ij
        - A: 节点属性映射
        """
        # 1. 构建节点集合 V
        nodes = {
            'START': {'type': 'control', 'attributes': {}},
            'GOAL': {'type': 'control', 'attributes': {}}
        }
        
        for s in steps:
            if isinstance(s, dict):
                step_id = s.get('step_id', f"step_{len(nodes)-1}")
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
            elif isinstance(s, str):
                step_id = f"step_{len(nodes)-1}"
                nodes[step_id] = {
                    'type': 'action',
                    'action': s,
                    'attributes': {'object': '', 'location': '', 'actor': '', 'triggers': [], 'outcomes': [], 'duration_seconds': 0}
                }
        
        # 2. 构建边集合 E（带转移计数）
        dag_edges = []
        step_ids = [sid for sid in nodes.keys() if sid not in ('START', 'GOAL')]
        
        if edges:
            # 使用提供的边
            for e in edges:
                dag_edges.append({
                    'from': e.get('from_step', e.get('from', '')),
                    'to': e.get('to_step', e.get('to', '')),
                    'count': e.get('count', 1),  # 初始计数为1
                    'probability': e.get('probability', 1.0),
                    'condition': e.get('condition', None)
                })
        elif step_ids:
            # 自动构建线性序列 + START/GOAL
            # START -> first_step
            dag_edges.append({
                'from': 'START',
                'to': step_ids[0],
                'count': 1,
                'probability': 1.0,
                'condition': None
            })
            
            # step_i -> step_{i+1}
            for i in range(len(step_ids) - 1):
                dag_edges.append({
                    'from': step_ids[i],
                    'to': step_ids[i + 1],
                    'count': 1,
                    'probability': 1.0,
                    'condition': None
                })
            
            # last_step -> GOAL
            dag_edges.append({
                'from': step_ids[-1],
                'to': 'GOAL',
                'count': 1,
                'probability': 1.0,
                'condition': None
            })
        
        return {
            'nodes': nodes,
            'edges': dag_edges
        }
    
    def build(
        self,
        video_name: str,
        dataset: str = 'web',
        max_procedures: int = None,
    ) -> Optional[Dict]:
        """为单个视频构建NSTF图谱"""
        
        max_procedures = max_procedures or self.config.get('max_procedures', 5)
        
        print(f"\n{'='*60}")
        print(f"处理: {video_name} ({dataset})")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # 1. 加载baseline图谱
        graph = self.load_baseline_graph(video_name, dataset)
        if graph is None:
            print(f"  ✗ 图谱不存在")
            return None
        
        # 2. 初始化 CharacterResolver
        self.character_resolver = CharacterResolver(graph, debug=self.debug)
        if self.debug:
            print(f"  Character mapping: {self.character_resolver.mapping}")
        
        # 3. 提取episodic内容（使用新方法，应用 character 解析）
        contents = self.extract_all_episodic(graph)
        print(f"  提取了 {len(contents)} 个episodic内容")
        
        # 4. 检测程序性知识
        print("  检测程序性知识...")
        procedures = self.extractor.detect_procedures(contents, max_procedures)
        print(f"  检测到 {len(procedures)} 个程序")
        
        # 5. 提取每个程序的结构
        procedure_nodes = {}
        for i, proc in enumerate(procedures):
            proc_id = f"{video_name}_proc_{i+1}"
            goal = proc.get('goal', proc_id)
            # 确保 goal 可打印
            if isinstance(goal, dict):
                goal_str = goal.get('name', str(goal)[:50])
            else:
                goal_str = str(goal)[:50]
            print(f"  提取结构: {goal_str}")
            
            try:
                structure = self.extractor.extract_structure(contents, proc)
                if structure:
                    node = self.create_procedure_node(structure, proc_id)
                    
                    # Phase 1: 使用 EpisodicLinker 重新构建 episodic_links
                    if self.debug:
                        print(f"    构建 episodic_links...")
                    verified_links = self.episodic_linker.build_verified_links(
                        procedure=structure,
                        all_episodic_contents=contents,
                    )
                    node['episodic_links'] = verified_links
                    
                    procedure_nodes[proc_id] = node
                    self.stats['total_steps'] += len(structure.get('steps', []))
            except Exception as e:
                print(f"    ⚠️ 结构提取失败: {e}")
                import traceback
                if self.debug:
                    traceback.print_exc()
            
            time.sleep(1)  # API限流
        
        # 清除 EpisodicLinker 缓存（释放内存）
        self.episodic_linker.clear_cache()
        
        # 6. DAG 融合 - 合并相似的 procedure
        if len(procedure_nodes) >= 2 and self.config.get('enable_fusion', True):
            print("  融合相似的 DAG...")
            procedures_before = len(procedure_nodes)
            procedure_nodes = self.fusion_manager.fuse_all(procedure_nodes)
            procedures_after = len(procedure_nodes)
            if self.debug or procedures_before != procedures_after:
                print(f"    融合: {procedures_before} → {procedures_after} procedures")
        
        self.stats['procedures_extracted'] += len(procedure_nodes)
        self.stats['videos_processed'] += 1
        
        # 7. 构建统计信息
        total_links = sum(len(p.get('episodic_links', [])) for p in procedure_nodes.values())
        fusion_stats = self.fusion_manager.get_stats()
        stats = {
            'total_procedures': len(procedure_nodes),
            'total_links': total_links,
            'avg_links_per_proc': total_links / len(procedure_nodes) if procedure_nodes else 0,
            'character_mapping_found': bool(self.character_resolver.mapping),
            'fusion_performed': fusion_stats.get('total_fusions', 0),
            'procedures_before_fusion': fusion_stats.get('procedures_before', len(procedure_nodes)),
        }
        
        if self.debug:
            print(f"\n  === Build Statistics ===")
            print(f"  Procedures: {stats['total_procedures']}")
            print(f"  Total links: {stats['total_links']}")
            print(f"  Avg links/proc: {stats['avg_links_per_proc']:.1f}")
            print(f"  Character mapping: {'Yes' if stats['character_mapping_found'] else 'No'}")
            print(f"  Fusions performed: {stats['fusion_performed']}")
        
        # 8. 保存
        output_subdir = self.output_dir / dataset
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        result = {
            'video_name': video_name,
            'dataset': dataset,
            'procedure_nodes': procedure_nodes,
            'character_mapping': self.character_resolver.mapping,
            'metadata': {
                'version': '2.3.0',  # 版本更新: 添加 DAG 融合
                'created_at': datetime.now().isoformat(),
                'num_procedures': len(procedure_nodes),
                'processing_time': time.time() - start_time,
                'fusion_enabled': self.config.get('enable_fusion', True),
            },
            'stats': stats
        }
        
        output_path = output_subdir / f'{video_name}_nstf.pkl'
        with open(output_path, 'wb') as f:
            pickle.dump(result, f)
        
        print(f"  ✓ 保存到: {output_path}")
        print(f"  耗时: {time.time() - start_time:.1f}秒")
        
        return result
    
    def build_batch(
        self,
        video_names: List[str],
        dataset: str = 'web',
        max_procedures: int = None,
    ):
        """批量构建NSTF图谱"""
        
        print(f"将处理 {len(video_names)} 个视频")
        
        for video_name in video_names:
            try:
                self.build(video_name, dataset, max_procedures)
                time.sleep(2)
            except Exception as e:
                print(f"  ✗ 失败: {e}")
        
        self.print_stats()
    
    def print_stats(self):
        """打印统计"""
        print(f"\n{'='*60}")
        print(f"构建完成")
        print(f"{'='*60}")
        print(f"处理视频数: {self.stats['videos_processed']}")
        print(f"提取程序数: {self.stats['procedures_extracted']}")
        print(f"总步骤数: {self.stats['total_steps']}")
