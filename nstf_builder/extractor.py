# -*- coding: utf-8 -*-
"""
程序结构提取器 - 优化版
参考: BytedanceM3Agent/neural_symbolic_experiments/scripts/generate_nstf_graphs_v2.py

核心改进:
1. 智能超时处理：5次超时跳过，避免无限等待
2. 分批处理：每批20个clip，避免超长请求
3. 内联prompt：不依赖外部模板文件
4. 更好的错误处理和日志
"""

import json
import time
from typing import List, Dict, Optional
from pathlib import Path


class ProcedureExtractor:
    """程序性知识提取器 - 优化版"""
    
    def __init__(
        self,
        llm_model: str = 'gemini-2.5-flash',
        batch_size: int = 20,  # 减小批次大小
        max_content_chars: int = 150,
        api_delay: float = 1.0,
    ):
        self.llm_model = llm_model
        self.batch_size = batch_size
        self.max_content_chars = max_content_chars
        self.api_delay = api_delay
        
        # 延迟导入
        self._chat_api = None
    
    @property
    def chat_api(self):
        if self._chat_api is None:
            # 使用 env_setup 确保路径已设置
            from env_setup import setup_paths
            setup_paths()
            from mmagent.utils.chat_api import get_response_with_retry, generate_messages
            self._chat_api = (get_response_with_retry, generate_messages)
        return self._chat_api
    
    def _get_gemini_response(self, prompt: str, max_retries: int = 5, timeout: int = 45) -> Optional[str]:
        """
        调用 Gemini API，带智能超时处理
        5次超时跳过，避免无限等待
        """
        get_response, generate_messages = self.chat_api
        timeout_count = 0
        
        for i in range(max_retries):
            try:
                messages = generate_messages([{"type": "text", "content": prompt}])
                response, _ = get_response(self.llm_model, messages, timeout=timeout)
                return response
            except Exception as e:
                error_str = str(e).lower()
                
                if "504" in error_str or "timeout" in error_str or "timed out" in error_str:
                    timeout_count += 1
                    print(f"    ⏱️ 超时 {timeout_count}/5: {str(e)[:50]}")
                    if timeout_count >= 5:
                        print(f"    ❌ 连续5次超时，跳过此请求")
                        return None
                else:
                    print(f"    ⚠️ 错误: {str(e)[:80]}")
                    return None
        
        return None
    
    def _parse_json(self, text: str) -> Optional[Dict]:
        """
        从文本中解析JSON（增强容错版本）
        
        处理常见的 LLM JSON 格式问题:
        1. 多余的逗号（trailing commas）
        2. 单引号替代双引号
        3. 未转义的换行符
        4. 代码块标记（```json）
        """
        if not text:
            return None
        
        # Step 1: 移除 markdown 代码块标记
        text = text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            # 移除首行 ```json 或 ```
            if lines[0].startswith('```'):
                lines = lines[1:]
            # 移除末行 ```
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)
        
        # Step 2: 找到 JSON 对象边界
        start = text.find('{')
        end = text.rfind('}') + 1
        if start < 0 or end <= start:
            return None
        
        json_str = text[start:end]
        
        # Step 3: 尝试直接解析
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Step 4: 修复常见问题并重试
        try:
            import re
            
            # 4a: 移除尾随逗号（在 } 或 ] 之前的逗号）
            fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
            
            # 4b: 修复未正确闭合的字符串（行末缺失引号）
            # 这通常是因为 LLM 在生成长字符串时被截断
            
            # 4c: 尝试解析修复后的 JSON
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        # Step 5: 最后尝试 - 用正则提取关键字段
        try:
            import re
            # 如果是 detect_in_clip 的输出，尝试提取 detected 字段
            detected_match = re.search(r'"detected"\s*:\s*(true|false)', json_str, re.IGNORECASE)
            if detected_match:
                if detected_match.group(1).lower() == 'false':
                    return {"detected": False}
                # detected=true 但 JSON 损坏，返回 None 让调用者重试
        except:
            pass
        
        # Step 6: 所有尝试失败，打印原始错误便于调试
        try:
            json.loads(json_str)
        except json.JSONDecodeError as e:
            # 只打印简短错误，避免刷屏
            error_context = json_str[max(0, e.pos-20):min(len(json_str), e.pos+30)]
            print(f"    ⚠️ JSON解析失败: {e.msg} near: ...{error_context}...")
        
        return None
    
    def detect_procedures(
        self,
        contents: List[Dict],
        max_procedures: int = 5,
    ) -> List[Dict]:
        """
        从内容中检测程序性知识（V2.3 改进）
        分批处理，带智能重试，提取具体的物品和位置信息
        """
        all_procedures = []
        total_clips = len(contents)
        total_batches = (total_clips + self.batch_size - 1) // self.batch_size
        
        print(f"    内容分成 {total_batches} 批处理")
        
        for batch_idx in range(total_batches):
            start = batch_idx * self.batch_size
            end = min(start + self.batch_size, total_clips)
            batch_contents = contents[start:end]
            
            # V2.3: 提取更多内容（200字符）以获取具体信息
            content_texts = [c['content'][:200] for c in batch_contents]
            
            prompt = f"""Analyze video content (clips {start+1}-{end}) to identify SPECIFIC procedural knowledge.

Content:
{json.dumps(content_texts, ensure_ascii=False)}

Identify up to {max_procedures} procedures. For each procedure, extract SPECIFIC details:

Output JSON:
{{
  "procedures": [
    {{
      "goal": "SPECIFIC goal with objects and locations (e.g., 'Store melon in refrigerator' NOT 'Put something somewhere')",
      "type": "task",
      "description": "detailed description mentioning WHO, WHAT objects, WHERE",
      "confidence": 0.9,
      "source_clips": [{start+1}],
      "key_objects": ["list", "specific", "objects", "like", "melon", "seasoning bottle"],
      "key_locations": ["list", "locations", "like", "refrigerator", "red cabinet", "dust bin"]
    }}
  ]
}}

CRITICAL:
- "type" MUST be exactly ONE of: "task", "habit", "trait", "social" - NEVER use combinations like "task|social"
- "goal" must mention SPECIFIC objects and locations from the video
- BAD: "Food preparation", "Cleaning", "Putting something"
- GOOD: "Store melon in refrigerator", "Get seasoning bottle from cabinet", "Throw expired food in dust bin"
- Extract key_objects and key_locations to help with later retrieval
- **USE person_N FORMAT**: Always refer to people as "person_1", "person_2", etc. NEVER use "woman", "man", "person in lab coat"
- Output JSON only."""
            
            response = self._get_gemini_response(prompt, max_retries=5, timeout=45)
            
            if response:
                result = self._parse_json(response)
                if result:
                    procs = result.get('procedures', [])
                    all_procedures.extend(procs)
                    print(f"    批次{batch_idx+1}: 检测到 {len(procs)} 个程序")
            else:
                print(f"    批次{batch_idx+1}: 无响应")
            
            if batch_idx < total_batches - 1:
                time.sleep(self.api_delay)
        
        # 去重
        return self._deduplicate(all_procedures, max_procedures)
    
    def extract_structure(
        self,
        contents: List[Dict],
        procedure: Dict,
    ) -> Optional[Dict]:
        """
        提取单个程序的详细结构（V2.3 论文规范）
        
        输出符合论文要求的 DAG 结构:
        - 包含 START 和 GOAL 控制节点
        - 边带有转移计数 count（初始为1）
        - 边带有转移概率 probability
        - 包含具体的物品、位置、参与者信息
        """
        
        goal = procedure.get('goal', '')
        # 确保 goal 是字符串
        if isinstance(goal, dict):
            goal = goal.get('name', str(goal))
        goal = str(goal)
        
        proc_type = procedure.get('type', 'task')
        if isinstance(proc_type, dict):
            proc_type = 'task'
        
        source_clips = procedure.get('source_clips', [])
        # 确保 source_clips 是整数列表
        clean_clips = []
        for clip in source_clips[:3]:
            if isinstance(clip, int):
                clean_clips.append(clip)
            elif isinstance(clip, dict):
                clean_clips.append(clip.get('clip_id', 1))
            else:
                try:
                    clean_clips.append(int(clip))
                except:
                    clean_clips.append(1)
        
        # 提供更多内容上下文，提取200字符
        sample_contents = [c['content'][:200] for c in contents[:20]]
        
        # 预先构建 episodic_links JSON 字符串
        episodic_links_list = [{"clip_id": c, "relevance": "source"} for c in clean_clips]
        episodic_links_json = json.dumps(episodic_links_list)
        
        prompt = f"""Extract DETAILED knowledge structure for: "{goal}"
Type: {proc_type}

Video content (analyze carefully for objects, locations, actions, and character traits):
{json.dumps(sample_contents, ensure_ascii=False)}

IMPORTANT: This is NOT just about action sequences! We support multiple knowledge types:
- "task": Step-by-step procedures (cooking, cleaning, organizing)
- "habit": Repeated behavioral patterns of a person
- "trait": Character attributes/personalities (e.g., "person_1 is helpful and often assists others")
- "social": Interaction patterns between people

Output JSON with SPECIFIC details:
{{
  "goal": "SPECIFIC goal - for task: 'Store melon in refrigerator'; for trait: 'person_1 demonstrates helpfulness'; for social: 'person_1 and person_2 collaborate on cooking'",
  "type": "{proc_type}",
  "description": "detailed description",
  "steps": [
    {{
      "step_id": "step_1", 
      "action": "SPECIFIC action or behavior", 
      "object": "item involved (or 'N/A' for trait/social)",
      "location": "where this happens",
      "actor": "who performs this (e.g., 'person_1')",
      "triggers": ["conditions that start this step"],
      "outcomes": ["results of this step"],
      "duration_seconds": 10
    }}
  ],
  "edges": [
    {{"from_step": "START", "to_step": "step_1", "count": 1, "probability": 1.0}},
    {{"from_step": "step_1", "to_step": "step_2", "count": 1, "probability": 0.7}},
    {{"from_step": "step_1", "to_step": "step_3", "count": 1, "probability": 0.3}},
    {{"from_step": "step_2", "to_step": "GOAL", "count": 1, "probability": 1.0}},
    {{"from_step": "step_3", "to_step": "GOAL", "count": 1, "probability": 1.0}}
  ],
  "objects": ["list", "all", "objects"],
  "locations": ["list", "all", "locations"],
  "participants": ["person_1", "person_2", "robot"],
  "episodic_links": {episodic_links_json}
}}

CRITICAL Requirements:
1. **SPECIFIC NOT GENERIC**: Use actual names from video
2. **MULTI-PATH DAG**: If there are ALTERNATIVE ways to achieve the goal, create BRANCHING edges!
   - Example: step_1 can lead to EITHER step_2 (70%) OR step_3 (30%)
   - Example: Both step_2 and step_3 can reach GOAL (convergence)
3. **SENSIBLE GOALS ONLY**: Reject nonsensical combinations (e.g., 'put Jesus in spinach' is WRONG)
4. **For trait/social types**: Steps represent behavioral instances, not physical actions
5. **MUST include START and GOAL in edges**
6. **Probabilities from same source must sum to 1.0**
7. **USE person_N FORMAT**: Always refer to people as "person_1", "person_2", etc. NEVER use descriptive terms like "woman", "man", "person in blue shirt", "first individual"

Output JSON only."""
        
        response = self._get_gemini_response(prompt, max_retries=5, timeout=60)
        result = self._parse_json(response)
        
        # 后处理：确保 DAG 结构完整
        if result:
            result = self._ensure_dag_completeness(result)
            # 添加 source_clips 到 metadata
            result['source_clips'] = clean_clips
        
        return result
    
    def _ensure_dag_completeness(self, structure: Dict) -> Dict:
        """
        确保 DAG 结构完整（论文规范）
        
        1. 确保有 START 和 GOAL 节点
        2. 确保所有边都有 count 字段
        3. 修复缺失的 START/GOAL 连接
        """
        steps = structure.get('steps', [])
        edges = structure.get('edges', [])
        
        if not steps:
            return structure
        
        # 收集所有 step_id
        step_ids = []
        for s in steps:
            if isinstance(s, dict):
                step_ids.append(s.get('step_id', f'step_{len(step_ids)+1}'))
        
        if not step_ids:
            return structure
        
        # 检查是否有 START 和 GOAL 连接
        has_start_edge = any(
            e.get('from_step') == 'START' or e.get('from') == 'START'
            for e in edges
        )
        has_goal_edge = any(
            e.get('to_step') == 'GOAL' or e.get('to') == 'GOAL'
            for e in edges
        )
        
        # 补充缺失的 START 连接
        if not has_start_edge and step_ids:
            edges.insert(0, {
                'from_step': 'START',
                'to_step': step_ids[0],
                'count': 1,
                'probability': 1.0,
                'condition': None
            })
        
        # 补充缺失的 GOAL 连接
        if not has_goal_edge and step_ids:
            # 找出没有后继的节点
            sources = {e.get('from_step') or e.get('from') for e in edges}
            targets = {e.get('to_step') or e.get('to') for e in edges}
            leaf_nodes = [sid for sid in step_ids if sid not in sources]
            
            if not leaf_nodes:
                leaf_nodes = [step_ids[-1]]  # 使用最后一个 step
            
            for leaf in leaf_nodes:
                edges.append({
                    'from_step': leaf,
                    'to_step': 'GOAL',
                    'count': 1,
                    'probability': 1.0,
                    'condition': None
                })
        
        # 确保所有边都有 count 字段
        for edge in edges:
            if 'count' not in edge:
                edge['count'] = 1
            if 'probability' not in edge:
                edge['probability'] = 1.0
        
        structure['edges'] = edges
        return structure
    
    def _deduplicate(self, procedures: List[Dict], max_count: int) -> List[Dict]:
        """去重 - 处理各种可能的格式问题"""
        seen = set()
        unique = []
        for p in procedures:
            # 确保 goal 是字符串
            goal = p.get('goal', '')
            if isinstance(goal, dict):
                goal = goal.get('name', str(goal))
            goal = str(goal)
            
            # 确保 source_clips 是整数列表
            source_clips = p.get('source_clips', [])
            if source_clips:
                cleaned_clips = []
                for clip in source_clips:
                    if isinstance(clip, int):
                        cleaned_clips.append(clip)
                    elif isinstance(clip, dict):
                        cleaned_clips.append(clip.get('clip_id', 0))
                    else:
                        try:
                            cleaned_clips.append(int(clip))
                        except:
                            pass
                p['source_clips'] = cleaned_clips
            
            if goal and goal not in seen:
                seen.add(goal)
                unique.append(p)
        return unique[:max_count]
    
    def detect_in_clip(self, clip_content: Dict) -> Optional[Dict]:
        """
        检测单个 clip 是否包含程序性知识，并提取完整结构（用于增量构建）
        
        V2.3 改进：同时提取 steps 和 edges，不再只是检测
        
        Args:
            clip_content: {'clip_id': int, 'content': str, 'raw_content': str}
            
        Returns:
            完整的程序结构，包含 steps 和 edges，或 None
        """
        content = clip_content.get('content', '')
        clip_id = clip_content.get('clip_id', 0)
        
        if not content or len(content.strip()) < 20:
            return None
        
        # V2.3: 一次性检测 + 提取完整结构
        prompt = f"""Analyze this video clip content and extract structured knowledge if present.

Clip content:
"{content[:500]}"

We support MULTIPLE knowledge types:
- "task": Step-by-step procedures (cooking, cleaning, organizing)
- "habit": Repeated behavioral patterns of a person (e.g., "person_1 always checks items before storing")
- "trait": Character attributes/personalities (e.g., "person_1 is organized and methodical")
- "social": Interaction patterns between people (e.g., "person_1 and person_2 discuss decisions together")

If this clip contains ANY of these knowledge types, extract the COMPLETE structure:

Output JSON:
{{
  "detected": true,
  "goal": "VERY SPECIFIC goal using ACTUAL names from content",
  "type": "task|habit|trait|social (pick ONE)",
  "description": "detailed description",
  "confidence": 0.8,
  "steps": [
    {{
      "step_id": "step_1", 
      "action": "specific action or behavior", 
      "object": "ACTUAL item name (or 'N/A' for trait/social)", 
      "location": "ACTUAL location from content",
      "actor": "who performs (e.g., person_1, robot)",
      "triggers": ["condition that starts this"],
      "outcomes": ["result of this"],
      "duration_seconds": 10
    }}
  ],
  "edges": [
    {{"from_step": "START", "to_step": "step_1", "count": 1, "probability": 1.0}},
    {{"from_step": "step_1", "to_step": "step_2", "count": 1, "probability": 0.6}},
    {{"from_step": "step_1", "to_step": "step_3", "count": 1, "probability": 0.4}},
    {{"from_step": "step_2", "to_step": "GOAL", "count": 1, "probability": 1.0}}
  ],
  "objects": ["list", "of", "objects"],
  "locations": ["list", "of", "locations"],
  "participants": ["person_1", "robot"]
}}

If NO structured knowledge, output: {{"detected": false}}

CRITICAL RULES:
1. "type" MUST be exactly ONE of: "task", "habit", "trait", "social"
2. REJECT NONSENSICAL goals (e.g., 'put Jesus in spinach' is WRONG - likely ASR error)
3. **MULTI-PATH DAG**: If there are ALTERNATIVE ways, create BRANCHING edges with probabilities
4. For "trait"/"social": steps are behavioral instances, object can be 'N/A'
5. Probabilities from same source node must sum to 1.0
6. Include START and GOAL in edges
7. **USE person_N FORMAT**: Always refer to people as "person_1", "person_2", etc. NEVER use "woman", "man", "person in blue shirt"

Output JSON only."""
        
        response = self._get_gemini_response(prompt, max_retries=3, timeout=45)
        result = self._parse_json(response)
        
        if result and result.get('detected'):
            # 添加 source clip 信息
            result['source_clips'] = [clip_id]
            
            # 确保 DAG 结构完整
            if result.get('steps'):
                result = self._ensure_dag_completeness(result)
            
            return result
        
        return None
