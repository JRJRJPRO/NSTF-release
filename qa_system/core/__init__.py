# -*- coding: utf-8 -*-
"""
核心模块

包含:
- Retriever: 原始检索器（兼容旧版）
- HybridRetriever: 混合检索器（论文 4.3 实现）
- Evaluator: 评估器
- LLMClient: LLM 客户端
- CacheManager: 缓存管理器
- QueryClassifier: 问题分类器
- NameResolver: 人名解析器
- SymbolicFunctions: Symbolic 函数封装
"""

from .retriever import Retriever
from .evaluator import Evaluator
from .llm_client import LLMClient
from .cache_manager import cache, CacheManager
from .query_classifier import QueryClassifier, QueryType, ClassificationResult
from .name_resolver import NameResolver, create_resolver
from .symbolic_functions import SymbolicFunctions, ProcedureDAG
from .hybrid_retriever import HybridRetriever, create_retriever, RetrievalResult

__all__ = [
    # 核心组件
    'Retriever',
    'HybridRetriever',
    'Evaluator', 
    'LLMClient',
    # 新增组件
    'cache',
    'CacheManager',
    'QueryClassifier',
    'QueryType',
    'ClassificationResult',
    'NameResolver',
    'create_resolver',
    'SymbolicFunctions',
    'ProcedureDAG',
    'create_retriever',
    'RetrievalResult',
]
