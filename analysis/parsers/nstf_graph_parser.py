"""
NSTF 图谱解析器 (NSTF Graph Parser)

将 pickle 格式的 NSTF 图谱解析为人可读的 Markdown 文档。

NSTF 图谱结构:
{
    'video_name': str,
    'dataset': str,
    'procedure_nodes': {
        'proc_id': {
            'proc_id': str,
            'type': 'procedure',
            'goal': str,
            'description': str,
            'steps': List[Dict],
            'edges': List[Dict],
            'episodic_links': List[Dict],
            'embeddings': Dict,
            'metadata': Dict,
            'fusion_info': Dict (optional)
        }
    },
    'character_mapping': Dict (optional),
    'metadata': Dict,
    'stats': Dict (optional)
}
"""

import os
import pickle
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class NSTFGraphParser:
    """
    NSTF 图谱解析器
    
    将 NSTF pkl 文件中的图谱结构解析为 Markdown 文档，
    展示 Procedure 节点、步骤、边、episodic 链接等信息。
    """
    
    def __init__(self, base_path: str):
        """
        Args:
            base_path: NSTF_MODEL 根目录的绝对路径
        """
        self.base_path = base_path
        
    def find_graph_file(self, video_id: str) -> Optional[str]:
        """
        查找视频对应的 NSTF 图谱文件
        
        Args:
            video_id: 视频 ID，如 "study_07" 或 "Efk3K4epEzg"
            
        Returns:
            NSTF 图谱文件的完整路径，未找到返回 None
        """
        # 尝试 robot 目录
        robot_path = os.path.join(self.base_path, "data/nstf_graphs/robot", f"{video_id}_nstf.pkl")
        if os.path.exists(robot_path):
            return robot_path
            
        # 尝试 web 目录
        web_path = os.path.join(self.base_path, "data/nstf_graphs/web", f"{video_id}_nstf.pkl")
        if os.path.exists(web_path):
            return web_path
        
        # 尝试不带 _nstf 后缀
        robot_path2 = os.path.join(self.base_path, "data/nstf_graphs/robot", f"{video_id}.pkl")
        if os.path.exists(robot_path2):
            return robot_path2
            
        web_path2 = os.path.join(self.base_path, "data/nstf_graphs/web", f"{video_id}.pkl")
        if os.path.exists(web_path2):
            return web_path2
            
        return None
    
    def get_dataset(self, video_id: str) -> Optional[str]:
        """判断视频属于哪个数据集"""
        for suffix in ["_nstf.pkl", ".pkl"]:
            robot_path = os.path.join(self.base_path, f"data/nstf_graphs/robot/{video_id}{suffix}")
            if os.path.exists(robot_path):
                return "robot"
            web_path = os.path.join(self.base_path, f"data/nstf_graphs/web/{video_id}{suffix}")
            if os.path.exists(web_path):
                return "web"
        return None
        
    def load_graph(self, graph_path: str) -> Dict:
        """
        加载 NSTF 图谱文件
        
        Args:
            graph_path: pkl 文件路径
            
        Returns:
            NSTF 图谱 dict
            
        Raises:
            FileNotFoundError: 文件不存在
            pickle.UnpicklingError: 反序列化失败
        """
        try:
            with open(graph_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[错误] Pickle 加载失败: {e}")
            raise
    
    def _format_embedding_info(self, embeddings: Any) -> str:
        """获取 embedding 信息（只显示维度）"""
        if embeddings is None:
            return "无"
        
        if isinstance(embeddings, dict):
            parts = []
            for key, val in embeddings.items():
                if val is not None:
                    if hasattr(val, 'shape'):
                        parts.append(f"{key}: {val.shape[-1]}维")
                    elif isinstance(val, list) and len(val) > 0:
                        parts.append(f"{key}: {len(val)}维")
            return ", ".join(parts) if parts else "无"
        elif hasattr(embeddings, 'shape'):
            return f"{embeddings.shape[-1]}维"
        elif isinstance(embeddings, list) and len(embeddings) > 0:
            return f"{len(embeddings)}维"
        else:
            return "未知格式"
    
    def _format_step(self, step: Dict, index: int) -> List[str]:
        """格式化单个步骤"""
        lines = []
        
        step_id = step.get('step_id', f'step_{index}')
        action = step.get('action', '(无动作)')
        
        lines.append(f"**{step_id}**: {action}")
        
        # 触发条件
        triggers = step.get('triggers', [])
        if triggers:
            triggers_str = ", ".join(triggers) if isinstance(triggers, list) else str(triggers)
            lines.append(f"   - 触发条件: {triggers_str}")
        
        # 预期结果
        outcomes = step.get('outcomes', [])
        if outcomes:
            outcomes_str = ", ".join(outcomes) if isinstance(outcomes, list) else str(outcomes)
            lines.append(f"   - 预期结果: {outcomes_str}")
        
        # 其他元信息
        duration = step.get('duration_seconds')
        success_rate = step.get('success_rate')
        if duration or success_rate:
            meta_parts = []
            if duration:
                meta_parts.append(f"时长: {duration}s")
            if success_rate:
                meta_parts.append(f"成功率: {success_rate:.0%}")
            lines.append(f"   - {', '.join(meta_parts)}")
        
        return lines
    
    def _format_edges(self, edges: List) -> str:
        """格式化 DAG 边信息"""
        if not edges:
            return "无边信息（顺序执行）"
        
        lines = ["| 源步骤 | 目标步骤 | 概率/权重 | 条件 |",
                 "|--------|----------|-----------|------|"]
        
        for edge in edges:
            if isinstance(edge, dict):
                src = edge.get('from', edge.get('source', '?'))
                tgt = edge.get('to', edge.get('target', '?'))
                prob = edge.get('probability', edge.get('weight', 1.0))
                cond = edge.get('condition', '-')
                lines.append(f"| {src} | {tgt} | {prob:.2f} | {cond} |")
            elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                src, tgt = edge[0], edge[1]
                prob = edge[2] if len(edge) > 2 else 1.0
                lines.append(f"| {src} | {tgt} | {prob:.2f} | - |")
        
        return "\n".join(lines)
    
    def _format_episodic_links(self, links: List) -> str:
        """格式化 episodic 链接"""
        if not links:
            return "无 episodic 链接"
        
        lines = ["| Clip ID | 相关性 | 相似度 | 步骤关联 |",
                 "|---------|--------|--------|----------|"]
        
        for link in links:
            if isinstance(link, dict):
                clip_id = link.get('clip_id', '?')
                relevance = link.get('relevance', '-')
                similarity = link.get('similarity', link.get('score', '-'))
                if isinstance(similarity, float):
                    similarity = f"{similarity:.3f}"
                step_ref = link.get('step_id', link.get('step_ref', '-'))
                lines.append(f"| {clip_id} | {relevance} | {similarity} | {step_ref} |")
            elif isinstance(link, (list, tuple)) and len(link) >= 1:
                clip_id = link[0]
                lines.append(f"| {clip_id} | - | - | - |")
        
        return "\n".join(lines)
    
    def _format_fusion_info(self, fusion_info: Dict) -> str:
        """格式化融合信息"""
        if not fusion_info:
            return "无融合信息（原始 Procedure）"
        
        lines = []
        
        if fusion_info.get('is_fused'):
            lines.append("**已融合**: ✓")
            
        if fusion_info.get('source_procedures'):
            sources = fusion_info['source_procedures']
            lines.append(f"**源 Procedures**: {', '.join(sources)}")
            
        if fusion_info.get('fusion_count'):
            lines.append(f"**融合次数**: {fusion_info['fusion_count']}")
            
        if fusion_info.get('alignment_score'):
            lines.append(f"**对齐得分**: {fusion_info['alignment_score']:.3f}")
        
        return "\n".join(lines) if lines else "无融合信息"
    
    def _format_character_mapping(self, mapping: Dict) -> str:
        """格式化 character 映射"""
        if not mapping:
            return "无 character 映射"
        
        lines = ["| Character ID | 名称/描述 |",
                 "|--------------|-----------|"]
        
        for char_id, info in sorted(mapping.items()):
            if isinstance(info, str):
                lines.append(f"| {char_id} | {info} |")
            elif isinstance(info, dict):
                name = info.get('name', info.get('description', str(info)))
                lines.append(f"| {char_id} | {name} |")
            else:
                lines.append(f"| {char_id} | {info} |")
        
        return "\n".join(lines)
    
    def parse(self, video_id: str, output_dir: str) -> bool:
        """
        解析指定视频的 NSTF 图谱
        
        Args:
            video_id: 视频 ID
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        # 查找图谱文件
        graph_path = self.find_graph_file(video_id)
        if not graph_path:
            print(f"[NSTFGraphParser] 未找到视频 {video_id} 的 NSTF 图谱文件")
            return False
        
        dataset = self.get_dataset(video_id)
        
        # 加载图谱
        print(f"[NSTFGraphParser] 加载 NSTF 图谱: {graph_path}")
        try:
            nstf_graph = self.load_graph(graph_path)
        except Exception as e:
            print(f"[NSTFGraphParser] 加载失败: {e}")
            return False
        
        # 验证是 NSTF 格式
        if not isinstance(nstf_graph, dict) or 'procedure_nodes' not in nstf_graph:
            print(f"[NSTFGraphParser] 无法识别为 NSTF 图谱结构")
            return False
        
        procedure_nodes = nstf_graph.get('procedure_nodes', {})
        metadata = nstf_graph.get('metadata', {})
        character_mapping = nstf_graph.get('character_mapping', {})
        stats = nstf_graph.get('stats', {})
        
        # 统计
        total_procedures = len(procedure_nodes)
        total_steps = sum(len(p.get('steps', [])) for p in procedure_nodes.values())
        total_edges = sum(len(p.get('edges', [])) for p in procedure_nodes.values())
        total_links = sum(len(p.get('episodic_links', [])) for p in procedure_nodes.values())
        
        # 生成 Markdown
        lines = []
        lines.append(f"# NSTF 图谱分析: {video_id}")
        lines.append("")
        lines.append(f"**来源**: data/nstf_graphs/{dataset}/{video_id}_nstf.pkl  ")
        lines.append(f"**解析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
        lines.append(f"**NSTF 版本**: {metadata.get('version', 'unknown')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 统计表
        lines.append("## 📊 图谱统计")
        lines.append("")
        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| Procedure 数量 | {total_procedures} |")
        lines.append(f"| 总步骤数 | {total_steps} |")
        lines.append(f"| 总边数 | {total_edges} |")
        lines.append(f"| Episodic 链接数 | {total_links} |")
        lines.append(f"| 平均链接/Procedure | {total_links/total_procedures:.1f} |" if total_procedures else "| 平均链接/Procedure | 0 |")
        
        if stats:
            if stats.get('fusion_performed'):
                lines.append(f"| 融合次数 | {stats.get('fusion_performed', 0)} |")
            if stats.get('procedures_before_fusion'):
                lines.append(f"| 融合前 Procedure 数 | {stats.get('procedures_before_fusion', 0)} |")
        
        lines.append("")
        
        # 元数据
        lines.append("## 📝 构建元数据")
        lines.append("")
        lines.append("| 字段 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 视频名称 | {nstf_graph.get('video_name', video_id)} |")
        lines.append(f"| 数据集 | {nstf_graph.get('dataset', dataset)} |")
        lines.append(f"| 创建时间 | {metadata.get('created_at', 'unknown')} |")
        lines.append(f"| 处理耗时 | {metadata.get('processing_time', 0):.1f} 秒 |")
        if metadata.get('fusion_enabled') is not None:
            lines.append(f"| 融合启用 | {'是' if metadata.get('fusion_enabled') else '否'} |")
        lines.append("")
        
        # Character 映射
        if character_mapping:
            lines.append("## 👥 Character 映射")
            lines.append("")
            lines.append(self._format_character_mapping(character_mapping))
            lines.append("")
        
        # Procedure 详情
        lines.append("## 🔄 Procedure 详情")
        lines.append("")
        
        for proc_id, proc in procedure_nodes.items():
            goal = proc.get('goal', proc_id)
            description = proc.get('description', '')
            steps = proc.get('steps', [])
            edges = proc.get('edges', [])
            episodic_links = proc.get('episodic_links', [])
            embeddings = proc.get('embeddings', {})
            proc_metadata = proc.get('metadata', {})
            fusion_info = proc.get('fusion_info', {})
            
            lines.append(f"### 📋 {proc_id}")
            lines.append("")
            lines.append(f"**Goal**: {goal}")
            lines.append("")
            if description:
                lines.append(f"**Description**: {description}")
                lines.append("")
            
            # 统计
            lines.append("| 统计 | 数值 |")
            lines.append("|------|------|")
            lines.append(f"| 步骤数 | {len(steps)} |")
            lines.append(f"| 边数 | {len(edges)} |")
            lines.append(f"| Episodic 链接数 | {len(episodic_links)} |")
            lines.append(f"| Embedding | {self._format_embedding_info(embeddings)} |")
            lines.append("")
            
            # 步骤
            lines.append("#### 📝 步骤序列")
            lines.append("")
            if steps:
                for i, step in enumerate(steps, 1):
                    step_lines = self._format_step(step, i)
                    lines.extend(step_lines)
                    lines.append("")
            else:
                lines.append("(无步骤)")
                lines.append("")
            
            # DAG 边
            lines.append("#### 🔗 DAG 边（状态转移）")
            lines.append("")
            lines.append(self._format_edges(edges))
            lines.append("")
            
            # Episodic 链接
            lines.append("#### 🎬 Episodic 链接（证据追溯）")
            lines.append("")
            lines.append(self._format_episodic_links(episodic_links))
            lines.append("")
            
            # 融合信息
            if fusion_info:
                lines.append("#### 🔀 融合信息")
                lines.append("")
                lines.append(self._format_fusion_info(fusion_info))
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # 与 Baseline 的关联分析
        lines.append("## 🔍 与 Baseline 图谱的关联")
        lines.append("")
        lines.append("NSTF 图谱基于 Baseline Memory Graph 构建，通过以下方式关联：")
        lines.append("")
        lines.append("1. **Episodic Links**: 每个 Procedure 的 `episodic_links` 字段指向 Baseline 图谱中的 Clip ID")
        lines.append("2. **Character Mapping**: 将 Baseline 中的 `<face_N>`, `<voice_N>` 映射为统一的 character ID")
        lines.append("3. **时序对齐**: Procedure 的步骤顺序与原始 Episodic 事件的时序保持一致")
        lines.append("")
        
        # 写入文件
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "nstf_graph_analysis.md")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        print(f"[NSTFGraphParser] 已保存: {output_path}")
        return True


if __name__ == "__main__":
    # 测试
    import sys
    base_path = "/data1/rongjiej/NSTF_MODEL"
    parser = NSTFGraphParser(base_path)
    
    video_id = sys.argv[1] if len(sys.argv) > 1 else "study_03"
    output_dir = os.path.join(base_path, "analysis/data/nstf", video_id)
    
    parser.parse(video_id, output_dir)
