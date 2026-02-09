"""
Character ID 解析器 V2

将 <face_N>、<voice_N>、<character_N> 格式的 ID 替换为统一标识或真实名字
支持多种方法 fallback: metadata → semantic equivalence → 保持原样

关键发现：
- robot 数据集使用 <face_N> 和 <voice_N> 格式
- semantic 节点中有 "Equivalence: <face_2>, <voice_0>" 这样的信息
- 这些可以用来建立 face/voice 的对应关系
"""

from typing import Dict, Set
import re


class CharacterResolver:
    """
    Character ID 解析器 V2
    
    支持格式:
    - <character_N>
    - <face_N>
    - <voice_N>
    
    功能:
    1. 从 semantic 节点提取 equivalence 关系 (face ↔ voice)
    2. 将 face/voice ID 统一为 person_N 格式
    3. 如果有真实名字映射，则替换为真实名字
    """
    
    def __init__(self, video_graph, debug: bool = False):
        self.mapping: Dict[str, str] = {}  # ID -> 统一名称
        self.equivalences: Dict[str, Set[str]] = {}  # 等价组
        self.video_graph = video_graph
        self.debug = debug
        self._resolve()
    
    def _resolve(self):
        """解析 character/face/voice 映射"""
        # 方法 1: 从 metadata 获取已有映射
        if hasattr(self.video_graph, 'metadata') and self.video_graph.metadata:
            mapping = self.video_graph.metadata.get('character_mapping', {})
            if mapping:
                self.mapping = mapping
                if self.debug:
                    print(f"CharacterResolver: Found mapping from metadata: {len(mapping)} entries")
                return
        
        # 方法 2: 从 semantic 节点提取 equivalence 关系
        self._extract_equivalences()
        
        # 方法 3: 基于 equivalence 建立统一映射
        self._build_unified_mapping()
        
        if self.debug:
            if self.mapping:
                print(f"CharacterResolver: Built mapping with {len(self.mapping)} entries")
                # 只显示前 5 个
                for i, (k, v) in enumerate(list(self.mapping.items())[:5]):
                    print(f"  {k} -> {v}")
                if len(self.mapping) > 5:
                    print(f"  ... and {len(self.mapping) - 5} more")
            else:
                print("⚠️ CharacterResolver: No mapping found")
    
    def _extract_equivalences(self):
        """从 semantic 节点提取 equivalence 关系"""
        if not hasattr(self.video_graph, 'nodes'):
            return
        
        # 匹配 "Equivalence: <face_2>, <voice_0>" 格式
        equiv_pattern = re.compile(r'Equivalence:\s*(<[^>]+>)\s*,\s*(<[^>]+>)')
        
        for node_id, node in self.video_graph.nodes.items():
            node_type = getattr(node, 'type', None)
            if node_type != 'semantic':
                continue
            
            metadata = getattr(node, 'metadata', {})
            if not metadata:
                continue
            
            contents = metadata.get('contents', [])
            for content in contents:
                match = equiv_pattern.search(content)
                if match:
                    id1, id2 = match.group(1), match.group(2)
                    self._add_equivalence(id1, id2)
    
    def _add_equivalence(self, id1: str, id2: str):
        """添加等价关系"""
        group1 = self._find_equivalence_group(id1)
        group2 = self._find_equivalence_group(id2)
        
        if group1 is None and group2 is None:
            new_group = {id1, id2}
            self.equivalences[id1] = new_group
            self.equivalences[id2] = new_group
        elif group1 is None:
            group2.add(id1)
            self.equivalences[id1] = group2
        elif group2 is None:
            group1.add(id2)
            self.equivalences[id2] = group1
        elif group1 is not group2:
            merged = group1 | group2
            for id_ in merged:
                self.equivalences[id_] = merged
    
    def _find_equivalence_group(self, id_: str) -> Set[str]:
        """找到 ID 所属的等价组"""
        return self.equivalences.get(id_)
    
    def _build_unified_mapping(self):
        """基于 equivalence 建立统一映射"""
        all_ids = set()
        
        for id_ in self.equivalences.keys():
            all_ids.add(id_)
        
        # 从 episodic 内容中收集所有 ID（不限制数量）
        id_pattern = re.compile(r'<(face|voice|character)_(\d+)>')
        
        if hasattr(self.video_graph, 'text_nodes_by_clip'):
            for clip_id in self.video_graph.text_nodes_by_clip.keys():
                node_ids = self.video_graph.text_nodes_by_clip[clip_id]
                for nid in node_ids:
                    node = self.video_graph.nodes.get(nid)
                    if node:
                        meta = getattr(node, 'metadata', {})
                        contents = meta.get('contents', [])
                        for c in contents:
                            matches = id_pattern.findall(c)
                            for prefix, num in matches:
                                all_ids.add(f'<{prefix}_{num}>')
        
        # 为每个等价组分配统一的 person ID
        processed_groups = set()
        person_counter = 1
        
        for id_ in all_ids:
            if id_ in self.mapping:
                continue
            
            group = self._find_equivalence_group(id_)
            if group:
                group_key = frozenset(group)
                if group_key in processed_groups:
                    continue
                processed_groups.add(group_key)
                
                unified_name = f"person_{person_counter}"
                person_counter += 1
                
                for member in group:
                    self.mapping[member] = unified_name
            else:
                self.mapping[id_] = f"person_{person_counter}"
                person_counter += 1
    
    def resolve(self, content: str) -> str:
        """将内容中的 face/voice/character ID 替换为统一名称"""
        if not self.mapping:
            return content
        
        result = content
        for id_, name in self.mapping.items():
            if id_ in result:
                result = result.replace(id_, name)
        
        return result
    
    def get_mapping_context(self) -> str:
        """生成映射上下文字符串"""
        if not self.mapping:
            return ""
        
        by_person = {}
        for id_, person in self.mapping.items():
            if person not in by_person:
                by_person[person] = []
            by_person[person].append(id_)
        
        parts = []
        for person, ids in by_person.items():
            if len(ids) > 1:
                parts.append(f"{person}={','.join(sorted(ids))}")
        
        if parts:
            return "Person Equivalences: " + "; ".join(parts)
        return ""
    
    def has_unresolved_ids(self, content: str) -> bool:
        """检查内容中是否还有未解析的 ID"""
        pattern = r'<(face|voice|character)[_\s]?\d+>'
        return bool(re.search(pattern, content, re.IGNORECASE))
    
    def get_unresolved_ids(self, content: str) -> list:
        """获取内容中所有未解析的 ID"""
        pattern = r'<(face|voice|character)[_\s]?\d+>'
        return re.findall(pattern, content, re.IGNORECASE)


def create_character_resolver(video_graph, debug: bool = False) -> CharacterResolver:
    """工厂函数"""
    return CharacterResolver(video_graph, debug=debug)
