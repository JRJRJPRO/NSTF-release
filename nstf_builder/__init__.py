# -*- coding: utf-8 -*-
"""
NSTF 图谱构建模块

将 Baseline Memory Graph 转换为 NSTF 增强图谱

两种构建模式:
- NSTFBuilder (StaticBuilder): 静态一次性构建，用于消融实验
- IncrementalNSTFBuilder: 增量构建，支持 Procedure 融合（推荐用于生产）
"""

from .builder import NSTFBuilder
from .incremental_builder import IncrementalNSTFBuilder

__all__ = ['NSTFBuilder', 'IncrementalNSTFBuilder']
