"""
检索策略模块

支持的策略：
- ClipLevelStrategy: Clip 级别检索（baseline 兼容）
- NodeLevelStrategy: 节点级别检索（NSTF 增强）
"""

from .base import RetrievalStrategy
from .clip_strategy import ClipLevelStrategy
from .node_strategy import NodeLevelStrategy

__all__ = [
    'RetrievalStrategy',
    'ClipLevelStrategy', 
    'NodeLevelStrategy',
]
