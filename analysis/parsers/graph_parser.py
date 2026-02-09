"""
图谱解析器 (Graph Parser)

将 pickle 格式的 VideoGraph 解析为人可读的 Markdown 文档。
"""

import os
import pickle
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple


class GraphParser:
    """
    VideoGraph 图谱解析器
    
    将 pkl 文件中的图谱结构解析为 Markdown 文档，
    便于人工阅读和分析。
    """
    
    def __init__(self, base_path: str):
        """
        Args:
            base_path: NSTF_MODEL 根目录的绝对路径
        """
        self.base_path = base_path
        
    def find_graph_file(self, video_id: str) -> Optional[str]:
        """
        查找视频对应的图谱文件
        
        Args:
            video_id: 视频 ID，如 "study_07" 或 "Efk3K4epEzg"
            
        Returns:
            图谱文件的完整路径，未找到返回 None
        """
        # 尝试 robot 目录
        robot_path = os.path.join(self.base_path, "data/memory_graphs/robot", f"{video_id}.pkl")
        if os.path.exists(robot_path):
            return robot_path
            
        # 尝试 web 目录
        web_path = os.path.join(self.base_path, "data/memory_graphs/web", f"{video_id}.pkl")
        if os.path.exists(web_path):
            return web_path
            
        return None
    
    def get_dataset(self, video_id: str) -> Optional[str]:
        """判断视频属于哪个数据集"""
        robot_path = os.path.join(self.base_path, "data/memory_graphs/robot", f"{video_id}.pkl")
        if os.path.exists(robot_path):
            return "robot"
        web_path = os.path.join(self.base_path, "data/memory_graphs/web", f"{video_id}.pkl")
        if os.path.exists(web_path):
            return "web"
        return None
        
    def load_graph(self, graph_path: str) -> Any:
        """
        加载图谱文件
        
        Args:
            graph_path: pkl 文件路径
            
        Returns:
            VideoGraph 对象
            
        Raises:
            FileNotFoundError: 文件不存在
            pickle.UnpicklingError: 反序列化失败
        """
        try:
            with open(graph_path, 'rb') as f:
                return pickle.load(f)
        except ModuleNotFoundError as e:
            print(f"[警告] 模块未找到: {e}")
            print(f"[提示] 请确保在正确的 Python 环境中运行，或检查 mmagent 模块是否在 sys.path 中")
            raise
        except Exception as e:
            print(f"[错误] Pickle 加载失败: {e}")
            raise
    
    def _get_node_type_counts(self, nodes: Dict) -> Dict[str, int]:
        """统计各类型节点数量"""
        counts = defaultdict(int)
        for node_id, node in nodes.items():
            # 适配不同的节点结构
            if hasattr(node, 'type'):
                node_type = node.type
            elif isinstance(node, dict) and 'type' in node:
                node_type = node['type']
            else:
                node_type = 'unknown'
            counts[node_type] += 1
        return dict(counts)
    
    def _get_node_attr(self, node: Any, attr: str, default=None):
        """安全获取节点属性（兼容多种数据结构）"""
        try:
            # 1. 尝试属性访问（普通对象、dataclass）
            if hasattr(node, attr):
                return getattr(node, attr)
            # 2. 尝试 dict 访问
            if isinstance(node, dict):
                return node.get(attr, default)
            # 3. 尝试 namedtuple 访问
            if hasattr(node, '_fields') and attr in node._fields:
                return getattr(node, attr, default)
            # 4. 尝试下标访问
            try:
                return node[attr]
            except (KeyError, TypeError, IndexError):
                pass
        except Exception:
            pass
        return default
    
    def _get_embedding_info(self, embeddings: Any) -> str:
        """获取 embedding 信息（只显示维度）"""
        if embeddings is None:
            return "无"
        
        if isinstance(embeddings, list):
            if len(embeddings) == 0:
                return "无"
            first = embeddings[0]
            if isinstance(first, list):
                return f"{len(first)}维 × {len(embeddings)}个"
            elif hasattr(first, 'shape'):
                return f"{first.shape[-1]}维 × {len(embeddings)}个"
            else:
                return f"{len(embeddings)}维"
        elif hasattr(embeddings, 'shape'):
            return f"{embeddings.shape[-1]}维"
        else:
            return "未知格式"
    
    def _format_contents(self, contents: Any, node_type: str) -> str:
        """格式化节点内容"""
        if contents is None:
            return "(空)"
        
        # 对于 img 和 voice 类型，内容是 Base64，不完整显示
        if node_type in ['img', 'voice']:
            if isinstance(contents, str) and len(contents) > 100:
                return f"[Base64 数据，长度 {len(contents)}]"
        
        # 文本内容完整保留
        return str(contents)
    
    def _group_nodes_by_clip(self, nodes: Dict) -> Dict[str, List[Tuple[int, Any]]]:
        """将节点按 Clip 分组"""
        clip_nodes = defaultdict(list)
        
        for node_id, node in nodes.items():
            metadata = self._get_node_attr(node, 'metadata', {})
            if isinstance(metadata, dict):
                timestamp = metadata.get('timestamp', 'UNKNOWN')
                clip_id = metadata.get('clip_id', timestamp)
            else:
                timestamp = self._get_node_attr(metadata, 'timestamp', 'UNKNOWN')
                clip_id = self._get_node_attr(metadata, 'clip_id', timestamp)
            
            # 标准化 clip 标识
            if isinstance(clip_id, int):
                clip_key = f"CLIP_{clip_id}"
            elif isinstance(clip_id, str) and clip_id.startswith('CLIP_'):
                clip_key = clip_id
            else:
                clip_key = str(clip_id)
                
            clip_nodes[clip_key].append((node_id, node))
        
        return dict(clip_nodes)
    
    def _format_character_mappings(self, graph: Any) -> str:
        """格式化人物映射"""
        lines = []
        
        # 尝试获取 character_mappings
        mappings = None
        if hasattr(graph, 'character_mappings'):
            mappings = graph.character_mappings
        elif hasattr(graph, 'characters'):
            mappings = graph.characters
        elif isinstance(graph, dict):
            mappings = graph.get('character_mappings') or graph.get('characters')
        
        if not mappings:
            return "无人物映射信息"
        
        lines.append("| Character | 关联节点 ID | 节点数量 |")
        lines.append("|-----------|------------|----------|")
        
        for char_id, node_ids in sorted(mappings.items()):
            if isinstance(node_ids, list):
                ids_str = ", ".join(str(nid) for nid in node_ids[:10])
                if len(node_ids) > 10:
                    ids_str += f" ... (+{len(node_ids)-10})"
                count = len(node_ids)
            else:
                ids_str = str(node_ids)
                count = 1
            lines.append(f"| {char_id} | {ids_str} | {count} |")
        
        return "\n".join(lines)
    
    def _format_edges(self, edges: Any, nodes: Dict) -> str:
        """格式化边信息"""
        if not edges:
            return "无边信息"
        
        # 统计边类型
        edge_types = defaultdict(int)
        edge_examples = defaultdict(list)
        
        for edge in edges:
            if isinstance(edge, tuple) and len(edge) >= 2:
                src, tgt = edge[0], edge[1]
                weight = edge[2] if len(edge) > 2 else 1.0
                
                src_type = self._get_node_attr(nodes.get(src), 'type', 'unknown')
                tgt_type = self._get_node_attr(nodes.get(tgt), 'type', 'unknown')
                
                edge_type = f"{src_type} → {tgt_type}"
                edge_types[edge_type] += 1
                
                if len(edge_examples[edge_type]) < 3:
                    edge_examples[edge_type].append(f"Node {src} → Node {tgt} (weight: {weight:.2f})")
        
        lines = ["| 边类型 | 数量 | 示例 |", "|--------|------|------|"]
        for edge_type, count in sorted(edge_types.items(), key=lambda x: -x[1]):
            examples = "; ".join(edge_examples[edge_type])
            lines.append(f"| {edge_type} | {count} | {examples} |")
        
        return "\n".join(lines)
    
    def parse(self, video_id: str, output_dir: str) -> bool:
        """
        解析指定视频的图谱
        
        Args:
            video_id: 视频 ID
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        # 查找图谱文件
        graph_path = self.find_graph_file(video_id)
        if not graph_path:
            print(f"[GraphParser] 未找到视频 {video_id} 的图谱文件")
            return False
        
        dataset = self.get_dataset(video_id)
        
        # 加载图谱
        print(f"[GraphParser] 加载图谱: {graph_path}")
        try:
            graph = self.load_graph(graph_path)
        except Exception as e:
            print(f"[GraphParser] 加载失败: {e}")
            return False
        
        # 获取节点
        if hasattr(graph, 'nodes'):
            nodes = graph.nodes
        elif isinstance(graph, dict) and 'nodes' in graph:
            nodes = graph['nodes']
        else:
            print(f"[GraphParser] 无法识别图谱结构")
            return False
        
        # 获取边
        edges = None
        if hasattr(graph, 'edges'):
            edges = graph.edges
        elif isinstance(graph, dict):
            edges = graph.get('edges')
        
        # 统计
        type_counts = self._get_node_type_counts(nodes)
        total_nodes = sum(type_counts.values())
        total_edges = len(edges) if edges else 0
        
        # 按 Clip 分组
        clip_nodes = self._group_nodes_by_clip(nodes)
        
        # 生成 Markdown
        lines = []
        lines.append(f"# 视频图谱分析: {video_id}")
        lines.append("")
        lines.append(f"**来源**: data/memory_graphs/{dataset}/{video_id}.pkl  ")
        lines.append(f"**解析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 统计表
        lines.append("## 📊 图谱统计")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 总节点数 | {total_nodes} |")
        for node_type, count in sorted(type_counts.items()):
            lines.append(f"| {node_type.capitalize()} 节点 | {count} |")
        lines.append(f"| 总边数 | {total_edges} |")
        lines.append(f"| Clip 数量 | {len(clip_nodes)} |")
        lines.append("")
        
        # 人物映射
        lines.append("## 👥 人物映射 (Character Mappings)")
        lines.append("")
        lines.append(self._format_character_mappings(graph))
        lines.append("")
        
        # Clip 详情
        lines.append("## 📹 Clip 详情")
        lines.append("")
        
        for clip_key in sorted(clip_nodes.keys(), key=lambda x: int(x.split('_')[-1]) if x.split('_')[-1].isdigit() else 0):
            clip_node_list = clip_nodes[clip_key]
            lines.append(f"### {clip_key}")
            lines.append("")
            
            # 按类型分组
            type_groups = defaultdict(list)
            for node_id, node in clip_node_list:
                node_type = self._get_node_attr(node, 'type', 'unknown')
                type_groups[node_type].append((node_id, node))
            
            # Episodic 节点
            if 'episodic' in type_groups:
                lines.append(f"#### Episodic 记忆 ({len(type_groups['episodic'])} 条)")
                lines.append("")
                for i, (node_id, node) in enumerate(type_groups['episodic'], 1):
                    embeddings = self._get_node_attr(node, 'embeddings')
                    emb_info = self._get_embedding_info(embeddings)
                    metadata = self._get_node_attr(node, 'metadata', {})
                    contents = metadata.get('contents', '') if isinstance(metadata, dict) else self._get_node_attr(metadata, 'contents', '')
                    
                    lines.append(f"{i}. **Node {node_id}** [episodic, {emb_info}]")
                    lines.append(f"   > {self._format_contents(contents, 'episodic')}")
                    lines.append("")
            
            # Semantic 节点
            if 'semantic' in type_groups:
                lines.append(f"#### Semantic 记忆 ({len(type_groups['semantic'])} 条)")
                lines.append("")
                for i, (node_id, node) in enumerate(type_groups['semantic'], 1):
                    embeddings = self._get_node_attr(node, 'embeddings')
                    emb_info = self._get_embedding_info(embeddings)
                    metadata = self._get_node_attr(node, 'metadata', {})
                    contents = metadata.get('contents', '') if isinstance(metadata, dict) else self._get_node_attr(metadata, 'contents', '')
                    
                    lines.append(f"{i}. **Node {node_id}** [semantic, {emb_info}]")
                    lines.append(f"   > {self._format_contents(contents, 'semantic')}")
                    lines.append("")
            
            # Img 节点
            if 'img' in type_groups:
                lines.append(f"#### Img 节点 ({len(type_groups['img'])} 个)")
                lines.append("")
                lines.append("| Node ID | Embedding | 其他信息 |")
                lines.append("|---------|-----------|----------|")
                for node_id, node in type_groups['img']:
                    embeddings = self._get_node_attr(node, 'embeddings')
                    emb_info = self._get_embedding_info(embeddings)
                    metadata = self._get_node_attr(node, 'metadata', {})
                    extra = ""
                    if isinstance(metadata, dict):
                        if 'quality_score' in metadata:
                            extra += f"quality={metadata['quality_score']:.1f} "
                        if 'bbox' in metadata:
                            extra += f"bbox={metadata['bbox']}"
                    lines.append(f"| {node_id} | {emb_info} | {extra} |")
                lines.append("")
            
            # Voice 节点
            if 'voice' in type_groups:
                lines.append(f"#### Voice 节点 ({len(type_groups['voice'])} 个)")
                lines.append("")
                lines.append("| Node ID | Embedding | ASR 文本 |")
                lines.append("|---------|-----------|----------|")
                for node_id, node in type_groups['voice']:
                    embeddings = self._get_node_attr(node, 'embeddings')
                    emb_info = self._get_embedding_info(embeddings)
                    metadata = self._get_node_attr(node, 'metadata', {})
                    asr = ""
                    if isinstance(metadata, dict):
                        asr_texts = metadata.get('asr_texts', [])
                        if asr_texts:
                            asr = "; ".join(asr_texts[:2])
                            if len(asr_texts) > 2:
                                asr += f" ... (+{len(asr_texts)-2})"
                    lines.append(f"| {node_id} | {emb_info} | {asr} |")
                lines.append("")
        
        # 边分析
        lines.append("## 🔗 边连接分析")
        lines.append("")
        lines.append(self._format_edges(edges, nodes))
        lines.append("")
        
        # 写入文件
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "graph_analysis.md")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        print(f"[GraphParser] 已保存: {output_path}")
        return True


if __name__ == "__main__":
    # 测试
    import sys
    base_path = "/data1/rongjiej/NSTF_MODEL"
    parser = GraphParser(base_path)
    
    video_id = sys.argv[1] if len(sys.argv) > 1 else "study_07"
    output_dir = os.path.join(base_path, "analysis/data", video_id)
    
    parser.parse(video_id, output_dir)
