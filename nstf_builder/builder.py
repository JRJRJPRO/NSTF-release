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
        """创建Procedure节点"""
        
        goal = structure.get('goal', proc_id)
        # 确保 goal 是字符串
        if isinstance(goal, dict):
            goal = goal.get('name', str(goal))
        goal = str(goal)
        
        description = structure.get('description', '')
        if isinstance(description, dict):
            description = str(description)
        
        steps = structure.get('steps', [])
        
        # 生成embedding - 安全处理 steps
        step_actions = []
        for s in steps:
            if isinstance(s, dict):
                action = s.get('action', '')
                if isinstance(action, str):
                    step_actions.append(action)
            elif isinstance(s, str):
                step_actions.append(s)
        
        text_for_embedding = f"{goal}. {description}. Steps: " + ", ".join(step_actions)
        
        try:
            embedding, _ = self.embedding_api(self.embedding_model, text_for_embedding)
        except Exception as e:
            print(f"    Embedding生成失败: {e}")
            embedding = [0.0] * 3072
        
        # 规范化 embedding 为 numpy array
        import numpy as np
        emb_array = np.array(embedding)
        emb_normalized = emb_array / (np.linalg.norm(emb_array) + 1e-8)
        
        return {
            'proc_id': proc_id,
            'type': 'procedure',
            'goal': goal,
            'description': description,
            'steps': steps,
            'edges': structure.get('edges', []),
            'episodic_links': structure.get('episodic_links', []),
            'embeddings': {
                'goal_emb': emb_normalized  # V2.2 格式：使用 goal_emb 字段
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'source': 'nstf_extraction'
            }
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
        
        self.stats['procedures_extracted'] += len(procedure_nodes)
        self.stats['videos_processed'] += 1
        
        # 6. 构建统计信息
        total_links = sum(len(p.get('episodic_links', [])) for p in procedure_nodes.values())
        stats = {
            'total_procedures': len(procedure_nodes),
            'total_links': total_links,
            'avg_links_per_proc': total_links / len(procedure_nodes) if procedure_nodes else 0,
            'character_mapping_found': bool(self.character_resolver.mapping),
        }
        
        if self.debug:
            print(f"\n  === Build Statistics ===")
            print(f"  Procedures: {stats['total_procedures']}")
            print(f"  Total links: {stats['total_links']}")
            print(f"  Avg links/proc: {stats['avg_links_per_proc']:.1f}")
            print(f"  Character mapping: {'Yes' if stats['character_mapping_found'] else 'No'}")
        
        # 7. 保存
        output_subdir = self.output_dir / dataset
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        result = {
            'video_name': video_name,
            'dataset': dataset,
            'procedure_nodes': procedure_nodes,
            'character_mapping': self.character_resolver.mapping,
            'metadata': {
                'version': '2.2.2',
                'created_at': datetime.now().isoformat(),
                'num_procedures': len(procedure_nodes),
                'processing_time': time.time() - start_time
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
