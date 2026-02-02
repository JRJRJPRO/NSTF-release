"""
检索器 V2 - 支持多种检索策略

使用策略模式，可以灵活切换:
- clip_level: 原始 Clip 级别检索（baseline 兼容）
- node_level: 节点级别检索（NSTF 增强）
"""

from typing import Dict, List, Optional, Any
from .strategies import ClipLevelStrategy, NodeLevelStrategy, RetrievalStrategy


class RetrieverV2:
    """
    检索器 V2 - 支持多种检索策略
    """
    
    STRATEGIES = {
        'clip_level': ClipLevelStrategy,
        'node_level': NodeLevelStrategy,
    }
    
    def __init__(
        self,
        strategy: str = 'clip_level',
        threshold: float = 0.3,
        topk: int = 10,
        **strategy_kwargs
    ):
        """
        Args:
            strategy: 检索策略名称 ('clip_level' 或 'node_level')
            threshold: 相似度阈值
            topk: 返回数量
            strategy_kwargs: 传递给策略的额外参数
                - include_timestamp: bool (node_level)
                - group_by_clip: bool (node_level)
                - include_semantic: bool (node_level)
                - preserve_clip_order: bool (node_level)
        """
        self.threshold = threshold
        self.topk = topk
        
        # 初始化策略
        if strategy not in self.STRATEGIES:
            raise ValueError(f"未知策略: {strategy}. 可选: {list(self.STRATEGIES.keys())}")
        
        self._strategy = self.STRATEGIES[strategy](**strategy_kwargs)
        
        # 图谱缓存
        self._graph_cache: Dict[str, Any] = {}
    
    @property
    def strategy_name(self) -> str:
        return self._strategy.name
    
    def set_strategy(self, strategy: str, **kwargs):
        """运行时切换策略"""
        if strategy not in self.STRATEGIES:
            raise ValueError(f"未知策略: {strategy}")
        self._strategy = self.STRATEGIES[strategy](**kwargs)
    
    def reset(self):
        """重置策略状态（每个新问题开始时调用）"""
        self._strategy.reset()
    
    def search(
        self,
        mem_path: str,
        query: str,
        current_context: List = None,
        before_clip: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行检索
        
        Args:
            mem_path: 图谱文件路径
            query: 查询字符串
            current_context: 已检索过的内容
            before_clip: 时间限制
            **kwargs: 传递给策略的额外参数
        
        Returns:
            {
                'memories': 检索结果,
                'context': 更新后的上下文,
                'metadata': 元信息,
            }
        """
        if current_context is None:
            current_context = []
        
        # 加载图谱
        video_graph = self._load_graph(mem_path)
        
        # 调用策略
        memories, updated_context, metadata = self._strategy.search(
            video_graph=video_graph,
            query=query,
            current_context=current_context,
            topk=self.topk,
            threshold=self.threshold,
            before_clip=before_clip,
            **kwargs
        )
        
        return {
            'memories': memories,
            'context': updated_context,
            'metadata': metadata,
        }
    
    def _load_graph(self, mem_path: str):
        """
        加载图谱（带缓存）
        
        注意：不使用 truncate_memory_by_clip，避免缓存污染。
        时间过滤在 search 时通过 before_clip 参数实现。
        """
        if mem_path not in self._graph_cache:
            from mmagent.utils.general import load_video_graph
            graph = load_video_graph(mem_path)
            graph.refresh_equivalences()
            self._graph_cache[mem_path] = graph
        return self._graph_cache[mem_path]
    
    def clear_cache(self):
        """清空图谱缓存"""
        self._graph_cache.clear()
