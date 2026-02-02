"""
检索策略基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any


class RetrievalStrategy(ABC):
    """检索策略基类"""
    
    @abstractmethod
    def search(
        self,
        video_graph: Any,
        query: str,
        current_context: List,
        topk: int,
        threshold: float,
        before_clip: Optional[int] = None,
        **kwargs
    ) -> Tuple[Dict[str, Any], List, Optional[Dict]]:
        """
        执行检索
        
        Args:
            video_graph: VideoGraph 对象
            query: 查询字符串
            current_context: 已检索过的内容（用于去重）
            topk: 返回数量
            threshold: 相似度阈值
            before_clip: 时间限制（只搜索此 clip 之前的内容）
            **kwargs: 额外参数
        
        Returns:
            memories: 检索结果 {key: content}
            updated_context: 更新后的上下文
            metadata: 额外元信息（如分数、来源等）
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    def reset(self):
        """
        重置策略状态（每个新问题开始时调用）
        
        子类可以覆盖此方法来清理状态
        """
        pass
