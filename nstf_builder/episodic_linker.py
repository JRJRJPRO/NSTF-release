"""
EpisodicLinker - episodic 链接器

V2.2.2 实现：
- 验证 LLM 指定的链接（verify_threshold）
- 自动发现遗漏的链接（discover_threshold）
- embedding 缓存避免重复计算

核心功能：
1. 对每个 Procedure，计算与所有 clip 内容的向量相似度
2. 高相似度的 clip 被链接到该 Procedure
3. 支持批量 embedding 计算
"""

from typing import Dict, List, Set, Optional
import numpy as np
from .utils import get_normalized_embedding, batch_get_normalized_embeddings


class EpisodicLinker:
    """
    增强的 episodic 链接器
    
    双重来源:
    1. LLM 指定的链接 → 向量验证
    2. 向量自动发现 → 补充遗漏
    
    优化: 使用 embedding 缓存避免重复计算
    """
    
    def __init__(
        self, 
        verify_threshold: float = 0.35,   # 验证 LLM 指定链接（从高开始）
        discover_threshold: float = 0.50,  # 自动发现链接
        max_links_per_proc: int = 10,      # 每个 Procedure 最多链接数
        debug: bool = False
    ):
        self.verify_threshold = verify_threshold
        self.discover_threshold = discover_threshold
        self.max_links_per_proc = max_links_per_proc
        self.debug = debug
        self._content_emb_cache: Dict[int, np.ndarray] = {}  # clip_id -> embedding
    
    def _ensure_content_embeddings(self, all_episodic_contents: List[Dict]):
        """批量预计算所有 content 的 embedding（只计算一次）"""
        if self._content_emb_cache:
            return  # 已有缓存
        
        # 收集需要计算的文本
        texts = []
        clip_ids = []
        for item in all_episodic_contents:
            clip_id = item['clip_id']
            content = item.get('content', '')
            if content and clip_id not in self._content_emb_cache:
                texts.append(content)
                clip_ids.append(clip_id)
        
        if not texts:
            return
        
        if self.debug:
            print(f"  EpisodicLinker: 批量计算 {len(texts)} 个 content embeddings...")
        
        # 批量计算
        all_embs = batch_get_normalized_embeddings(texts)
        
        for clip_id, emb in zip(clip_ids, all_embs):
            self._content_emb_cache[clip_id] = emb
        
        if self.debug:
            print(f"  EpisodicLinker: 缓存了 {len(self._content_emb_cache)} 个 embeddings")
    
    def build_verified_links(
        self,
        procedure: Dict,
        all_episodic_contents: List[Dict],
    ) -> List[Dict]:
        """
        构建经过验证的 episodic_links
        
        Args:
            procedure: Procedure 结构，包含 goal, description, source_clips 等
            all_episodic_contents: 所有 clip 的 episodic 内容列表
        
        Returns:
            验证过的 episodic_links 列表
        """
        links = []
        
        # 获取 LLM 指定的 source_clips（如果有）
        llm_clips = set()
        for clip in procedure.get('source_clips', []):
            if isinstance(clip, int):
                llm_clips.add(clip)
            elif isinstance(clip, str):
                # 尝试提取数字
                import re
                match = re.search(r'(\d+)', clip)
                if match:
                    llm_clips.add(int(match.group(1)))
        
        # 1. 确保 content embeddings 已缓存
        self._ensure_content_embeddings(all_episodic_contents)
        
        # 2. 计算 Procedure embedding
        goal = procedure.get('goal', '')
        description = procedure.get('description', '')
        proc_text = f"{goal}. {description}"
        proc_emb = get_normalized_embedding(proc_text)
        
        if proc_emb is None:
            if self.debug:
                print(f"  ⚠️ 无法计算 Procedure embedding")
            return links
        
        # 3. 计算与每个 clip 的相似度
        rejected_count = 0
        discovered_count = 0
        verified_count = 0
        
        candidates = []
        
        for item in all_episodic_contents:
            clip_id = item['clip_id']
            content = item.get('content', '')
            
            if not content:
                continue
            
            # 获取缓存的 embedding
            content_emb = self._content_emb_cache.get(clip_id)
            if content_emb is None:
                continue
            
            # 计算相似度
            sim = float(np.dot(proc_emb, content_emb))
            
            if clip_id in llm_clips:
                # LLM 指定的链接 - 验证
                if sim >= self.verify_threshold:
                    candidates.append({
                        'clip_id': clip_id,
                        'relevance': 'source',
                        'similarity': round(sim, 4),
                        'content_preview': content[:100] if content else None
                    })
                    verified_count += 1
                else:
                    rejected_count += 1
                    if self.debug:
                        print(f"    ⚠️ Rejected LLM link: clip_{clip_id} (sim={sim:.3f} < {self.verify_threshold})")
            
            elif sim >= self.discover_threshold:
                # 自动发现
                candidates.append({
                    'clip_id': clip_id,
                    'relevance': 'discovered',
                    'similarity': round(sim, 4),
                    'content_preview': content[:100] if content else None
                })
                discovered_count += 1
        
        # 4. 按相似度排序，取 top N
        candidates.sort(key=lambda x: x['similarity'], reverse=True)
        links = candidates[:self.max_links_per_proc]
        
        if self.debug:
            print(f"    Links: {len(links)} (verified: {verified_count}, "
                  f"discovered: {discovered_count}, rejected: {rejected_count})")
        
        return links
    
    def clear_cache(self):
        """清除 embedding 缓存"""
        self._content_emb_cache.clear()


def create_episodic_linker(
    verify_threshold: float = 0.35,
    discover_threshold: float = 0.50,
    debug: bool = False
) -> EpisodicLinker:
    """工厂函数"""
    return EpisodicLinker(
        verify_threshold=verify_threshold,
        discover_threshold=discover_threshold,
        debug=debug
    )
