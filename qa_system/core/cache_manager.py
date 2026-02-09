# -*- coding: utf-8 -*-
"""
统一缓存管理器

解决问题:
1. 多个检索器重复缓存相同数据
2. 缓存不一致导致的潜在 bug
3. 内存管理困难
"""

import pickle
from typing import Dict, Any, Optional
from pathlib import Path


class CacheManager:
    """
    全局单例缓存管理器
    
    管理的缓存类型:
    - video_graph: 视频记忆图谱
    - nstf_graph: NSTF 逻辑图谱
    - embeddings: Procedure embeddings
    - name_mapping: 人名映射表
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_cache()
        return cls._instance
    
    def _init_cache(self):
        """初始化缓存存储"""
        self._video_graph_cache: Dict[str, Any] = {}
        self._nstf_graph_cache: Dict[str, Any] = {}
        self._embedding_cache: Dict[str, Dict] = {}
        self._name_mapping_cache: Dict[str, Dict[str, str]] = {}
        
        # 统计信息
        self._stats = {
            'video_graph_hits': 0,
            'video_graph_misses': 0,
            'nstf_graph_hits': 0,
            'nstf_graph_misses': 0,
        }
    
    # ========== Video Graph ==========
    
    def get_video_graph(self, mem_path: str, loader_func=None):
        """获取视频图谱（带缓存）"""
        if mem_path in self._video_graph_cache:
            self._stats['video_graph_hits'] += 1
            return self._video_graph_cache[mem_path]
        
        self._stats['video_graph_misses'] += 1
        
        if loader_func is None:
            from mmagent.utils.general import load_video_graph
            loader_func = load_video_graph
        
        graph = loader_func(mem_path)
        self._video_graph_cache[mem_path] = graph
        return graph
    
    # ========== NSTF Graph ==========
    
    def get_nstf_graph(self, nstf_path: str, loader_func=None) -> Optional[Dict]:
        """获取 NSTF 图谱（带缓存）"""
        if nstf_path is None:
            return None
        
        if nstf_path in self._nstf_graph_cache:
            self._stats['nstf_graph_hits'] += 1
            return self._nstf_graph_cache[nstf_path]
        
        self._stats['nstf_graph_misses'] += 1
        
        try:
            if loader_func:
                graph = loader_func(nstf_path)
            else:
                with open(nstf_path, 'rb') as f:
                    graph = pickle.load(f)
            self._nstf_graph_cache[nstf_path] = graph
            return graph
        except Exception as e:
            print(f"⚠️ 加载 NSTF 图谱失败 ({nstf_path}): {e}")
            self._nstf_graph_cache[nstf_path] = None
            return None
    
    # ========== Embeddings ==========
    
    def get_embeddings(self, nstf_path: str) -> Optional[Dict]:
        """获取 Procedure embeddings（带缓存）"""
        return self._embedding_cache.get(nstf_path)
    
    def set_embeddings(self, nstf_path: str, embeddings: Dict):
        """设置 Procedure embeddings"""
        self._embedding_cache[nstf_path] = embeddings
    
    # ========== Name Mapping ==========
    
    def get_name_mapping(self, mem_path: str) -> Optional[Dict[str, str]]:
        """获取人名映射表"""
        return self._name_mapping_cache.get(mem_path)
    
    def set_name_mapping(self, mem_path: str, mapping: Dict[str, str]):
        """设置人名映射表"""
        self._name_mapping_cache[mem_path] = mapping
    
    # ========== 管理操作 ==========
    
    def clear_all(self):
        """清除所有缓存"""
        self._video_graph_cache.clear()
        self._nstf_graph_cache.clear()
        self._embedding_cache.clear()
        self._name_mapping_cache.clear()
        # 重置统计
        for key in self._stats:
            self._stats[key] = 0
    
    def clear_video(self, mem_path: str):
        """清除指定视频的缓存"""
        self._video_graph_cache.pop(mem_path, None)
        self._name_mapping_cache.pop(mem_path, None)
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            **self._stats,
            'video_graph_cached': len(self._video_graph_cache),
            'nstf_graph_cached': len(self._nstf_graph_cache),
            'embeddings_cached': len(self._embedding_cache),
            'name_mapping_cached': len(self._name_mapping_cache),
        }


# 全局单例
cache = CacheManager()
