# -*- coding: utf-8 -*-
"""
NSTF 图谱构建模块

将 Baseline Memory Graph 转换为 NSTF 增强图谱

两种构建模式:
- NSTFBuilder (StaticBuilder): 静态一次性构建，用于消融实验
- IncrementalNSTFBuilder: 增量构建，支持 Procedure 融合（推荐用于生产）

核心组件:
- DAGFusion: DAG 融合模块
- ProcedureFusionManager: 程序融合管理器
- ProcedureExtractor: LLM 程序提取器
- EpisodicLinker: Episodic 链接验证器
- CharacterResolver: 角色 ID 解析器
- ProcedureMatcher: Procedure 匹配器
"""

from .builder import NSTFBuilder
from .incremental_builder import IncrementalNSTFBuilder
from .dag_fusion import DAGFusion, ProcedureFusionManager

__all__ = [
    'NSTFBuilder', 
    'IncrementalNSTFBuilder', 
    'DAGFusion', 
    'ProcedureFusionManager',
]
