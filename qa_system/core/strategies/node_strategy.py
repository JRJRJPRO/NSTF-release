"""
节点级别检索策略（独立实现）

核心逻辑：
  查询 embedding → 和每个文本节点的 embedding 计算相似度 → 排序 → 取 top-k

不依赖 mmagent.retrieve 的复杂函数，只使用：
  - back_translate(): 查询扩展（人名→face_id）
  - translate(): 结果翻译（face_id→人名）
  - parallel_get_embedding(): 计算 embedding
  - video_graph.nodes: 访问节点数据

与 baseline 的一致性：
  - 使用 back_translate 处理人名
  - 多个 query 变体取 max（不是 mean）
  - 支持 include_semantic 配置
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict
from .base import RetrievalStrategy


class NodeLevelStrategy(RetrievalStrategy):
    """
    节点级别检索策略（独立实现）
    """
    
    def __init__(
        self, 
        include_timestamp: bool = True, 
        group_by_clip: bool = True,
        include_semantic: bool = False,
        preserve_clip_order: bool = True,
    ):
        """
        Args:
            include_timestamp: 是否在返回中包含时间戳
            group_by_clip: 是否按 clip 分组返回（默认 True 保持格式兼容）
            include_semantic: 是否包含 semantic 节点（默认只要 episodic）
            preserve_clip_order: group 后是否恢复时间顺序
        """
        self.include_timestamp = include_timestamp
        self.group_by_clip = group_by_clip
        self.include_semantic = include_semantic
        self.preserve_clip_order = preserve_clip_order
        self._retrieved_node_ids: Set[int] = set()
    
    @property
    def name(self) -> str:
        return "node_level"
    
    def reset(self):
        """每个新问题开始时调用，重置去重状态"""
        self._retrieved_node_ids.clear()
    
    def search(
        self, 
        video_graph: Any, 
        query: str, 
        current_context: List,
        topk: int,
        threshold: float,
        before_clip: Optional[int] = None,
        **kwargs
    ) -> Tuple[Dict, List, Optional[Dict]]:
        """
        节点级别检索
        
        流程:
        1. 查询预处理（back_translate 替换人名为 face_id）
        2. 计算查询 embedding（多个变体）
        3. 遍历所有文本节点，计算相似度（对 query 变体取 max，与 baseline 一致）
        4. 过滤（时间、阈值、去重、节点类型）+ 排序 + 取 top-k
        5. 格式化返回（group 后恢复时间顺序）
        """
        import random
        from mmagent.retrieve import back_translate, translate
        from mmagent.utils.chat_api import parallel_get_embedding
        
        # 1. 查询预处理（替换人名为内部ID，生成多个查询变体）
        queries = back_translate(video_graph, [query])
        if len(queries) > 100:
            queries = random.sample(queries, 100)
        
        # 2. 计算所有查询变体的 embedding
        model = "text-embedding-3-large"
        query_embeddings = parallel_get_embedding(model, queries)[0]
        query_embeddings = np.array(query_embeddings)
        
        # 归一化
        norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # 避免除零
        query_embeddings = query_embeddings / norms
        
        # 3. 遍历所有文本节点，计算相似度（对 query 变体取 max，与 baseline 一致）
        nodes_with_scores = []
        for node_id, node in video_graph.nodes.items():
            # 节点类型过滤
            if node.type in ['img', 'voice']:
                continue
            if not self.include_semantic and node.type == 'semantic':
                continue
            
            # 获取节点 embedding（注意：是 embeddings 复数，不是 embedding）
            node_emb = getattr(node, 'embeddings', None)
            if node_emb is None:
                continue
            
            # 处理 embedding 格式（参考 videograph.py search_text_nodes）
            try:
                if isinstance(node_emb, list):
                    if len(node_emb) == 0:
                        continue
                    if isinstance(node_emb[0], list):
                        # [[emb]] 格式
                        vec = np.array(node_emb[0], dtype=float)
                    elif isinstance(node_emb[0], (int, float)):
                        # [emb] 格式
                        vec = np.array(node_emb, dtype=float)
                    else:
                        continue
                else:
                    vec = np.array(node_emb, dtype=float).flatten()
                
                # 检查维度是否合理
                if vec.size < 64:
                    continue
                
                # 维度对齐
                query_dim = query_embeddings.shape[1]
                if vec.size > query_dim:
                    vec = vec[:query_dim]
                elif vec.size < query_dim:
                    vec = np.pad(vec, (0, query_dim - vec.size))
                
                node_embedding = vec.reshape(1, -1)
            except Exception:
                continue
            
            # 归一化
            node_norm = np.linalg.norm(node_embedding)
            if node_norm == 0:
                continue
            node_embedding = node_embedding / node_norm
            
            # 与所有 query 变体计算相似度，取 max
            similarities = np.dot(query_embeddings, node_embedding.T)  # (n_queries, 1)
            score = float(np.max(similarities))  # 取 max，与 baseline 一致
            
            nodes_with_scores.append((node_id, score))
        
        # 按分数排序
        nodes_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 4. 过滤和选取 top-k
        filtered_nodes = []
        for node_id, score in nodes_with_scores:
            # 去重（基于 node_id）
            if node_id in self._retrieved_node_ids:
                continue
            
            node = video_graph.nodes[node_id]
            clip_id = node.metadata.get('timestamp', -1)
            
            # 时间过滤（不用 truncate，直接 filter，避免缓存污染）
            if before_clip is not None and clip_id > before_clip:
                continue
            
            # 阈值过滤
            if score < threshold:
                continue
            
            content = node.metadata.get('contents', [''])[0]
            
            filtered_nodes.append({
                'node_id': node_id,
                'score': score,
                'clip_id': clip_id,
                'content': content,
                'type': node.type,
            })
            
            # 取够了就停
            if len(filtered_nodes) >= topk:
                break
        
        # 更新已检索节点集合
        for n in filtered_nodes:
            self._retrieved_node_ids.add(n['node_id'])
        
        # 5. 格式化返回
        if self.group_by_clip:
            memories = self._format_grouped(video_graph, filtered_nodes)
        else:
            memories = self._format_flat(video_graph, filtered_nodes)
        
        # 更新上下文（保持接口兼容）
        updated_context = current_context + [n['content'] for n in filtered_nodes]
        
        metadata = {
            'strategy': self.name,
            'num_nodes': len(filtered_nodes),
            'node_scores': [(n['node_id'], n['score']) for n in filtered_nodes],
            'total_retrieved': len(self._retrieved_node_ids),
        }
        
        return memories, updated_context, metadata
    
    def _format_flat(self, video_graph, nodes: List[Dict]) -> Dict:
        """扁平格式：按相关度排序的节点列表"""
        from mmagent.retrieve import translate
        
        memories = {"RETRIEVED_NODES": []}
        for n in nodes:
            content = translate(video_graph, [n['content']])[0]
            if self.include_timestamp:
                entry = f"[CLIP_{n['clip_id']}] {content}"
            else:
                entry = content
            memories["RETRIEVED_NODES"].append(entry)
        
        return memories
    
    def _format_grouped(self, video_graph, nodes: List[Dict]) -> Dict:
        """
        分组格式：按 clip 分组（与 baseline 格式兼容）
        
        返回格式:
        {
            "CLIP_5": ["event1", "event2"],
            "CLIP_8": ["event1"],
        }
        
        如果 preserve_clip_order=True，同一 clip 内的节点按原始时间顺序排列
        """
        from mmagent.retrieve import translate
        
        # 按 clip 分组
        grouped = defaultdict(list)
        for n in nodes:
            grouped[n['clip_id']].append(n)
        
        # 如果需要恢复时间顺序
        if self.preserve_clip_order:
            for clip_id in grouped:
                # 获取该 clip 原始节点顺序
                original_order = getattr(video_graph, 'text_nodes_by_clip', {}).get(clip_id, [])
                order_map = {nid: i for i, nid in enumerate(original_order)}
                # 按原始顺序排序（未找到的放最后）
                grouped[clip_id].sort(key=lambda x: order_map.get(x['node_id'], float('inf')))
        
        # 格式化输出
        memories = {}
        for clip_id in sorted(grouped.keys()):
            contents = [translate(video_graph, [n['content']])[0] for n in grouped[clip_id]]
            memories[f"CLIP_{clip_id}"] = contents
        
        return memories
