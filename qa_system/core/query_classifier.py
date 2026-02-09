# -*- coding: utf-8 -*-
"""
问题分类器 - 实现论文 4.3.1 Query Classification

分类类型:
- factual: 事实问题 (who, what, where, when)
- procedural: 程序问题 (how to, steps, procedure)
- constraint: 约束问题 (without X, if no Y, alternative)
- character: 人物理解问题 (does X like, is X good at)

分类策略:
1. Rule-based pre-filter (快速)
2. LLM-based refinement (必要时)
"""

import re
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    CONSTRAINT = "constraint"
    CHARACTER = "character"


@dataclass
class ClassificationResult:
    """分类结果"""
    query_type: QueryType
    confidence: float  # 0-1
    method: str  # "rule" or "llm"
    matched_pattern: Optional[str] = None


class QueryClassifier:
    """
    问题分类器
    
    遵循论文 4.3.1 的两阶段分类:
    1. Rule-based pre-filter
    2. LLM-based classifier (可选)
    """
    
    # ========== 规则模式定义 ==========
    
    # Constraint 模式（最高优先级）
    CONSTRAINT_PATTERNS = [
        (r'\bwithout\s+\w+', 'without_X'),
        (r'\bif\s+(?:there\s+is\s+)?no\s+\w+', 'if_no_X'),
        (r'\balternative\b', 'alternative'),
        (r'\bmissing\b', 'missing'),
        (r'\binstead\s+of\b', 'instead_of'),
        (r'\bexcept\b', 'except'),
        (r'\bother\s+than\b', 'other_than'),
        (r'如果没有', 'zh_if_no'),
        (r'替代', 'zh_alternative'),
        (r'不[用使]', 'zh_without'),
    ]
    
    # Procedural 模式
    PROCEDURAL_PATTERNS = [
        (r'\bhow\s+(?:to|do|does|should|can|could)\b', 'how_to'),
        (r'\bsteps?\b', 'steps'),
        (r'\bprocedure\b', 'procedure'),
        (r'\bprocess\b', 'process'),
        (r'\bwhat\s+to\s+do\b', 'what_to_do'),
        (r'\bin\s+what\s+order\b', 'in_order'),
        (r'\bfirst.*then\b', 'first_then'),
        (r'怎么做', 'zh_how_to'),
        (r'步骤', 'zh_steps'),
        (r'流程', 'zh_process'),
    ]
    
    # Character 模式
    CHARACTER_PATTERNS = [
        (r'\b(?:usually|often|always|frequently)\b', 'usually'),
        (r'\bhabit\b', 'habit'),
        (r'\btend\s+to\b', 'tend_to'),
        (r'\b(?:good|skilled|familiar)\s+(?:at|with)\b', 'good_at'),
        (r'\bdoes\s+\w+\s+like\b', 'does_X_like'),
        (r'\bis\s+\w+\s+(?:good|skilled)\b', 'is_X_good'),
        (r'\bpersonality\b', 'personality'),
        (r'\bbehavior\b', 'behavior'),
        (r'习惯', 'zh_habit'),
        (r'擅长', 'zh_good_at'),
        (r'喜欢', 'zh_like'),
        (r'经常', 'zh_often'),
    ]
    
    def __init__(
        self,
        use_llm_refinement: bool = False,
        llm_client=None,
        confidence_threshold: float = 0.7,
    ):
        """
        Args:
            use_llm_refinement: 是否启用 LLM 精细分类
            llm_client: LLM 客户端实例
            confidence_threshold: 规则分类置信度阈值，低于此值触发 LLM
        """
        self.use_llm_refinement = use_llm_refinement
        self.llm_client = llm_client
        self.confidence_threshold = confidence_threshold
    
    def classify(self, query: str) -> ClassificationResult:
        """
        分类问题类型
        
        Returns:
            ClassificationResult 包含类型、置信度和方法
        """
        # Stage 1: Rule-based pre-filter
        rule_result = self._rule_based_classify(query)
        
        # 如果置信度足够高，直接返回
        if rule_result.confidence >= self.confidence_threshold:
            return rule_result
        
        # Stage 2: LLM-based refinement (可选)
        if self.use_llm_refinement and self.llm_client:
            return self._llm_based_classify(query, rule_result)
        
        return rule_result
    
    def _rule_based_classify(self, query: str) -> ClassificationResult:
        """规则分类"""
        query_lower = query.lower()
        
        # 检查 Constraint（最高优先级）
        for pattern, name in self.CONSTRAINT_PATTERNS:
            if re.search(pattern, query_lower):
                return ClassificationResult(
                    query_type=QueryType.CONSTRAINT,
                    confidence=0.9,
                    method="rule",
                    matched_pattern=name,
                )
        
        # 检查 Procedural
        for pattern, name in self.PROCEDURAL_PATTERNS:
            if re.search(pattern, query_lower):
                return ClassificationResult(
                    query_type=QueryType.PROCEDURAL,
                    confidence=0.85,
                    method="rule",
                    matched_pattern=name,
                )
        
        # 检查 Character
        for pattern, name in self.CHARACTER_PATTERNS:
            if re.search(pattern, query_lower):
                return ClassificationResult(
                    query_type=QueryType.CHARACTER,
                    confidence=0.8,
                    method="rule",
                    matched_pattern=name,
                )
        
        # 默认 Factual
        return ClassificationResult(
            query_type=QueryType.FACTUAL,
            confidence=0.6,  # 默认分类置信度较低
            method="rule",
            matched_pattern="default_factual",
        )
    
    def _llm_based_classify(
        self,
        query: str,
        rule_result: ClassificationResult
    ) -> ClassificationResult:
        """LLM-based refinement (reserved interface)"""
        return rule_result
