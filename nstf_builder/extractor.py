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
        """从文本中解析JSON"""
        if not text:
            return None
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError as e:
            print(f"    ⚠️ JSON解析失败: {e}")
        return None
    
    def detect_procedures(
        self,
        contents: List[Dict],
        max_procedures: int = 5,
    ) -> List[Dict]:
        """
        从内容中检测程序性知识
        分批处理，带智能重试
        """
        all_procedures = []
        total_clips = len(contents)
        total_batches = (total_clips + self.batch_size - 1) // self.batch_size
        
        print(f"    内容分成 {total_batches} 批处理")
        
        for batch_idx in range(total_batches):
            start = batch_idx * self.batch_size
            end = min(start + self.batch_size, total_clips)
            batch_contents = contents[start:end]
            
            content_texts = [c['content'][:self.max_content_chars] for c in batch_contents]
            
            prompt = f"""Analyze video content (clips {start+1}-{end}) to identify procedural knowledge patterns.

Procedural knowledge includes:
1. **Task Procedures**: Step-by-step processes (e.g., cooking, assembling, operating)
2. **Behavioral Habits**: Recurring personal routines (e.g., checking keys before leaving)
3. **Character Traits & Reactions**: Consistent psychological or emotional response patterns (e.g., getting angry when interrupted)
4. **Social Interaction Patterns**: Recurring interpersonal dynamics (e.g., conflict resolution style)

Content:
{json.dumps(content_texts, ensure_ascii=False)}

Identify up to {max_procedures} procedures. Output JSON:
{{"procedures": [{{"goal": "procedure name/trigger condition", "type": "task|habit|trait|social", "description": "brief description", "confidence": 0.9, "source_clips": [{start+1}]}}]}}

Important:
- For character traits/reactions, "goal" should describe the trigger condition
- Include source_clips to enable linking back to episodic memories
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
        """提取单个程序的详细结构"""
        
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
        
        # 只取前15个clip的内容
        sample_contents = [c['content'][:100] for c in contents[:15]]
        
        # 预先构建 episodic_links JSON 字符串
        episodic_links_list = [{"clip_id": c, "relevance": "source"} for c in clean_clips]
        episodic_links_json = json.dumps(episodic_links_list)
        
        prompt = f"""Create a structured representation for: "{goal}"
Type: {proc_type}

Reference content:
{json.dumps(sample_contents, ensure_ascii=False)}

Output JSON:
{{
  "goal": "{goal}",
  "type": "{proc_type}",
  "description": "brief description",
  "steps": [
    {{"step_id": "step_1", "action": "action description", "triggers": [], "outcomes": [], "duration_seconds": 30, "success_rate": 0.95}}
  ],
  "edges": [
    {{"from_step": "step_1", "to_step": "step_2", "probability": 1.0, "condition": "optional condition"}}
  ],
  "episodic_links": {episodic_links_json}
}}
}}

DAG Structure Guidelines:
- **No separate 'alternatives' field** - alternatives are naturally represented by multiple edges
- **Path Fusion**: If both A→B→C and A→D→C patterns exist, create edges A→B, A→D, B→C, D→C
- **Multi-cause-single-effect**: For emotional/behavioral outcomes, multiple nodes can point to same result
  - Example: "tired"(p=0.25) → "angry", "shoes stepped on"(p=0.65) → "angry"
- Edge probabilities reflect observed frequency or causal strength

Output JSON only."""
        
        response = self._get_gemini_response(prompt, max_retries=5, timeout=60)
        return self._parse_json(response)
    
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
