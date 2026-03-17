"""LLM-based procedure structure extractor with batch processing."""

import json
import time
from typing import List, Dict, Optional
from pathlib import Path


class ProcedureExtractor:
    """Extract procedural knowledge structures from video content via LLM."""

    def __init__(
        self,
        llm_model: str = 'gemini-2.5-flash',
        batch_size: int = 20,
        max_content_chars: int = 150,
        api_delay: float = 1.0,
    ):
        self.llm_model = llm_model
        self.batch_size = batch_size
        self.max_content_chars = max_content_chars
        self.api_delay = api_delay

        self._chat_api = None

    @property
    def chat_api(self):
        if self._chat_api is None:
            from env_setup import setup_paths
            setup_paths()
            from mmagent.utils.chat_api import get_response_with_retry, generate_messages
            self._chat_api = (get_response_with_retry, generate_messages)
        return self._chat_api

    def _get_gemini_response(self, prompt: str, max_retries: int = 5, timeout: int = 45) -> Optional[str]:
        """Call LLM API with retry and timeout handling."""
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
                    if timeout_count >= 5:
                        return None
                else:
                    return None

        return None

    def _parse_json(self, text: str) -> Optional[Dict]:
        """Parse JSON from LLM response with tolerance for common format issues."""
        if not text:
            return None

        text = text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)

        start = text.find('{')
        end = text.rfind('}') + 1
        if start < 0 or end <= start:
            return None

        json_str = text[start:end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        try:
            import re
            fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        try:
            import re
            detected_match = re.search(r'"detected"\s*:\s*(true|false)', json_str, re.IGNORECASE)
            if detected_match:
                if detected_match.group(1).lower() == 'false':
                    return {"detected": False}
        except:
            pass

        return None

    def detect_procedures(
        self,
        contents: List[Dict],
        max_procedures: int = 5,
    ) -> List[Dict]:
        """Detect procedural knowledge from episodic contents in batches."""
        all_procedures = []
        total_clips = len(contents)
        total_batches = (total_clips + self.batch_size - 1) // self.batch_size

        for batch_idx in range(total_batches):
            start = batch_idx * self.batch_size
            end = min(start + self.batch_size, total_clips)
            batch_contents = contents[start:end]

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

            if batch_idx < total_batches - 1:
                time.sleep(self.api_delay)

        return self._deduplicate(all_procedures, max_procedures)

    def extract_structure(
        self,
        contents: List[Dict],
        procedure: Dict,
    ) -> Optional[Dict]:
        """Extract detailed DAG structure for a single procedure."""

        goal = procedure.get('goal', '')
        if isinstance(goal, dict):
            goal = goal.get('name', str(goal))
        goal = str(goal)

        proc_type = procedure.get('type', 'task')
        if isinstance(proc_type, dict):
            proc_type = 'task'

        source_clips = procedure.get('source_clips', [])
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

        sample_contents = [c['content'][:200] for c in contents[:20]]

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

        if result:
            result = self._ensure_dag_completeness(result)
            result['source_clips'] = clean_clips

        return result

    def _ensure_dag_completeness(self, structure: Dict) -> Dict:
        """Ensure DAG has proper START/GOAL connections and edge attributes."""
        steps = structure.get('steps', [])
        edges = structure.get('edges', [])

        if not steps:
            return structure

        step_ids = []
        for s in steps:
            if isinstance(s, dict):
                step_ids.append(s.get('step_id', f'step_{len(step_ids)+1}'))

        if not step_ids:
            return structure

        has_start_edge = any(
            e.get('from_step') == 'START' or e.get('from') == 'START'
            for e in edges
        )
        has_goal_edge = any(
            e.get('to_step') == 'GOAL' or e.get('to') == 'GOAL'
            for e in edges
        )

        if not has_start_edge and step_ids:
            edges.insert(0, {
                'from_step': 'START',
                'to_step': step_ids[0],
                'count': 1,
                'probability': 1.0,
                'condition': None
            })

        if not has_goal_edge and step_ids:
            sources = {e.get('from_step') or e.get('from') for e in edges}
            targets = {e.get('to_step') or e.get('to') for e in edges}
            leaf_nodes = [sid for sid in step_ids if sid not in sources]

            if not leaf_nodes:
                leaf_nodes = [step_ids[-1]]

            for leaf in leaf_nodes:
                edges.append({
                    'from_step': leaf,
                    'to_step': 'GOAL',
                    'count': 1,
                    'probability': 1.0,
                    'condition': None
                })

        for edge in edges:
            if 'count' not in edge:
                edge['count'] = 1
            if 'probability' not in edge:
                edge['probability'] = 1.0

        structure['edges'] = edges
        return structure

    def _deduplicate(self, procedures: List[Dict], max_count: int) -> List[Dict]:
        """Deduplicate procedures by goal string."""
        seen = set()
        unique = []
        for p in procedures:
            goal = p.get('goal', '')
            if isinstance(goal, dict):
                goal = goal.get('name', str(goal))
            goal = str(goal)

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
        """Detect and extract procedural knowledge from a single clip."""
        content = clip_content.get('content', '')
        clip_id = clip_content.get('clip_id', 0)

        if not content or len(content.strip()) < 20:
            return None

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
            result['source_clips'] = [clip_id]

            if result.get('steps'):
                result = self._ensure_dag_completeness(result)

            return result

        return None
