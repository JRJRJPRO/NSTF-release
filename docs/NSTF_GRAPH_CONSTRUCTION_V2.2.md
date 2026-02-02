# NSTF 图谱构建方案 V2.2

> **文档状态**: 最终版  
> **更新日期**: 2026-02-02  
> **版本**: V2.2.2 (基于四次评审修订)  
> **变更摘要**: 精简属性集、移除 NoLinks 消融组、success_rate 允许 LLM 猜测、调试模式、公共 embedding 工具、fallback 逻辑、阈值从高往低调

---

## 核心设计原则

1. **Episodic 信息充足** → 问题聚焦在构建/提取/链接方式
2. **追溯是核心机制** → Procedure 可以抽象，通过 episodic_links 追溯到具体证据
3. **增量更新解决稀疏** → 多个 clips 贡献到同一 Procedure
4. **最小可行属性集** → 先跑通核心链路，再按需扩展

**核心链路**：
```
Query → 匹配 Procedure → 通过 episodic_links 追溯 → 返回 Procedure + Episodic 内容 → LLM 生成答案
```

---

## 1. 节点与边属性定义（最终版）

### 1.1 Procedure 节点属性

| 属性 | 类型 | 必要性 | 说明 |
|------|------|--------|------|
| `proc_id` | str | **必须** | 唯一标识 |
| `goal` | str | **必须** | 触发条件/目标描述 |
| `proc_type` | str | **必须** | task/habit/trait/social |
| `steps` | List[Step] | **必须** | 步骤列表 |
| `episodic_links` | List[Link] | **必须** | 追溯链接（核心） |
| `embeddings.goal_emb` | ndarray | **必须** | 用于检索匹配 |
| `description` | str | 可选 | 简要描述 |
| `metadata.source_clips` | List[int] | 推荐 | 来源 clips（调试用） |
| `metadata.observation_count` | int | 增量时必须 | 被观测次数 |

**暂不实现**：
- `edges`: LLM 提取成功率低，后续需要 DAG 推理时再添加
- `embeddings.steps_emb`: 先验证 goal_emb 是否足够

### 1.2 Step 节点属性

| 属性 | 类型 | 必要性 | 说明 |
|------|------|--------|------|
| `step_id` | str | **必须** | 步骤标识 |
| `action` | str | **必须** | 动作描述 |
| `success_rate` | float | 可选 | 成功率（LLM 合理猜测即可，不需严格统计） |
| `triggers` | List[str] | Phase 2 验证 | 触发条件 |
| `outcomes` | List[str] | Phase 2 验证 | 执行结果 |

**说明**：`success_rate` 允许 LLM 基于常识合理猜测（如"煎蛋成功率约 0.9"），不要求严格的统计数据支撑。

### 1.3 EpisodicLink 属性

| 属性 | 类型 | 必要性 | 说明 |
|------|------|--------|------|
| `clip_id` | int | **必须** | 关联的 clip ID |
| `relevance` | str | **必须** | source/discovered/update |
| `similarity` | float | 推荐 | 与 Procedure 的相似度 |
| `node_id` | str | Phase 1 后期 | 具体节点 ID（更细粒度） |
| `content_preview` | str | 可选 | 内容预览（调试用，前 100 字） |

---

## 2. 双模式设计

### 2.1 Mode A: Static Builder（静态构建）

用于消融实验，一次性处理所有 clips。

```python
class StaticNSTFBuilder:
    """静态 NSTF 构建器"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.character_resolver = None
        self.episodic_linker = None
    
    def build(self, video_name: str, dataset: str) -> Dict:
        """
        一次性构建完整 NSTF 图谱
        """
        # 1. 加载 memory graph
        mem_graph = self.load_memory_graph(video_name, dataset)
        
        # 2. 初始化 Character 解析器
        self.character_resolver = CharacterResolver(mem_graph)
        if self.debug:
            print(f"Character mapping: {self.character_resolver.mapping}")
        
        # 3. 提取所有 episodic 内容（Character ID 已替换）
        all_contents = self.extract_all_episodic(mem_graph)
        
        # 4. 检测 Procedures
        procedures = self.extractor.detect_procedures(all_contents)
        if self.debug:
            print(f"Detected {len(procedures)} procedures")
        
        # 5. 提取结构 + 建立 episodic_links
        procedure_nodes = {}
        for proc in procedures:
            structure = self.extractor.extract_structure(all_contents, proc)
            node = self.create_procedure_node(structure)
            
            # 建立验证过的 episodic_links
            node['episodic_links'] = self.episodic_linker.build_verified_links(
                procedure=structure,
                all_episodic_contents=all_contents,
                video_graph=mem_graph
            )
            
            if self.debug:
                print(f"  {node['proc_id']}: {len(node['episodic_links'])} links")
            
            procedure_nodes[node['proc_id']] = node
        
        # 构建统计信息
        total_links = sum(len(p['episodic_links']) for p in procedure_nodes.values())
        stats = {
            'total_procedures': len(procedure_nodes),
            'total_links': total_links,
            'avg_links_per_proc': total_links / len(procedure_nodes) if procedure_nodes else 0,
            'character_mapping_found': bool(self.character_resolver.mapping),
        }
        
        if self.debug:
            print(f"\n=== Build Statistics ===")
            print(f"Procedures: {stats['total_procedures']}")
            print(f"Total links: {stats['total_links']}")
            print(f"Avg links/proc: {stats['avg_links_per_proc']:.1f}")
            print(f"Character mapping: {'Yes' if stats['character_mapping_found'] else 'No'}")
        
        nstf_graph = {
            'video_name': video_name,
            'dataset': dataset,
            'procedure_nodes': procedure_nodes,
            'character_mapping': self.character_resolver.mapping,
            'metadata': {
                'version': '2.2.2',
                'build_mode': 'static',
                'total_procedures': len(procedure_nodes),
            },
            'stats': stats  # 包含统计信息
        }
        return nstf_graph
    
    def extract_all_episodic(self, mem_graph) -> List[Dict]:
        """
        提取所有 episodic 内容，并应用 CharacterResolver 替换 ID
        
        重要：必须在返回前调用 character_resolver.resolve()
        否则内容仍然是 <character_2>，后续匹配会有问题
        """
        all_contents = []
        
        for clip_id in sorted(mem_graph.text_nodes_by_clip.keys()):
            node_ids = mem_graph.text_nodes_by_clip[clip_id]
            clip_texts = []
            
            for nid in node_ids:
                node = mem_graph.nodes.get(nid)
                if node and hasattr(node, 'metadata'):
                    contents = node.metadata.get('contents', [])
                    clip_texts.extend(contents)
            
            if clip_texts:
                # 合并并替换 Character ID
                combined = ' '.join(clip_texts)
                resolved = self.character_resolver.resolve(combined)  # 关键步骤!
                
                all_contents.append({
                    'clip_id': clip_id,
                    'content': resolved,
                    'raw_content': combined  # 保留原始内容便于调试
                })
        
        if self.debug:
            print(f"Extracted {len(all_contents)} clips with episodic content")
            # 检查是否还有未替换的 character ID
            for item in all_contents[:5]:
                if '<character_' in item['content']:
                    print(f"  ⚠️ Clip {item['clip_id']}: Character ID not fully resolved")
        
        return all_contents
```

### 2.2 Mode B: Incremental Builder（增量构建）

主实验方案，支持 Procedure 更新。

```python
class IncrementalNSTFBuilder:
    """增量 NSTF 构建器"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.matcher = ProcedureMatcher()
    
    def build(self, video_name: str, dataset: str) -> Dict:
        """
        逐 clip 增量构建 NSTF 图谱
        """
        mem_graph = self.load_memory_graph(video_name, dataset)
        clips = self.get_sorted_clips(mem_graph)
        
        nstf_graph = {
            'video_name': video_name,
            'procedure_nodes': {},
            'metadata': {'build_mode': 'incremental'}
        }
        
        for clip_id in clips:
            clip_content = self.get_clip_content(mem_graph, clip_id)
            
            # 检测当前 clip 是否包含程序性知识
            detected = self.extractor.detect_in_clip(clip_content)
            if not detected:
                continue
            
            # 尝试匹配已有 Procedure
            matched_proc = self.matcher.match_existing(nstf_graph, detected)
            
            if matched_proc:
                # 更新已有 Procedure
                self.update_procedure(matched_proc, clip_id, clip_content, detected)
                if self.debug:
                    print(f"  Clip {clip_id}: Updated {matched_proc['proc_id']}")
            else:
                # 创建新 Procedure
                new_proc = self.create_procedure(detected, clip_id, clip_content)
                nstf_graph['procedure_nodes'][new_proc['proc_id']] = new_proc
                if self.debug:
                    print(f"  Clip {clip_id}: Created {new_proc['proc_id']}")
        
        return nstf_graph
    
    def update_procedure(self, proc: Dict, clip_id: int, clip_content: Dict, detected: Dict):
        """更新已有 Procedure"""
        # 添加 episodic_link
        proc['episodic_links'].append({
            'clip_id': clip_id,
            'relevance': 'update',
            'similarity': detected.get('match_score', 0)
        })
        
        # 更新元数据
        proc['metadata']['observation_count'] += 1
        proc['metadata']['source_clips'].append(clip_id)
```

---

## 3. 公共工具函数

### 3.0 Embedding 工具（跨组件共享）

```python
# nstf_builder/utils.py
from functools import lru_cache
import numpy as np

# 全局缓存，跨组件共享
_embedding_cache = {}

def get_normalized_embedding(text: str, use_cache: bool = True) -> np.ndarray:
    """
    获取归一化的 embedding（带缓存）
    
    所有组件（EpisodicLinker, ProcedureMatcher, NSTFRetrieverV2）
    都应该使用这个函数，避免重复计算和重复 import
    """
    if use_cache and text in _embedding_cache:
        return _embedding_cache[text]
    
    from mmagent.utils.chat_api import parallel_get_embedding
    embs, _ = parallel_get_embedding("text-embedding-3-large", [text])
    vec = np.array(embs[0])
    normalized = vec / (np.linalg.norm(vec) + 1e-8)
    
    if use_cache:
        _embedding_cache[text] = normalized
    return normalized

def batch_get_normalized_embeddings(texts: List[str], use_cache: bool = True) -> List[np.ndarray]:
    """
    批量获取归一化的 embeddings
    
    优先从缓存获取，只对未缓存的调用 API
    """
    results = [None] * len(texts)
    texts_to_fetch = []
    indices_to_fetch = []
    
    for i, text in enumerate(texts):
        if use_cache and text in _embedding_cache:
            results[i] = _embedding_cache[text]
        else:
            texts_to_fetch.append(text)
            indices_to_fetch.append(i)
    
    if texts_to_fetch:
        from mmagent.utils.chat_api import parallel_get_embedding
        embs, _ = parallel_get_embedding("text-embedding-3-large", texts_to_fetch)
        for idx, text, emb in zip(indices_to_fetch, texts_to_fetch, embs):
            vec = np.array(emb)
            normalized = vec / (np.linalg.norm(vec) + 1e-8)
            if use_cache:
                _embedding_cache[text] = normalized
            results[idx] = normalized
    
    return results

def clear_embedding_cache():
    """清空缓存（测试或内存管理时使用）"""
    global _embedding_cache
    _embedding_cache = {}
```

---

## 4. 核心组件

### 4.1 CharacterResolver（多方法 Fallback）

```python
class CharacterResolver:
    """
    Character ID 解析器
    
    多方法 fallback:
    1. 从 video_graph.metadata 获取
    2. 从 semantic 节点提取
    3. 从 episodic 内容推断
    """
    
    def __init__(self, video_graph):
        self.mapping = {}
        self.video_graph = video_graph
        self._resolve()
    
    def _resolve(self):
        # 方法 1: 从 metadata
        if hasattr(self.video_graph, 'metadata'):
            mapping = self.video_graph.metadata.get('character_mapping', {})
            if mapping:
                self.mapping = mapping
                return
        
        # 方法 2: 从 semantic 节点
        self.mapping = self._extract_from_semantic()
        if self.mapping:
            return
        
        # 方法 3: 从 episodic 推断（复杂，暂不实现）
        print("⚠️ No character mapping found, character-related questions may fail")
    
    def _extract_from_semantic(self) -> Dict[str, str]:
        """从 semantic 节点提取 character 映射"""
        mapping = {}
        for node_id, node in self.video_graph.nodes.items():
            if getattr(node, 'type', '') == 'semantic':
                metadata = getattr(node, 'metadata', {})
                if metadata.get('semantic_type') == 'character':
                    char_id = metadata.get('character_id')
                    name = metadata.get('name')
                    if char_id and name:
                        mapping[char_id] = name
        return mapping
    
    def resolve(self, content: str) -> str:
        """将内容中的 character ID 替换为真实名字"""
        for char_id, name in self.mapping.items():
            content = content.replace(char_id, name)
        return content
    
    def get_mapping_context(self) -> str:
        """生成映射上下文字符串"""
        if not self.mapping:
            return ""
        pairs = [f"{k}={v}" for k, v in self.mapping.items()]
        return "Character Mapping: " + ", ".join(pairs)
```

### 4.2 EpisodicLinker（验证 + 发现）

```python
class EpisodicLinker:
    """
    增强的 episodic 链接器
    
    双重来源:
    1. LLM 指定的链接 → 向量验证
    2. 向量自动发现 → 补充遗漏
    
    使用公共 embedding 工具函数，跨组件共享缓存
    """
    
    def __init__(
        self, 
        verify_threshold: float = 0.40,   # 验证 LLM 指定链接（从高往低调）
        discover_threshold: float = 0.55,  # 自动发现链接
        debug: bool = False
    ):
        self.verify_threshold = verify_threshold
        self.discover_threshold = discover_threshold
        self.debug = debug
        self._clip_emb_map = {}  # clip_id -> embedding 的映射
    
    def _ensure_content_embeddings(self, all_episodic_contents: List[Dict]):
        """批量预计算所有 content 的 embedding（使用公共缓存）"""
        if self._clip_emb_map:
            return  # 本次构建已处理过
        
        from nstf_builder.utils import batch_get_normalized_embeddings
        texts = [item['content'] for item in all_episodic_contents]
        all_embs = batch_get_normalized_embeddings(texts)  # 使用公共工具
        
        for item, emb in zip(all_episodic_contents, all_embs):
            self._clip_emb_map[item['clip_id']] = emb
        
        if self.debug:
            print(f"  Prepared {len(all_embs)} content embeddings")
    
    def build_verified_links(
        self,
        procedure: Dict,
        all_episodic_contents: List[Dict],
        video_graph
    ) -> List[Dict]:
        """构建经过验证的 episodic_links"""
        links = []
        llm_clips = set(procedure.get('source_clips', []))
        
        # 1. 确保 content embeddings 已缓存
        self._ensure_content_embeddings(all_episodic_contents)
        
        # 2. 计算 Procedure embedding（使用公共工具）
        from nstf_builder.utils import get_normalized_embedding
        proc_text = f"{procedure.get('goal', '')}. {procedure.get('description', '')}"
        proc_emb = get_normalized_embedding(proc_text)
        
        rejected_count = 0
        discovered_count = 0
        
        for item in all_episodic_contents:
            clip_id = item['clip_id']
            content = item['content']
            
            # 使用预计算的 embedding
            content_emb = self._clip_emb_map.get(clip_id)
            if content_emb is None:
                content_emb = get_normalized_embedding(content)
            sim = self._cosine_similarity(proc_emb, content_emb)
            
            if clip_id in llm_clips:
                # LLM 指定的链接 - 验证
                if sim >= self.verify_threshold:
                    links.append({
                        'clip_id': clip_id,
                        'relevance': 'source',
                        'similarity': round(sim, 4),
                        'content_preview': content[:100] if content else None
                    })
                else:
                    rejected_count += 1
                    if self.debug:
                        print(f"  ⚠️ Rejected: clip_{clip_id} (sim={sim:.3f})")
            
            elif sim >= self.discover_threshold:
                # 自动发现
                links.append({
                    'clip_id': clip_id,
                    'relevance': 'discovered',
                    'similarity': round(sim, 4),
                    'content_preview': content[:100] if content else None
                })
                discovered_count += 1
        
        if self.debug:
            print(f"  Links: {len(links)} (source: {len(links)-discovered_count}, "
                  f"discovered: {discovered_count}, rejected: {rejected_count})")
        
        # 按相似度排序
        links.sort(key=lambda x: x['similarity'], reverse=True)
        return links
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        import numpy as np
        return float(np.dot(vec1, vec2))
```

### 4.3 ProcedureMatcher（多信号融合）

```python
class ProcedureMatcher:
    """
    Procedure 匹配器 - 用于增量更新
    
    多信号融合: goal相似度(50%) + 类型匹配(20%) + 动词重叠(30%)
    使用公共 embedding 工具函数
    """
    
    def __init__(
        self,
        match_threshold: float = 0.70,
        debug: bool = False
    ):
        self.match_threshold = match_threshold
        self.debug = debug
        self.decision_log = []  # 记录决策便于审核
    
    def match_existing(self, nstf_graph: Dict, detected: Dict) -> Optional[Dict]:
        """判断检测到的程序是否与已有程序匹配"""
        from nstf_builder.utils import get_normalized_embedding
        
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        if not proc_nodes:
            return None
        
        detected_goal = detected.get('goal', '')
        detected_type = detected.get('type', 'task')
        detected_emb = get_normalized_embedding(detected_goal)  # 使用公共工具
        detected_verbs = self._extract_verbs(detected_goal)
        
        candidates = []
        
        for proc_id, proc in proc_nodes.items():
            signals = {}
            
            # 信号 1: Goal 语义相似度
            proc_emb = proc.get('embeddings', {}).get('goal_emb')
            if proc_emb is not None:
                import numpy as np
                signals['goal_sim'] = float(np.dot(detected_emb, proc_emb))
            else:
                signals['goal_sim'] = 0.0
            
            # 信号 2: 类型匹配
            proc_type = proc.get('proc_type', 'task')
            signals['type_match'] = 1.0 if detected_type == proc_type else 0.5
            
            # 信号 3: 关键动词重叠
            proc_verbs = self._extract_verbs(proc.get('goal', ''))
            signals['verb_overlap'] = self._jaccard(detected_verbs, proc_verbs)
            
            # 加权得分
            score = (
                0.5 * signals['goal_sim'] +
                0.2 * signals['type_match'] +
                0.3 * signals['verb_overlap']
            )
            
            candidates.append({
                'proc_id': proc_id,
                'proc': proc,
                'score': score,
                'signals': signals
            })
        
        best = max(candidates, key=lambda x: x['score'])
        
        # 记录决策
        decision = {
            'detected_goal': detected_goal,
            'best_match': best['proc_id'],
            'score': best['score'],
            'signals': best['signals'],
            'decision': 'merge' if best['score'] >= self.match_threshold else 'create_new'
        }
        self.decision_log.append(decision)
        
        if self.debug:
            print(f"  Match decision: {decision['decision']} "
                  f"(score={best['score']:.3f}, goal_sim={best['signals']['goal_sim']:.3f})")
        
        return best['proc'] if best['score'] >= self.match_threshold else None
    
    def _extract_verbs(self, text: str) -> set:
        """提取动词（扩展的动词列表）"""
        import re
        # 通用动词 + 领域动词
        verb_patterns = [
            # 通用
            r'\b(make|cook|prepare|clean|wash|wipe|put|place|store|open|close|turn|check|get|take|give|find|use)\b',
            # 厨房
            r'\b(chop|stir|fry|boil|bake|pour|mix|season|slice|peel|heat|cool)\b',
            # 清洁
            r'\b(scrub|sweep|mop|dust|vacuum|rinse|dry)\b',
            # 动名词形式
            r'\b(making|cooking|preparing|cleaning|washing|wiping|putting|placing|storing)\b',
        ]
        verbs = set()
        for pattern in verb_patterns:
            matches = re.findall(pattern, text.lower())
            verbs.update(matches)
        return verbs
    
    def _jaccard(self, set1: set, set2: set) -> float:
        if not set1 and not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
```

### 4.4 NSTFRetrieverV2（检索器）

```python
class NSTFRetrieverV2:
    """
    改进的 NSTF 检索器
    
    返回: Procedure 结构 + 追溯的 Episodic 内容 + Character 映射
    支持 fallback 到 Baseline
    使用公共 embedding 工具函数
    """
    
    def __init__(
        self,
        max_episodic_per_proc: int = 5,
        total_max_episodic: int = 10,
        prioritize_by: str = 'relevance',
        min_confidence: float = 0.40  # 低于此阈值 fallback 到 Baseline（从高往低调）
    ):
        self.max_episodic_per_proc = max_episodic_per_proc
        self.total_max_episodic = total_max_episodic
        self.prioritize_by = prioritize_by
        self.min_confidence = min_confidence
        self.min_confidence = min_confidence
    
    def search(
        self,
        query: str,
        nstf_graph: Dict,
        video_graph,
        character_resolver=None,
        baseline_search_fn=None
    ) -> Dict:
        """
        完整检索流程（带 fallback）
        
        Args:
            baseline_search_fn: Baseline 检索函数，用于 fallback
        """
        # 1. 尝试 NSTF 检索
        matched_procs = self._match_procedures(query, nstf_graph)
        
        if matched_procs and matched_procs[0]['similarity'] >= self.min_confidence:
            # NSTF 命中
            return self.retrieve_with_episodic(
                matched_procs, nstf_graph, video_graph, character_resolver
            )
        else:
            # Fallback 到 Baseline
            if baseline_search_fn:
                memories, _, _ = baseline_search_fn(video_graph, query, [])
                return memories
            else:
                # 无 fallback 函数，返回空
                return {}
    
    def _match_procedures(self, query: str, nstf_graph: Dict) -> List[Dict]:
        """匹配 query 到 Procedures"""
        from nstf_builder.utils import get_normalized_embedding
        
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        if not proc_nodes:
            return []
        
        query_emb = get_normalized_embedding(query)  # 使用公共工具
        matches = []
        
        for proc_id, proc in proc_nodes.items():
            goal_emb = proc.get('embeddings', {}).get('goal_emb')
            if goal_emb is not None:
                import numpy as np
                sim = float(np.dot(query_emb, goal_emb))
                matches.append({'proc_id': proc_id, 'similarity': sim})
        
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        return matches[:3]  # 返回 top 3
    
    def retrieve_with_episodic(
        self,
        matched_procs: List[Dict],
        nstf_graph: Dict,
        video_graph,
        character_resolver=None
    ) -> Dict:
        """返回 Procedure + Episodic 内容"""
        memories = {}
        
        # 1. Character 映射信息
        if character_resolver:
            mapping_info = character_resolver.get_mapping_context()
            if mapping_info:
                memories['CHARACTER_INFO'] = mapping_info
        
        # 2. Procedure 结构
        proc_info = self._format_procedures(matched_procs, nstf_graph)
        memories['NSTF_Procedures'] = proc_info
        
        # 3. 收集 episodic_links
        all_links = []
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        
        for match in matched_procs:
            proc = proc_nodes.get(match['proc_id'], {})
            for link in proc.get('episodic_links', [])[:self.max_episodic_per_proc]:
                link_copy = dict(link)
                link_copy['proc_similarity'] = match.get('similarity', 0)
                all_links.append(link_copy)
        
        # 4. 排序
        all_links = self._sort_links(all_links)
        
        # 5. 获取 Episodic 内容
        for link in all_links[:self.total_max_episodic]:
            clip_id = link['clip_id']
            content = self._get_episodic_content(video_graph, clip_id)
            
            if content:
                if character_resolver:
                    content = [character_resolver.resolve(c) for c in content]
                
                key = f"CLIP_{clip_id}"
                if key not in memories:
                    memories[key] = content
        
        return memories
    
    def _sort_links(self, links: List[Dict]) -> List[Dict]:
        if self.prioritize_by == 'relevance':
            order = {'source': 3, 'discovered': 2, 'update': 1}
            return sorted(links, key=lambda x: (order.get(x.get('relevance'), 0), x.get('similarity', 0)), reverse=True)
        elif self.prioritize_by == 'similarity':
            return sorted(links, key=lambda x: x.get('similarity', 0), reverse=True)
        return links
    
    def _get_episodic_content(self, video_graph, clip_id: int) -> List[str]:
        """正确获取 episodic 内容（修复 bug）"""
        if clip_id not in video_graph.text_nodes_by_clip:
            return []
        
        contents = []
        node_ids = video_graph.text_nodes_by_clip[clip_id]
        for nid in node_ids:
            node = video_graph.nodes.get(nid)
            if node and hasattr(node, 'metadata'):
                node_contents = node.metadata.get('contents', [])
                contents.extend(node_contents)
        return contents
    
    def _format_procedures(self, matched_procs: List[Dict], nstf_graph: Dict) -> str:
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        lines = []
        
        for i, match in enumerate(matched_procs, 1):
            proc = proc_nodes.get(match['proc_id'], {})
            lines.append(f"--- Procedure {i} (Relevance: {match.get('similarity', 0):.2f}) ---")
            lines.append(f"Goal: {proc.get('goal', 'Unknown')}")
            
            for j, step in enumerate(proc.get('steps', []), 1):
                if isinstance(step, dict):
                    action = step.get('action', '')
                    if action:
                        lines.append(f"Step {j}: {action}")
            lines.append("")
        
        return '\n'.join(lines)
```

---

## 5. 消融实验设计

### 5.1 实验组别（精简版）

| 组别 | Procedure | episodic_links | 增量更新 | 说明 |
|------|-----------|----------------|----------|------|
| **Baseline** | ✗ | ✗ | ✗ | M3-Agent 原版 |
| **NSTF-Static** | ✓ | ✓ | ✗ | 静态构建 + 追溯 |
| **NSTF-Incr** | ✓ | ✓ | ✓ | 增量更新 |

### 5.2 关键对比

| 对比 | 验证目标 |
|------|---------|
| NSTF-Static vs Baseline | NSTF 整体方案有效性 |
| NSTF-Incr vs NSTF-Static | 增量更新的价值 |

### 5.3 评估指标

| 指标 | 说明 |
|------|------|
| Overall Accuracy | 整体问答准确率 |
| Character Accuracy | 人物相关问题准确率 |
| Empty Search Rate | 空搜索结果的比例 |
| Avg Links per Procedure | 每个 Procedure 平均链接数（质量指标） |

---

## 6. 阈值调参实验

在正式实验前，需要快速验证阈值设置。**从高往低调**，避免过低阈值引入噪声：

```python
# 阈值配置（从严格到宽松）
THRESHOLD_CONFIGS = [
    {'verify': 0.40, 'discover': 0.55},  # 默认值（严格）
    {'verify': 0.35, 'discover': 0.50},
    {'verify': 0.30, 'discover': 0.45},
]

# 评估标准
# - 每个 Procedure 应有 2-8 个 links
# - source 链接占 30-50%
# - 人工抽查准确率 > 70%
# - 记录 precision/recall，不仅是 link 数量
```

---

## 7. 实施计划

### Phase 0: 立即修复（1-2 天）

1. ✅ 修复 episodic_links 获取 bug
2. ✅ 实现 CharacterResolver
3. ✅ 用 minimal 属性集重建 kitchen_03 图谱
4. ✅ 手动验证核心链路

### Phase 1: 短期优化（3-5 天）

1. 实现 EpisodicLinker（verify + discover + **embedding 缓存**）
2. 阈值调参实验
3. 运行 NSTF-Static vs Baseline

### Phase 1.5: 检索器集成（1-2 天）

1. 确认 NSTFRetrieverV2 与现有系统的集成方式
2. 实现 fallback 到 Baseline 逻辑
3. 端到端测试检索流程

### Phase 2: 中期改进（5-7 天）

1. 实现 `detect_in_clip` 方法（单 clip 程序检测）
2. 实现 ProcedureMatcher + IncrementalBuilder
3. 运行 NSTF-Incr vs NSTF-Static
4. 测试 Step 扩展属性（triggers, outcomes）提取成功率

**detect_in_clip 设计要点**（Phase 2 实现时参考）：

```python
class ProcedureExtractor:
    def detect_in_clip(self, clip_content: Dict) -> Optional[Dict]:
        """
        检测单个 clip 是否包含程序性知识
        
        与 detect_procedures 的区别：
        - 输入是单个 clip，不是全部
        - 返回 0 或 1 个 detected procedure
        - 判断标准更宽松（因为上下文有限）
        - 使用不同的 prompt
        """
        prompt = f"""Analyze this single video clip to determine if it contains procedural knowledge.

Clip content:
{clip_content['content']}

Procedural knowledge includes: tasks, habits, routines, social interactions.
Be lenient - if there's any hint of a procedure, return detected=true.

If procedural knowledge is found, return JSON:
{{"detected": true, "goal": "...", "type": "task|habit|trait|social", "confidence": 0.8}}

If not found, return:
{{"detected": false}}
"""
        # ... LLM 调用
```

---

## 8. 核心链路验证清单

实施前手动验证：

```
□ 1. 选择测试问题（如 kitchen_03_Q01）
□ 2. 检查 NSTF 图谱中是否有相关 Procedure
□ 3. 检查 episodic_links 是否指向正确的 clips
□ 4. 手动获取这些 clips 的内容
□ 5. 验证内容是否包含回答问题所需的信息
□ 6. 检查 Character ID 映射是否可用
□ 7. 端到端测试检索 + LLM 生成
□ 8. 验证 embedding 缓存是否正常工作（避免重复计算）
□ 9. 验证 fallback 到 Baseline 的逻辑是否正常
□ 10. 检查构建时间是否在可接受范围（<5分钟/视频）
□ 11. 检查 API 调用次数是否合理（构建时、检索时）
□ 12. 验证 extract_all_episodic 是否正确应用了 CharacterResolver
□ 13. 验证 _embed 缓存是否跨组件共享（避免重复计算同一文本）
□ 14. 阈值调参时记录 precision/recall，不仅是 link 数量
```

---

## 9. 文件结构

```
nstf_builder/
├── __init__.py
├── utils.py                # 公共工具函数（embedding 等）
├── builder_v2.py           # 构建器入口（选择 static/incremental）
├── static_builder.py       # 静态构建器
├── incremental_builder.py  # 增量构建器
├── extractor.py            # Procedure 提取器（含 detect_in_clip）
├── episodic_linker.py      # episodic 链接器
├── procedure_matcher.py    # Procedure 匹配器
├── character_resolver.py   # Character ID 解析器
└── config/
    └── default.json

qa_system/core/
├── retriever_nstf.py       # 修复 bug 版本
├── retriever_nstf_v2.py    # V2 检索器
└── ...
```

---

**文档结束**

*下一步*：从 Phase 0 开始实施。
