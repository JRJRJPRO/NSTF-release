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
    """Query classification result."""
    query_type: QueryType
    confidence: float
    method: str
    matched_pattern: Optional[str] = None


class QueryClassifier:
    """Rule-based query classifier with optional LLM refinement."""

    CONSTRAINT_PATTERNS = [
        (r'\bwithout\s+\w+', 'without_X'),
        (r'\bif\s+(?:there\s+is\s+)?no\s+\w+', 'if_no_X'),
        (r'\balternative\b', 'alternative'),
        (r'\bmissing\b', 'missing'),
        (r'\binstead\s+of\b', 'instead_of'),
        (r'\bexcept\b', 'except'),
        (r'\bother\s+than\b', 'other_than'),
    ]

    PROCEDURAL_PATTERNS = [
        (r'\bhow\s+(?:to|do|does|should|can|could)\b', 'how_to'),
        (r'\bsteps?\b', 'steps'),
        (r'\bprocedure\b', 'procedure'),
        (r'\bprocess\b', 'process'),
        (r'\bwhat\s+to\s+do\b', 'what_to_do'),
        (r'\bin\s+what\s+order\b', 'in_order'),
        (r'\bfirst.*then\b', 'first_then'),
    ]

    CHARACTER_PATTERNS = [
        (r'\b(?:usually|often|always|frequently)\b', 'usually'),
        (r'\bhabit\b', 'habit'),
        (r'\btend\s+to\b', 'tend_to'),
        (r'\b(?:good|skilled|familiar)\s+(?:at|with)\b', 'good_at'),
        (r'\bdoes\s+\w+\s+like\b', 'does_X_like'),
        (r'\bis\s+\w+\s+(?:good|skilled)\b', 'is_X_good'),
        (r'\bpersonality\b', 'personality'),
        (r'\bbehavior\b', 'behavior'),
    ]

    def __init__(
        self,
        use_llm_refinement: bool = False,
        llm_client=None,
        confidence_threshold: float = 0.7,
    ):
        self.use_llm_refinement = use_llm_refinement
        self.llm_client = llm_client
        self.confidence_threshold = confidence_threshold

    def classify(self, query: str) -> ClassificationResult:
        """Classify query into factual/constraint/procedural/character types."""
        rule_result = self._rule_based_classify(query)

        if rule_result.confidence >= self.confidence_threshold:
            return rule_result

        if self.use_llm_refinement and self.llm_client:
            return self._llm_based_classify(query, rule_result)

        return rule_result

    def _rule_based_classify(self, query: str) -> ClassificationResult:
        """Rule-based classification via pattern matching."""
        query_lower = query.lower()

        for pattern, name in self.CONSTRAINT_PATTERNS:
            if re.search(pattern, query_lower):
                return ClassificationResult(
                    query_type=QueryType.CONSTRAINT,
                    confidence=0.9,
                    method="rule",
                    matched_pattern=name,
                )

        for pattern, name in self.PROCEDURAL_PATTERNS:
            if re.search(pattern, query_lower):
                return ClassificationResult(
                    query_type=QueryType.PROCEDURAL,
                    confidence=0.85,
                    method="rule",
                    matched_pattern=name,
                )

        for pattern, name in self.CHARACTER_PATTERNS:
            if re.search(pattern, query_lower):
                return ClassificationResult(
                    query_type=QueryType.CHARACTER,
                    confidence=0.8,
                    method="rule",
                    matched_pattern=name,
                )

        return ClassificationResult(
            query_type=QueryType.FACTUAL,
            confidence=0.6,
            method="rule",
            matched_pattern="default_factual",
        )

    def _llm_based_classify(
        self,
        query: str,
        rule_result: ClassificationResult
    ) -> ClassificationResult:
        """LLM-based refinement (reserved interface)."""
        return rule_result
