# -*- coding: utf-8 -*-
"""
检索模块

支持三种检索模式:
1. Baseline: 原始M3-Agent向量检索
2. NSTF: 完整NSTF增强检索
3. 消融模式: prototype(纯向量) / structure(有结构无推理)
"""

import os
import re
import sys
import pickle
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# 统一环境设置（路径、videograph修复等）
from env_setup import setup_all
setup_all()

from mmagent.retrieve import search
from mmagent.utils.general import load_video_graph

# NSTF相关导入
try:
    from neural_symbolic_experiments.nstf.nstf_retrieve import search_with_nstf
    from neural_symbolic_experiments.ablation.ablation_retrieve import search_ablation
    NSTF_AVAILABLE = True
except ImportError:
    NSTF_AVAILABLE = False
    print("⚠️ NSTF模块未找到，仅支持Baseline检索")


def contains_entity_id(content: str) -> bool:
    """
    检测查询内容中是否包含实体ID格式
    
    与原始 M3-Agent 一致，只检查 "character id" (区分大小写)
    """
    if "character id" in content:
        return True
    return False


class Retriever:
    """检索器 - 统一管理各种检索模式"""
    
    def __init__(
        self,
        ablation_mode: Optional[str] = None,
        threshold: float = 0.05,
        threshold_baseline: float = 0.5,
        topk: int = 10,
    ):
        """
        Args:
            ablation_mode: 消融模式 (None/baseline/prototype/structure)
            threshold: NSTF模式相似度阈值
            threshold_baseline: Baseline模式相似度阈值
            topk: 检索数量
        """
        self.ablation_mode = ablation_mode
        self.threshold = threshold
        self.threshold_baseline = threshold_baseline
        self.topk = topk
        
        # 缓存加载的图谱
        self._graph_cache: Dict[str, Any] = {}
        self._nstf_cache: Dict[str, Any] = {}
    
    def load_video_graph(self, mem_path: str) -> Any:
        """加载视频图谱（带缓存）"""
        if mem_path not in self._graph_cache:
            self._graph_cache[mem_path] = load_video_graph(mem_path)
        return self._graph_cache[mem_path]
    
    def load_nstf_graph(self, nstf_path: str) -> Optional[Any]:
        """加载NSTF图谱（带缓存）"""
        if not NSTF_AVAILABLE:
            return None
        
        if nstf_path not in self._nstf_cache:
            if os.path.exists(nstf_path):
                try:
                    with open(nstf_path, 'rb') as f:
                        self._nstf_cache[nstf_path] = pickle.load(f)
                except Exception as e:
                    print(f"  ⚠️ 加载NSTF图谱失败: {e}")
                    self._nstf_cache[nstf_path] = None
            else:
                self._nstf_cache[nstf_path] = None
        
        return self._nstf_cache[nstf_path]
    
    def search(
        self,
        mem_path: str,
        query: str,
        current_clips: List = None,
        nstf_path: Optional[str] = None,
        before_clip: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], List, Optional[str]]:
        """
        执行检索
        
        Args:
            mem_path: 视频图谱路径
            query: 查询文本
            current_clips: 当前已检索的clips
            nstf_path: NSTF图谱路径（可选）
            before_clip: 时间截断点（可选）
            
        Returns:
            (memories, updated_clips, nstf_info)
        """
        if current_clips is None:
            current_clips = []
        
        # 加载图谱
        mem_node = self.load_video_graph(mem_path)
        if before_clip is not None:
            mem_node.truncate_memory_by_clip(before_clip, False)
        mem_node.refresh_equivalences()
        
        new_memories = {}
        nstf_info = None
        
        # 实体ID查询特殊处理
        if contains_entity_id(query):
            memories, _, _ = search(
                mem_node, query, [], 
                mem_wise=True, topk=20, 
                before_clip=before_clip
            )
            return memories, current_clips, None
        
        # 加载NSTF图谱
        nstf_graph = None
        if nstf_path:
            nstf_graph = self.load_nstf_graph(nstf_path)
        
        # 根据消融模式选择检索策略
        if self.ablation_mode == 'baseline':
            # 消融A: 纯Baseline
            memories, current_clips, _ = search(
                mem_node, query, current_clips,
                threshold=self.threshold_baseline,
                topk=self.topk,
                before_clip=before_clip
            )
            new_memories.update(memories)
            
        elif self.ablation_mode in ['prototype', 'structure'] and nstf_graph is not None:
            # 消融B/C
            memories, current_clips, nstf_info = search_ablation(
                video_graph=mem_node,
                nstf_graph=nstf_graph,
                query=query,
                current_clips=current_clips,
                mode=self.ablation_mode,
                threshold=self.threshold,
                topk=self.topk,
                before_clip=before_clip
            )
            new_memories.update(memories)
            
        elif nstf_graph is not None:
            # 完整NSTF检索
            memories, current_clips, nstf_info = search_with_nstf(
                mem_node, nstf_graph, query,
                current_clips,
                threshold=self.threshold,
                topk=self.topk,
                before_clip=before_clip
            )
            new_memories.update(memories)
            if nstf_info:
                new_memories["NSTF_Procedures"] = nstf_info
                
        else:
            # 无NSTF的默认检索
            memories, current_clips, _ = search(
                mem_node, query, current_clips,
                threshold=self.threshold,
                topk=self.topk,
                before_clip=before_clip
            )
            new_memories.update(memories)
        
        return new_memories, current_clips, nstf_info
    
    def clear_cache(self):
        """清除图谱缓存"""
        self._graph_cache.clear()
        self._nstf_cache.clear()
    
    @property
    def mode_name(self) -> str:
        """当前模式名称"""
        if self.ablation_mode is None:
            return "Full NSTF"
        return f"Ablation-{self.ablation_mode}"
