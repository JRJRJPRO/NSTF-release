"""
Clip 级别检索策略

直接调用 mmagent.retrieve.search()，保持与 baseline 完全一致
"""

from typing import Dict, List, Tuple, Optional, Any
from .base import RetrievalStrategy


class ClipLevelStrategy(RetrievalStrategy):
    """
    Clip 级别检索策略
    
    直接调用 mmagent.retrieve.search()，保持与 baseline 完全一致。
    用于 baseline 实验，确保结果可比。
    """
    
    def __init__(self):
        """初始化 Clip 级别策略"""
        pass
    
    @property
    def name(self) -> str:
        return "clip_level"
    
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
        Clip 级别检索
        
        直接调用原始 mmagent.retrieve.search()
        """
        from mmagent.retrieve import search as mmagent_search
        
        # 直接调用原始 search
        memories, updated_clips, scores = mmagent_search(
            video_graph, 
            query, 
            current_context,
            topk=topk, 
            threshold=threshold, 
            before_clip=before_clip
        )
        
        metadata = {
            'strategy': self.name,
            'clip_scores': scores,
            'num_clips': len(memories),
        }
        
        return memories, updated_clips, metadata
