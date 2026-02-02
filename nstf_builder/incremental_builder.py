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
from .utils import get_normalized_embedding


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
        """创建新的 Procedure 节点"""
        goal = detected.get('goal', '')
        if isinstance(goal, dict):
            goal = goal.get('name', str(goal))
        goal = str(goal)
        
        description = detected.get('description', '')
        proc_type = detected.get('type', 'task')
        steps = detected.get('steps', [])
        
        # 生成 embedding
        text_for_embedding = f"{goal}. {description}"
        emb = get_normalized_embedding(text_for_embedding)
        
        return {
            'proc_id': proc_id,
            'type': 'procedure',
            'goal': goal,
            'description': description,
            'proc_type': proc_type,
            'steps': steps,
            'episodic_links': [{
                'clip_id': clip_id,
                'relevance': 'source',
                'similarity': 1.0,  # 首次创建，similarity = 1
                'content_preview': clip_content['content'][:100]
            }],
            'embeddings': {
                'goal_emb': emb
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'source': 'incremental_nstf',
                'observation_count': 1,
                'source_clips': [clip_id],
            }
        }
    
    def update_procedure(
        self, 
        proc: Dict, 
        clip_id: int, 
        clip_content: Dict,
        detected: Dict
    ):
        """更新已有 Procedure（合并操作）"""
        # 计算相似度
        proc_emb = proc.get('embeddings', {}).get('goal_emb')
        if proc_emb is not None:
            content_emb = get_normalized_embedding(clip_content['content'])
            import numpy as np
            sim = float(np.dot(proc_emb, content_emb))
        else:
            sim = 0.5
        
        # 添加 episodic_link
        proc['episodic_links'].append({
            'clip_id': clip_id,
            'relevance': 'update',
            'similarity': round(sim, 4),
            'content_preview': clip_content['content'][:100]
        })
        
        # 更新元数据
        proc['metadata']['observation_count'] = proc['metadata'].get('observation_count', 0) + 1
        if 'source_clips' not in proc['metadata']:
            proc['metadata']['source_clips'] = []
        proc['metadata']['source_clips'].append(clip_id)
        
        # 如果新检测到的步骤更详细，可以考虑合并步骤
        new_steps = detected.get('steps', [])
        if new_steps and len(new_steps) > len(proc.get('steps', [])):
            # 新步骤更详细，更新
            proc['steps'] = new_steps
            if self.debug:
                print(f"    Updated steps: {len(new_steps)} steps")
    
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
                'version': '2.2.2',
                'build_mode': 'incremental',
                'created_at': datetime.now().isoformat(),
            }
        }
        
        proc_counter = 0
        
        # 5. 逐 clip 处理
        for i, clip_id in enumerate(clips):
            clip_content = self.get_clip_content(graph, clip_id)
            
            if not clip_content['content'].strip():
                continue
            
            # 检测当前 clip 是否包含程序性知识
            detected = self.extractor.detect_in_clip(clip_content)
            
            if not detected:
                continue
            
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
            
            # 进度显示
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{len(clips)} clips")
            
            time.sleep(0.5)  # API 限流
        
        # 清除缓存
        self.linker.clear_cache()
        self.matcher.clear_log()
        
        self.stats['videos_processed'] += 1
        
        # 6. 构建统计信息
        proc_nodes = nstf_graph['procedure_nodes']
        total_links = sum(len(p.get('episodic_links', [])) for p in proc_nodes.values())
        
        nstf_graph['stats'] = {
            'total_procedures': len(proc_nodes),
            'total_links': total_links,
            'avg_links_per_proc': total_links / len(proc_nodes) if proc_nodes else 0,
            'merges': self.stats['procedures_merged'],
            'creates': self.stats['procedures_created'],
        }
        
        print(f"\n  === Build Statistics ===")
        print(f"  Procedures: {len(proc_nodes)} (created: {self.stats['procedures_created']}, merged: {self.stats['procedures_merged']})")
        print(f"  Total links: {total_links}")
        print(f"  Avg links/proc: {nstf_graph['stats']['avg_links_per_proc']:.1f}")
        
        # 7. 保存
        output_subdir = self.output_dir / dataset
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_subdir / f'{video_name}_nstf_incremental.pkl'
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
