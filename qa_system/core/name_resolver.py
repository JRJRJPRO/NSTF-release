# -*- coding: utf-8 -*-
"""
人名解析服务 - 将 ID 映射为真实名称

核心功能:
1. face_X, voice_X → 真实人名（如果有semantic node包含名字）
2. character_X → 真实人名或更友好的标识
3. 支持批量解析和缓存

名称获取优先级:
1. 直接存储的 name 属性
2. 从 semantic node 的 contents 中提取
3. 从 equivalence 节点解析
4. 保留原始 ID 作为 fallback

使用方法:
    resolver = NameResolver(video_graph)
    real_name = resolver.resolve("face_123")  # 返回 "John" 或 "face_123"
    text = resolver.resolve_text(some_text)   # 批量替换文本中的所有 ID
"""

import re
from typing import Dict, List, Optional, Set, Tuple, Any
from .cache_manager import cache


class NameResolver:
    """
    人名解析服务
    
    维护以下映射:
    - face_id -> real_name
    - voice_id -> real_name
    - character_id -> real_name
    """
    
    def __init__(self, video_graph=None, nstf_graph: Dict = None):
        """
        Args:
            video_graph: M3-Agent VideoGraph 实例
            nstf_graph: NSTF 图谱字典
        """
        self.video_graph = video_graph
        self.nstf_graph = nstf_graph
        
        # ID -> 名称映射
        self._name_mapping: Dict[str, str] = {}
        self._initialized = False
    
    def initialize(self):
        """初始化名称映射（延迟加载）"""
        if self._initialized:
            return
        
        # 尝试从缓存加载
        graph_id = self._get_graph_id()
        cached = cache.get_name_mapping(graph_id)
        if cached:
            self._name_mapping = cached
            self._initialized = True
            return
        
        # 从 video_graph 构建映射
        if self.video_graph:
            self._build_from_video_graph()
        
        # 从 nstf_graph 补充映射
        if self.nstf_graph:
            self._build_from_nstf_graph()
        
        # 保存到缓存
        cache.set_name_mapping(graph_id, self._name_mapping)
        self._initialized = True
    
    def _get_graph_id(self) -> str:
        """获取图谱唯一标识"""
        if self.video_graph and hasattr(self.video_graph, 'video_id'):
            return str(self.video_graph.video_id)
        return "default"
    
    def _build_from_video_graph(self):
        """从 video_graph 构建名称映射"""
        graph = self.video_graph
        
        # 1. 从 character_mappings 获取基础映射
        if hasattr(graph, 'character_mappings'):
            for char_id, tags in graph.character_mappings.items():
                # char_id: "character_0", tags: ["face_123", "voice_456"]
                # 尝试为每个 tag 找到名称
                for tag in tags:
                    self._name_mapping[tag] = char_id  # 默认映射
        
        if hasattr(graph, 'reverse_character_mappings'):
            # face_X/voice_X -> character_X 的映射
            for tag, char_id in graph.reverse_character_mappings.items():
                if tag not in self._name_mapping:
                    self._name_mapping[tag] = char_id
        
        # 2. 从 semantic nodes 提取真实名称
        if hasattr(graph, 'nodes'):
            for node_id, node in graph.nodes.items():
                if not hasattr(node, 'type') or node.type != 'semantic':
                    continue
                
                contents = node.metadata.get('contents', []) if hasattr(node, 'metadata') else []
                for content in contents:
                    if not isinstance(content, str):
                        continue
                    
                    # 解析 equivalence 语句: "equivalence: face_123 is John"
                    equiv_match = re.match(
                        r'equivalence[:\s]+(\w+_\d+)\s+is\s+(\w+)',
                        content, re.IGNORECASE
                    )
                    if equiv_match:
                        entity_id = equiv_match.group(1)
                        real_name = equiv_match.group(2)
                        self._name_mapping[entity_id] = real_name
                        
                        # 同时更新对应的 character
                        if hasattr(graph, 'reverse_character_mappings'):
                            char_id = graph.reverse_character_mappings.get(entity_id)
                            if char_id:
                                self._name_mapping[char_id] = real_name
                    
                    # 解析其他名称模式: "face_123's name is John"
                    name_match = re.match(
                        r"(\w+_\d+)'s?\s+name\s+is\s+(\w+)",
                        content, re.IGNORECASE
                    )
                    if name_match:
                        entity_id = name_match.group(1)
                        real_name = name_match.group(2)
                        self._name_mapping[entity_id] = real_name
    
    def _build_from_nstf_graph(self):
        """从 nstf_graph 补充名称映射"""
        if not self.nstf_graph:
            return
        
        # 从 entity_nodes 获取名称
        entity_nodes = self.nstf_graph.get('entity_nodes', {})
        for entity_id, entity_data in entity_nodes.items():
            if isinstance(entity_data, dict):
                name = entity_data.get('name') or entity_data.get('label')
                if name and entity_id not in self._name_mapping:
                    self._name_mapping[entity_id] = name
        
        # 从 character_map 获取名称
        char_map = self.nstf_graph.get('character_map', {})
        for char_id, char_info in char_map.items():
            if isinstance(char_info, dict):
                name = char_info.get('name') or char_info.get('display_name')
                if name:
                    self._name_mapping[char_id] = name
    
    def resolve(self, entity_id: str) -> str:
        """
        解析单个 ID 为名称
        
        Args:
            entity_id: face_X, voice_X, character_X 等
            
        Returns:
            真实名称或原始 ID
        """
        self.initialize()
        return self._name_mapping.get(entity_id, entity_id)
    
    def resolve_batch(self, entity_ids: List[str]) -> Dict[str, str]:
        """批量解析 ID"""
        self.initialize()
        return {eid: self.resolve(eid) for eid in entity_ids}
    
    def resolve_text(self, text: str) -> str:
        """
        替换文本中所有的 ID 为真实名称
        
        策略:
        - 如果有真实人名映射，则替换
        - 如果没有，保留原始标识符（character_X）
        - 将 person_X 统一转换为 character_X 格式（保持一致性）
        
        Args:
            text: 包含 face_X, voice_X, character_X, person_X 的文本
            
        Returns:
            替换后的文本
        """
        self.initialize()
        
        # 匹配所有 ID 模式（包括 person_X 和带尖括号的格式）
        pattern = r'<?\b(face_\d+|voice_\d+|character_\d+|person_\d+)\b>?'
        
        def replacer(match):
            entity_id = match.group(1)
            
            # 1. 检查是否有真实人名映射
            resolved = self._name_mapping.get(entity_id)
            if resolved and not resolved.startswith(('character_', 'person_', 'face_', 'voice_')):
                # 有真实人名，使用它
                return resolved
            
            # 2. 将 person_X 转换为 character_X（统一格式）
            if entity_id.startswith('person_'):
                idx = entity_id.replace('person_', '')
                return f'character_{idx}'
            
            # 3. 保留原始标识符（去掉尖括号）
            return entity_id
        
        return re.sub(pattern, replacer, text)
    
    def add_mapping(self, entity_id: str, name: str):
        """手动添加映射"""
        self.initialize()
        self._name_mapping[entity_id] = name
        
        # 更新缓存
        graph_id = self._get_graph_id()
        cache.set_name_mapping(graph_id, self._name_mapping)
    
    def get_all_mappings(self) -> Dict[str, str]:
        """获取所有映射"""
        self.initialize()
        return dict(self._name_mapping)
    
    def get_character_name(self, character_id: str) -> str:
        """
        获取 character 的名称，优先返回真实名称
        
        如果没有真实名称，返回格式化的标识如 "Person 1"
        """
        self.initialize()
        
        name = self._name_mapping.get(character_id)
        if name and not name.startswith('character_'):
            return name
        
        # 生成友好名称
        if character_id.startswith('character_'):
            idx = character_id.replace('character_', '')
            try:
                return f"Person {int(idx) + 1}"
            except ValueError:
                pass
        
        return character_id
    
    def extract_entities_from_query(self, query: str) -> List[str]:
        """
        从查询中提取所有实体 ID
        
        Returns:
            实体 ID 列表
        """
        pattern = r'\b(face_\d+|voice_\d+|character_\d+)\b'
        matches = re.findall(pattern, query)
        return list(set(matches))


def create_resolver(video_graph=None, nstf_graph: Dict = None) -> NameResolver:
    """
    工厂函数：创建 NameResolver 实例
    
    Args:
        video_graph: VideoGraph 实例
        nstf_graph: NSTF 图谱
        
    Returns:
        NameResolver 实例
    """
    resolver = NameResolver(video_graph, nstf_graph)
    resolver.initialize()
    return resolver
