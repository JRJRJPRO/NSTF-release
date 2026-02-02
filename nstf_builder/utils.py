"""
NSTF Builder 公共工具函数

提供跨组件共享的 embedding 缓存和计算功能
所有组件（EpisodicLinker, ProcedureMatcher, NSTFRetrieverV2）都应使用这些函数
"""

from typing import List, Dict, Optional
import numpy as np

# 全局缓存，跨组件共享
_embedding_cache: Dict[str, np.ndarray] = {}


def get_normalized_embedding(text: str, use_cache: bool = True) -> np.ndarray:
    """
    获取归一化的 embedding（带缓存）
    
    所有组件（EpisodicLinker, ProcedureMatcher, NSTFRetrieverV2）
    都应该使用这个函数，避免重复计算和重复 import
    
    Args:
        text: 要计算 embedding 的文本
        use_cache: 是否使用缓存（默认 True）
    
    Returns:
        归一化后的 embedding 向量
    """
    if use_cache and text in _embedding_cache:
        return _embedding_cache[text]
    
    from mmagent.utils.chat_api import parallel_get_embedding
    embs, _ = parallel_get_embedding("text-embedding-3-large", [text])
    vec = np.array(embs[0])
    normalized = vec / (np.linalg.norm(vec) + 1e-8)
    
    if use_cache:
        _embedding_cache[text] = normalized
    return normalized


def batch_get_normalized_embeddings(texts: List[str], use_cache: bool = True) -> List[np.ndarray]:
    """
    批量获取归一化的 embeddings
    
    优先从缓存获取，只对未缓存的调用 API
    
    Args:
        texts: 要计算 embedding 的文本列表
        use_cache: 是否使用缓存（默认 True）
    
    Returns:
        归一化后的 embedding 向量列表
    """
    results: List[Optional[np.ndarray]] = [None] * len(texts)
    texts_to_fetch: List[str] = []
    indices_to_fetch: List[int] = []
    
    for i, text in enumerate(texts):
        if use_cache and text in _embedding_cache:
            results[i] = _embedding_cache[text]
        else:
            texts_to_fetch.append(text)
            indices_to_fetch.append(i)
    
    if texts_to_fetch:
        from mmagent.utils.chat_api import parallel_get_embedding
        embs, _ = parallel_get_embedding("text-embedding-3-large", texts_to_fetch)
        for idx, text, emb in zip(indices_to_fetch, texts_to_fetch, embs):
            vec = np.array(emb)
            normalized = vec / (np.linalg.norm(vec) + 1e-8)
            if use_cache:
                _embedding_cache[text] = normalized
            results[idx] = normalized
    
    return results


def clear_embedding_cache():
    """清空缓存（测试或内存管理时使用）"""
    global _embedding_cache
    _embedding_cache = {}


def get_cache_stats() -> Dict:
    """获取缓存统计信息"""
    return {
        'cached_embeddings': len(_embedding_cache),
        'memory_estimate_mb': len(_embedding_cache) * 3072 * 8 / (1024 * 1024)  # text-embedding-3-large = 3072 dim
    }


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算余弦相似度（假设向量已归一化）"""
    return float(np.dot(vec1, vec2))
