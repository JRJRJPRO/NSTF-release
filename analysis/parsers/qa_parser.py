"""
问答结果解析器 (QA Parser)

将问答结果 JSON 解析为人可读的 Markdown 文档。
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 支持的 schema 版本
SUPPORTED_SCHEMA_VERSIONS = ["1.0", "1.1"]


class QAParser:
    """
    问答结果解析器
    
    将 results/{method}/{dataset}/{video_id}/*.json 解析为 Markdown 文档，
    展示完整的问答过程和对话历史。
    """
    
    def __init__(self, base_path: str):
        """
        Args:
            base_path: NSTF_MODEL 根目录的绝对路径
        """
        self.base_path = base_path
    
    def _normalize_method(self, method: str) -> str:
        """
        规范化方法名为实际的结果目录名
        
        nstf_level, nstf_node 等都映射到 nstf 目录
        """
        if method in ["nstf_level", "nstf_node"]:
            return "nstf"
        return method
        
    def find_result_dir(self, video_id: str, method: str = "baseline") -> Optional[str]:
        """
        查找视频对应的结果目录
        
        Args:
            video_id: 视频 ID
            method: 方法名 (baseline, nstf, nstf_level, nstf_node, etc.)
            
        Returns:
            结果目录路径，未找到返回 None
        """
        # 规范化方法名
        result_method = self._normalize_method(method)
        
        # 尝试 robot 目录
        robot_path = os.path.join(self.base_path, f"results/{result_method}/robot", video_id)
        if os.path.exists(robot_path) and os.path.isdir(robot_path):
            return robot_path
            
        # 尝试 web 目录
        web_path = os.path.join(self.base_path, f"results/{result_method}/web", video_id)
        if os.path.exists(web_path) and os.path.isdir(web_path):
            return web_path
            
        return None
    
    def get_dataset(self, video_id: str, method: str = "baseline") -> Optional[str]:
        """判断视频属于哪个数据集"""
        result_method = self._normalize_method(method)
        robot_path = os.path.join(self.base_path, f"results/{result_method}/robot", video_id)
        if os.path.exists(robot_path):
            return "robot"
        web_path = os.path.join(self.base_path, f"results/{result_method}/web", video_id)
        if os.path.exists(web_path):
            return "web"
        return None
    
    def load_annotation(self, video_id: str) -> Dict[str, Any]:
        """加载问答标注信息（包含 reasoning 等额外信息）"""
        for dataset in ["robot", "web"]:
            ann_path = os.path.join(self.base_path, f"data/annotations/{dataset}.json")
            if os.path.exists(ann_path):
                with open(ann_path, 'r', encoding='utf-8') as f:
                    annotations = json.load(f)
                if video_id in annotations:
                    return annotations[video_id]
        return {}
        
    def list_qa_files(self, result_dir: str) -> List[str]:
        """列出目录下所有问答结果文件"""
        files = []
        for f in os.listdir(result_dir):
            if f.endswith('.json') and not f.startswith('.'):
                files.append(os.path.join(result_dir, f))
        # 按问题编号排序
        files.sort(key=lambda x: self._extract_question_num(os.path.basename(x)))
        return files
    
    def _extract_question_num(self, filename: str) -> int:
        """从文件名提取问题编号"""
        # study_07_Q01.json -> 1
        import re
        match = re.search(r'Q(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def _format_json_block(self, data: Any, max_depth: int = 3) -> str:
        """格式化 JSON 数据块"""
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _format_conversation_message(self, msg: Dict) -> str:
        """格式化单条对话消息"""
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        lines = []
        if role == 'system':
            lines.append("### System Prompt")
            lines.append("")
            lines.append("```")
            lines.append(content)
            lines.append("```")
        elif role == 'user':
            lines.append("**User**:")
            lines.append("```")
            # 尝试美化 JSON
            if content.startswith("Searched knowledge:"):
                prefix = "Searched knowledge: "
                json_part = content[len(prefix):]
                try:
                    parsed = json.loads(json_part)
                    lines.append(prefix)
                    lines.append(json.dumps(parsed, ensure_ascii=False, indent=2))
                except:
                    lines.append(content)
            else:
                lines.append(content)
            lines.append("```")
        elif role == 'assistant':
            lines.append("**Assistant**:")
            lines.append("```")
            lines.append(content)
            lines.append("```")
        
        return "\n".join(lines)
    
    def _extract_think_and_action(self, content: str) -> Dict[str, str]:
        """从 assistant 回复中提取思考和行动"""
        result = {"think": "", "action": "", "action_content": ""}
        
        # 提取 <think>...</think>
        import re
        think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
        if think_match:
            result["think"] = think_match.group(1).strip()
        
        # 提取 Action 和 Content
        action_match = re.search(r'Action:\s*\[(\w+)\]', content)
        if action_match:
            result["action"] = action_match.group(1)
        
        content_match = re.search(r'Content:\s*(.+?)(?:\n|$)', content, re.DOTALL)
        if content_match:
            result["action_content"] = content_match.group(1).strip()
        
        return result
    
    def _load_json_file(self, file_path: str) -> dict:
        """
        安全加载 JSON 文件（带编码和解析错误处理）
        
        Args:
            file_path: JSON 文件路径
            
        Returns:
            解析后的 dict，失败返回空 dict
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except UnicodeDecodeError:
            # 尝试其他常见编码
            for encoding in ['utf-8-sig', 'latin-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return json.load(f)
                except:
                    continue
            print(f"[警告] 无法解码文件 {file_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[警告] JSON 解析失败 {file_path}: {e}")
            return {}
    
    def parse_single_qa(self, qa_file: str, annotation: Dict = None) -> str:
        """
        解析单个问答结果
        
        Args:
            qa_file: JSON 文件路径
            annotation: 该问题的标注信息（可选）
            
        Returns:
            Markdown 格式的分析文档
        """
        qa_data = self._load_json_file(qa_file)
        if not qa_data:
            return f"# 解析失败\n\n无法加载文件: {qa_file}"
        
        # Schema 版本检查
        schema_version = qa_data.get('schema_version', 'unknown')
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            print(f"[警告] 未知 schema 版本: {schema_version}，可能导致解析问题")
        
        lines = []
        
        # 标题
        qa_id = qa_data.get('id', os.path.basename(qa_file).replace('.json', ''))
        video_id = qa_data.get('video_id', 'unknown')
        
        lines.append(f"# 问答分析: {qa_id}")
        lines.append("")
        lines.append(f"**视频**: {video_id}  ")
        lines.append(f"**数据集**: {qa_data.get('dataset', 'unknown')}  ")
        lines.append(f"**方法**: {qa_data.get('method', 'unknown')}  ")
        lines.append(f"**解析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 问题信息
        lines.append("## 📋 问题信息")
        lines.append("")
        lines.append("| 字段 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| **问题** | {qa_data.get('question', '')} |")
        lines.append(f"| **标准答案** | {qa_data.get('answer', '')} |")
        
        type_original = qa_data.get('type_original', [])
        if isinstance(type_original, list):
            type_str = ", ".join(type_original)
        else:
            type_str = str(type_original)
        lines.append(f"| **问题类型** | {type_str} |")
        lines.append(f"| **Query Type** | {qa_data.get('type_query', 'N/A')} |")
        
        # 如果有标注信息，添加额外字段
        if annotation:
            if 'timestamp' in annotation:
                lines.append(f"| **时间戳** | {annotation['timestamp']} |")
            if 'before_clip' in annotation:
                lines.append(f"| **Before Clip** | {annotation['before_clip']} |")
            if 'reasoning' in annotation:
                lines.append(f"| **标注推理** | {annotation['reasoning']} |")
        
        lines.append("")
        
        # 结果摘要
        lines.append("## 🎯 结果摘要")
        lines.append("")
        lines.append("| 指标 | 值 |")
        lines.append("|------|-----|")
        
        response = qa_data.get('response', '')
        lines.append(f"| **模型回答** | {response} |")
        
        gpt_eval = qa_data.get('gpt_eval', False)
        eval_icon = "✅ 正确" if gpt_eval else "❌ 错误"
        lines.append(f"| **GPT 评估** | {eval_icon} |")
        lines.append(f"| **LLM 轮数** | {qa_data.get('num_rounds', 'N/A')} |")
        lines.append(f"| **耗时** | {qa_data.get('elapsed_time_sec', 'N/A')} 秒 |")
        lines.append(f"| **检索次数** | {qa_data.get('search_count', 'N/A')} |")
        
        if qa_data.get('status') != 'success':
            lines.append(f"| **状态** | {qa_data.get('status', 'unknown')} |")
            if qa_data.get('error_message'):
                lines.append(f"| **错误信息** | {qa_data.get('error_message')} |")
        
        lines.append("")
        
        # NSTF 专用信息（如果有）
        if qa_data.get('nstf_available') or qa_data.get('nstf_path'):
            lines.append("## 🔷 NSTF 信息")
            lines.append("")
            lines.append("| 字段 | 值 |")
            lines.append("|------|-----|")
            lines.append(f"| NSTF 可用 | {'是' if qa_data.get('nstf_available') else '否'} |")
            if qa_data.get('nstf_path'):
                nstf_path = qa_data.get('nstf_path', '')
                nstf_name = os.path.basename(nstf_path) if nstf_path else '-'
                lines.append(f"| NSTF 图谱 | {nstf_name} |")
            if qa_data.get('mem_path'):
                mem_path = qa_data.get('mem_path', '')
                mem_name = os.path.basename(mem_path) if mem_path else '-'
                lines.append(f"| Memory 图谱 | {mem_name} |")
            lines.append("")
        
        # 检索追踪
        retrieval_trace = qa_data.get('retrieval_trace', [])
        if retrieval_trace:
            lines.append("## 🔍 检索过程追踪")
            lines.append("")
            
            for trace in retrieval_trace:
                round_num = trace.get('round', '?')
                query = trace.get('query', '')
                num_results = trace.get('num_results', 0)
                clips = trace.get('clips', [])
                
                lines.append(f"### Round {round_num}")
                lines.append("")
                lines.append(f"**检索 Query**: `{query}`")
                lines.append("")
                lines.append(f"**返回结果数**: {num_results}")
                lines.append("")
                
                # NSTF 检索决策（如果有）
                nstf_decision = trace.get('nstf_decision')
                if nstf_decision:
                    decision_icon = "✅ 使用 NSTF" if nstf_decision == 'use_nstf' else "⬇️ Fallback 到 Baseline"
                    lines.append(f"**NSTF 决策**: {decision_icon}")
                    lines.append("")
                
                # 匹配的 Procedures（如果有）
                matched_procs = trace.get('matched_procedures', [])
                if matched_procs:
                    lines.append("**匹配的 Procedures**:")
                    lines.append("")
                    lines.append("| Procedure ID | 相似度 | 匹配类型 |")
                    lines.append("|--------------|--------|----------|")
                    for proc in matched_procs:
                        proc_id = proc.get('proc_id', '?')
                        sim = proc.get('similarity', 0)
                        match_type = proc.get('match_type', '-')
                        lines.append(f"| {proc_id} | {sim:.3f} | {match_type} |")
                    lines.append("")
                
                if clips:
                    lines.append("**检索到的 Clips**:")
                    lines.append("")
                    lines.append("| Clip ID | Score | Source |")
                    lines.append("|---------|-------|--------|")
                    for clip in clips:
                        score = clip.get('score')
                        score_str = f"{score:.3f}" if isinstance(score, (int, float)) else str(score) if score else "-"
                        lines.append(f"| {clip.get('clip_id', '?')} | {score_str} | {clip.get('source', '?')} |")
                    lines.append("")
        
        # 完整对话历史
        conversations = qa_data.get('conversations', [])
        if conversations:
            lines.append("## 💬 完整对话历史")
            lines.append("")
            
            turn_num = 0
            for i, msg in enumerate(conversations):
                role = msg.get('role', '')
                content = msg.get('content', '')
                
                if role == 'system':
                    lines.append("### System Prompt")
                    lines.append("")
                    lines.append("```")
                    lines.append(content)
                    lines.append("```")
                    lines.append("")
                elif role == 'user':
                    turn_num += 1
                    lines.append(f"### Turn {turn_num}")
                    lines.append("")
                    lines.append("**User**:")
                    lines.append("")
                    
                    # 解析 Searched knowledge
                    if content.startswith("Searched knowledge:"):
                        prefix = "Searched knowledge: "
                        json_part = content[len(prefix):]
                        lines.append("```json")
                        try:
                            parsed = json.loads(json_part)
                            lines.append(json.dumps(parsed, ensure_ascii=False, indent=2))
                        except:
                            lines.append(json_part)
                        lines.append("```")
                    else:
                        lines.append("```")
                        lines.append(content)
                        lines.append("```")
                    lines.append("")
                elif role == 'assistant':
                    lines.append("**Assistant**:")
                    lines.append("")
                    lines.append("```")
                    lines.append(content)
                    lines.append("```")
                    lines.append("")
                    
                    # 提取并展示思考和行动
                    parsed = self._extract_think_and_action(content)
                    if parsed["think"]:
                        lines.append("**LLM 思考摘要**:")
                        lines.append("")
                        # 截取前500字符作为摘要
                        think_summary = parsed["think"][:500]
                        if len(parsed["think"]) > 500:
                            think_summary += "..."
                        lines.append(f"> {think_summary}")
                        lines.append("")
                    
                    if parsed["action"]:
                        lines.append(f"**行动**: `[{parsed['action']}]` {parsed['action_content']}")
                        lines.append("")
        
        # 分析总结（留空供手动填写）
        lines.append("## 📈 分析总结")
        lines.append("")
        lines.append("### 正确性分析")
        lines.append("- **答案匹配度**: (待分析)")
        lines.append("- **推理过程**: (待分析)")
        lines.append("")
        lines.append("### 检索效率")
        lines.append(f"- **检索轮数**: {qa_data.get('search_count', 'N/A')} 次")
        lines.append("- **检索精度**: (待分析)")
        lines.append("")
        lines.append("### 改进建议")
        lines.append("- (可手动添加分析笔记)")
        lines.append("")
        
        return "\n".join(lines)
    
    def parse(self, video_id: str, output_dir: str, method: str = "baseline") -> bool:
        """
        解析指定视频的所有问答结果
        
        Args:
            video_id: 视频 ID
            output_dir: 输出目录
            method: 方法名
            
        Returns:
            是否成功
        """
        # 查找结果目录
        result_dir = self.find_result_dir(video_id, method)
        if not result_dir:
            print(f"[QAParser] 未找到视频 {video_id} 的 {method} 结果目录")
            return False
        
        # 加载标注信息
        annotation_data = self.load_annotation(video_id)
        qa_annotations = {}
        if annotation_data and 'qa_list' in annotation_data:
            for qa in annotation_data['qa_list']:
                qid = qa.get('question_id', '')
                qa_annotations[qid] = qa
        
        # 列出所有问答文件
        qa_files = self.list_qa_files(result_dir)
        if not qa_files:
            print(f"[QAParser] 目录 {result_dir} 中没有问答结果文件")
            return False
        
        print(f"[QAParser] 找到 {len(qa_files)} 个问答结果")
        
        # 创建输出目录
        qa_output_dir = os.path.join(output_dir, "qa_results")
        os.makedirs(qa_output_dir, exist_ok=True)
        
        # 解析每个问答
        for qa_file in qa_files:
            filename = os.path.basename(qa_file)
            qa_id = filename.replace('.json', '')
            
            # 获取标注
            annotation = qa_annotations.get(qa_id)
            
            # 解析
            try:
                md_content = self.parse_single_qa(qa_file, annotation)
                
                # 提取问题编号
                q_num = self._extract_question_num(filename)
                output_filename = f"Q{q_num:02d}_analysis.md"
                output_path = os.path.join(qa_output_dir, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                print(f"[QAParser] 已保存: {output_path}")
                
            except Exception as e:
                print(f"[QAParser] 解析 {qa_file} 失败: {e}")
                continue
        
        return True


if __name__ == "__main__":
    # 测试
    import sys
    base_path = "/data1/rongjiej/NSTF_MODEL"
    parser = QAParser(base_path)
    
    video_id = sys.argv[1] if len(sys.argv) > 1 else "study_07"
    method = sys.argv[2] if len(sys.argv) > 2 else "baseline"
    output_dir = os.path.join(base_path, "analysis/data", video_id)
    
    parser.parse(video_id, output_dir, method)
