# NSTF 图谱构建方案 V2.1

> **文档状态**: 已评审修订  
> **更新日期**: 2026-02-02  
> **版本**: V2.1 (基于专家评审修订)  
> **变更摘要**: 采纳评审建议，强化 episodic_links 机制，添加 Character ID 映射，优化属性分层

---

## 核心设计原则

基于评审确认的核心假设：

1. **Episodic 信息充足** → 问题聚焦在构建/提取/链接方式
2. **追溯是核心机制** → Procedure 可以抽象，通过 episodic_links 追溯到具体证据
3. **增量更新解决稀疏** → 多个 clips 贡献到同一 Procedure
4. **属性迭代设计** → 核心层必须实现，扩展层按需启用

**核心链路**：
```
Query → 匹配 Procedure → 通过 episodic_links 追溯 → 返回 Procedure + Episodic 内容 → LLM 生成答案
```

---

## 1. 问题诊断（保持不变）

### 1.1 设计意图 vs 实际实现

| 设计意图 | 实际实现 | 差距分析 |
|---------|---------|---------|
| **episodic_links 追溯** | 代码 bug：使用了不存在的 `video_graph.contents` | ❌ 完全失效 |
| **Procedure 增量更新** | 每次全量重建 | ❌ 未实现 |
| **Character ID 映射** | 未处理 | ❌ 人物问题无法回答 |

### 1.2 导致准确率低的直接原因

1. **episodic_links 失效**：检索器使用错误 API，`clips: []` 为空
2. **Character ID 未映射**：episodic 中是 `<character_2>`，问题中是 "Saxon"
3. **Procedure 稀疏**：单次提取信息不足

---

## 2. 改进方案设计

### 2.1 双模式设计（支持消融实验）

| 模式 | 名称 | 特点 | 适用场景 |
|------|------|------|---------|
| **Mode A** | `static` | 一次性构建，不更新 | 消融对照组 |
| **Mode B** | `incremental` | 逐 clip 构建，支持更新 | 主实验 |

### 2.2 核心架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NSTFGraphBuilder V2.1                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    CharacterResolver                         │   │
│  │  - resolve_ids(): 将 <character_x> 替换为真实名字            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ProcedureExtractor                        │   │
│  │  - detect_procedures()                                       │   │
│  │  - extract_structure()                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    EpisodicLinker (核心改进)                  │   │
│  │  - build_verified_links(): LLM指定 + 向量验证 + 自动发现     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│        ┌─────────────────────┴─────────────────────┐               │
│        ▼                                           ▼               │
│  ┌─────────────┐                         ┌─────────────────┐       │
│  │ Static      │                         │ Incremental     │       │
│  │ Builder     │                         │ Builder         │       │
│  │             │                         │ - match_proc()  │       │
│  │             │                         │ - update_proc() │       │
│  └─────────────┘                         └─────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. 详细技术设计

### 3.1 属性分层设计（采纳评审建议）

#### 3.1.1 Procedure 节点属性

| 层级 | 属性 | 必要性 | 说明 |
|------|------|--------|------|
| **核心层** | `proc_id` | 必须 | 唯一标识 |
| | `goal` | 必须 | 触发条件/目标描述 |
| | `proc_type` | 必须 | task/habit/trait/social |
| | `steps` | 必须 | 步骤列表 |
| | `episodic_links` | **必须** | 追溯到 episodic 的链接 |
| | `embeddings.goal_emb` | 必须 | 用于检索匹配 |
| **扩展层** | `description` | 推荐 | 简要描述 |
| | `edges` | 可选 | DAG 边 |
| | `embeddings.steps_emb` | 推荐 | steps 聚合 embedding |
| | `metadata.observation_count` | 推荐 | 被观测次数（增量用） |
| | `metadata.source_clips` | 推荐 | 来源 clip 列表 |

#### 3.1.2 Step 节点属性

| 层级 | 属性 | 必要性 |
|------|------|--------|
| **核心层** | `step_id`, `action` | 必须 |
| **扩展层** | `triggers`, `outcomes` | 可选 |
| **实验层** | `required_tools`, `duration_seconds` | 待验证 |

#### 3.1.3 EpisodicLink 属性（核心改进）

| 层级 | 属性 | 必要性 | 说明 |
|------|------|--------|------|
| **核心层** | `clip_id` | 必须 | 关联的 clip ID |
| | `relevance` | 必须 | source/discovered/update |
| **扩展层** | `node_id` | 推荐 | 具体 episodic 节点 ID（更细粒度） |
| | `similarity` | 推荐 | 与 Procedure 的相似度 |
| | `verified` | 推荐 | 是否经过向量验证 |

### 3.2 Character ID 映射（新增，采纳评审建议）

```python
class CharacterResolver:
    """
    Character ID 解析器
    
    解决: episodic 中 <character_2>，问题中 "Saxon" 的映射问题
    """
    
    def __init__(self, video_graph):
        # 从 video_graph 元数据中获取映射
        # 格式: {'<character_2>': 'Saxon', '<character_3>': 'Tamera'}
        self.mapping = video_graph.metadata.get('character_mapping', {})
        
        # 如果没有预定义映射，尝试从 semantic 节点提取
        if not self.mapping:
            self.mapping = self._extract_from_semantic(video_graph)
    
    def _extract_from_semantic(self, video_graph) -> Dict[str, str]:
        """从 semantic 节点提取 character 映射"""
        mapping = {}
        for node_id, node in video_graph.nodes.items():
            if getattr(node, 'type', '') == 'semantic':
                # 查找 character 类型的 semantic 节点
                metadata = getattr(node, 'metadata', {})
                if metadata.get('semantic_type') == 'character':
                    char_id = metadata.get('character_id')  # <character_2>
                    name = metadata.get('name')  # Saxon
                    if char_id and name:
                        mapping[char_id] = name
        return mapping
    
    def resolve(self, content: str) -> str:
        """将内容中的 character ID 替换为真实名字"""
        for char_id, name in self.mapping.items():
            content = content.replace(char_id, name)
        return content
    
    def get_mapping_context(self) -> str:
        """生成映射上下文字符串，用于添加到检索结果"""
        if not self.mapping:
            return ""
        pairs = [f"{k}={v}" for k, v in self.mapping.items()]
        return "Character Mapping: " + ", ".join(pairs)
```

**使用方式**：
- **构建时**：在保存 episodic_links 的 content_preview 时替换
- **检索时**：在返回 memories 时添加 CHARACTER_INFO

### 3.3 EpisodicLinker（核心改进，采纳评审建议）

```python
class EpisodicLinker:
    """
    增强的 episodic 链接器
    
    核心改进（基于评审建议）:
    1. 双重来源: LLM 指定 + 向量自动发现
    2. 验证机制: 过滤明显错误的链接
    3. 链接到 node_id 而非仅 clip_id
    """
    
    def __init__(self, embed_fn, verify_threshold: float = 0.25, discover_threshold: float = 0.40):
        self.embed_fn = embed_fn
        self.verify_threshold = verify_threshold    # 验证 LLM 指定链接的阈值
        self.discover_threshold = discover_threshold  # 自动发现链接的阈值
    
    def build_verified_links(
        self,
        procedure: Dict,
        all_episodic_contents: List[Dict],
        video_graph
    ) -> List[Dict]:
        """
        构建经过验证的 episodic_links
        
        流程:
        1. 获取 LLM 指定的 source_clips
        2. 计算 Procedure 与所有 episodic 内容的相似度
        3. 验证 LLM 指定的链接（sim >= verify_threshold）
        4. 发现 LLM 遗漏的相关内容（sim >= discover_threshold）
        """
        links = []
        
        # LLM 指定的 clips
        llm_clips = set(procedure.get('source_clips', []))
        
        # 计算 Procedure embedding
        proc_text = f"{procedure.get('goal', '')}. {procedure.get('description', '')}"
        proc_emb = self._embed(proc_text)
        
        for item in all_episodic_contents:
            clip_id = item['clip_id']
            content = item['content']
            node_id = item.get('node_id')
            
            # 计算相似度
            content_emb = self._embed(content)
            sim = self._cosine_similarity(proc_emb, content_emb)
            
            if clip_id in llm_clips:
                # LLM 指定的链接 - 验证
                if sim >= self.verify_threshold:
                    links.append({
                        'clip_id': clip_id,
                        'node_id': node_id,
                        'relevance': 'source',
                        'similarity': round(sim, 4),
                        'verified': True
                    })
                else:
                    # 记录被拒绝的链接（调试用）
                    print(f"  ⚠️ Rejected LLM link: clip_{clip_id} (sim={sim:.3f} < {self.verify_threshold})")
            
            elif sim >= self.discover_threshold:
                # 自动发现的链接
                links.append({
                    'clip_id': clip_id,
                    'node_id': node_id,
                    'relevance': 'discovered',
                    'similarity': round(sim, 4),
                    'verified': True
                })
        
        # 按相似度排序
        links.sort(key=lambda x: x['similarity'], reverse=True)
        
        return links
    
    def _embed(self, text: str):
        """获取文本 embedding"""
        embs, _ = self.embed_fn("text-embedding-3-large", [text])
        vec = np.array(embs[0])
        return vec / (np.linalg.norm(vec) + 1e-8)
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        return float(np.dot(vec1, vec2))
```

### 3.4 Procedure 匹配器（增量更新用，采纳评审建议）

```python
class ProcedureMatcher:
    """
    Procedure 匹配器 - 用于增量更新
    
    采纳评审建议: 多信号融合匹配
    """
    
    def __init__(
        self, 
        embed_fn,
        match_threshold: float = 0.70,
        log_decisions: bool = True
    ):
        self.embed_fn = embed_fn
        self.match_threshold = match_threshold
        self.log_decisions = log_decisions
        self.decision_log = []
    
    def match_existing(
        self,
        nstf_graph: Dict,
        detected: Dict
    ) -> Optional[Dict]:
        """
        判断检测到的程序是否与已有程序匹配
        
        多信号融合:
        1. Goal 语义相似度 (50%)
        2. 类型匹配 (20%)
        3. 关键动词重叠 (30%)
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        if not proc_nodes:
            return None
        
        detected_goal = detected.get('goal', '')
        detected_type = detected.get('type', 'task')
        detected_emb = self._embed(detected_goal)
        detected_verbs = self._extract_verbs(detected_goal)
        
        candidates = []
        
        for proc_id, proc in proc_nodes.items():
            signals = {}
            
            # 信号 1: Goal 语义相似度
            if 'goal_emb' in proc.get('embeddings', {}):
                proc_emb = proc['embeddings']['goal_emb']
                signals['goal_sim'] = float(np.dot(detected_emb, proc_emb))
            else:
                signals['goal_sim'] = 0.0
            
            # 信号 2: 类型匹配
            proc_type = proc.get('proc_type', proc.get('type', 'task'))
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
        
        # 找最佳候选
        if not candidates:
            return None
        
        best = max(candidates, key=lambda x: x['score'])
        
        # 记录决策
        if self.log_decisions:
            self.decision_log.append({
                'detected_goal': detected_goal,
                'best_match': best['proc_id'],
                'score': best['score'],
                'signals': best['signals'],
                'decision': 'merge' if best['score'] >= self.match_threshold else 'create_new'
            })
        
        if best['score'] >= self.match_threshold:
            return best['proc']
        return None
    
    def _embed(self, text: str):
        from mmagent.utils.chat_api import parallel_get_embedding
        embs, _ = parallel_get_embedding("text-embedding-3-large", [text])
        vec = np.array(embs[0])
        return vec / (np.linalg.norm(vec) + 1e-8)
    
    def _extract_verbs(self, text: str) -> set:
        """简单提取动词（可用 spaCy 增强）"""
        # 简化实现：提取常见动词模式
        import re
        verb_patterns = [
            r'\b(make|cook|prepare|clean|wash|wipe|put|place|store|open|close|turn|check)\b',
            r'\b(making|cooking|preparing|cleaning|washing|wiping|putting|placing|storing)\b'
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

### 3.5 检索时 episodic 返回策略（采纳评审建议）

```python
class NSTFRetrieverV2:
    """
    改进的 NSTF 检索器
    
    采纳评审建议:
    1. 控制返回的 episodic 数量
    2. 支持多种排序策略
    3. 添加 Character 映射信息
    """
    
    def __init__(
        self,
        max_episodic_per_proc: int = 5,
        total_max_episodic: int = 10,
        prioritize_by: str = 'relevance'  # relevance | similarity | temporal
    ):
        self.max_episodic_per_proc = max_episodic_per_proc
        self.total_max_episodic = total_max_episodic
        self.prioritize_by = prioritize_by
    
    def retrieve_with_episodic(
        self,
        matched_procs: List[Dict],
        nstf_graph: Dict,
        video_graph,
        character_resolver = None
    ) -> Dict:
        """
        返回 Procedure + 追溯的 Episodic 内容
        """
        memories = {}
        
        # 1. 添加 Character 映射信息（如果有）
        if character_resolver:
            mapping_info = character_resolver.get_mapping_context()
            if mapping_info:
                memories['CHARACTER_INFO'] = mapping_info
        
        # 2. 格式化 Procedure 结构
        proc_info = self._format_procedures(matched_procs, nstf_graph)
        memories['NSTF_Procedures'] = proc_info
        
        # 3. 收集所有 episodic_links
        all_links = []
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        
        for match in matched_procs:
            proc = proc_nodes.get(match['proc_id'], {})
            links = proc.get('episodic_links', [])
            
            for link in links[:self.max_episodic_per_proc]:
                link_copy = dict(link)
                link_copy['proc_id'] = match['proc_id']
                link_copy['proc_similarity'] = match.get('similarity', 0)
                all_links.append(link_copy)
        
        # 4. 排序
        all_links = self._sort_links(all_links)
        
        # 5. 获取 episodic 内容
        for link in all_links[:self.total_max_episodic]:
            clip_id = link['clip_id']
            node_id = link.get('node_id')
            
            content = self._get_episodic_content(video_graph, clip_id, node_id)
            
            if content:
                # 如果有 character_resolver，替换 ID
                if character_resolver:
                    content = [character_resolver.resolve(c) for c in content]
                
                key = f"CLIP_{clip_id}"
                if key not in memories:
                    memories[key] = content
        
        return memories
    
    def _sort_links(self, links: List[Dict]) -> List[Dict]:
        """按指定策略排序"""
        if self.prioritize_by == 'relevance':
            # source > discovered > update
            relevance_order = {'source': 3, 'discovered': 2, 'update': 1}
            return sorted(
                links,
                key=lambda x: (relevance_order.get(x.get('relevance', ''), 0), x.get('similarity', 0)),
                reverse=True
            )
        elif self.prioritize_by == 'similarity':
            return sorted(links, key=lambda x: x.get('similarity', 0), reverse=True)
        elif self.prioritize_by == 'temporal':
            return sorted(links, key=lambda x: x.get('clip_id', 0))
        return links
    
    def _get_episodic_content(self, video_graph, clip_id: int, node_id: str = None) -> List[str]:
        """
        正确获取 episodic 内容（修复原有 bug）
        """
        contents = []
        
        if node_id and node_id in video_graph.nodes:
            # 优先使用 node_id（更精确）
            node = video_graph.nodes[node_id]
            if hasattr(node, 'metadata'):
                contents = node.metadata.get('contents', [])
        
        elif clip_id in video_graph.text_nodes_by_clip:
            # 回退到 clip_id
            node_ids = video_graph.text_nodes_by_clip[clip_id]
            for nid in node_ids:
                node = video_graph.nodes.get(nid)
                if node and hasattr(node, 'metadata'):
                    node_contents = node.metadata.get('contents', [])
                    contents.extend(node_contents)
        
        return contents
    
    def _format_procedures(self, matched_procs: List[Dict], nstf_graph: Dict) -> str:
        """格式化 Procedure 信息"""
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        lines = []
        
        for i, match in enumerate(matched_procs, 1):
            proc_id = match['proc_id']
            proc = proc_nodes.get(proc_id, {})
            
            lines.append(f"--- Procedure {i} (Relevance: {match.get('similarity', 0):.2f}) ---")
            lines.append(f"Goal: {proc.get('goal', 'Unknown')}")
            
            steps = proc.get('steps', [])
            for j, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    action = step.get('action', '')
                    if action:
                        lines.append(f"Step {j}: {action}")
            
            lines.append("")
        
        return '\n'.join(lines)
```

---

## 4. 消融实验设计（采纳评审建议）

### 4.1 实验组别

| 组别 | Procedure | episodic_links | 增量更新 | 验证目标 |
|------|-----------|----------------|----------|---------|
| **Baseline** | ✗ | ✗ | ✗ | 对照组 |
| **NSTF-NoLinks** | ✓ | ✗ | ✗ | Procedure 结构本身的价值 |
| **NSTF-Links** | ✓ | ✓ | ✗ | episodic_links 追溯的价值 |
| **NSTF-Incr** | ✓ | ✓ | ✓ | 增量更新的价值 |

**关键对比**：
- NSTF-Links vs NSTF-NoLinks → 证明追溯机制的价值
- NSTF-Incr vs NSTF-Links → 证明增量更新的价值

### 4.2 评估指标

| 指标 | 说明 |
|------|------|
| Overall Accuracy | 整体问答准确率 |
| Procedural Accuracy | 步骤类问题准确率 |
| Character Accuracy | 人物相关问题准确率 |
| Link Precision | episodic_links 的准确率 |
| Link Recall | episodic_links 的召回率 |
| Empty Search Rate | 空搜索结果的比例 |

---

## 5. 实施计划

### 5.1 Phase 0: 立即修复（1-2天）

| 任务 | 优先级 | 预期收益 |
|------|--------|---------|
| 修复 episodic_links 获取 bug | P0 | **高** |
| 添加 Character ID 映射 | P0 | **高** |
| 验证 Baseline 检索失效原因 | P0 | **高** |

### 5.2 Phase 1: 短期优化（3-5天）

| 任务 | 说明 |
|------|------|
| 实现 EpisodicLinker | 验证+扩展机制 |
| 优化检索返回策略 | 排序+数量控制 |
| 重新构建测试图谱 | 使用改进后的构建器 |

### 5.3 Phase 2: 中期改进（5-7天）

| 任务 | 说明 |
|------|------|
| 实现 ProcedureMatcher | 多信号融合匹配 |
| 实现 IncrementalBuilder | 增量更新支持 |
| 运行消融实验 | 验证各组件价值 |

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| episodic_links 验证阈值不合适 | 链接过多/过少 | 可调参数，先用保守值 |
| Procedure 匹配误差 | 错误合并/分开 | 记录决策日志便于审核 |
| Character 映射不完整 | 部分人物无法解析 | 检索时补充映射上下文 |
| LLM 提取不稳定 | 属性缺失 | 核心属性必须，其他允许缺失 |

---

## 7. 核心链路验证清单

实施前先手动验证：

```
□ 1. 选择测试问题（如 kitchen_03_Q01）
□ 2. 检查 NSTF 图谱中是否有相关 Procedure
□ 3. 检查 episodic_links 是否指向正确的 clips
□ 4. 手动获取这些 clips 的内容
□ 5. 验证内容是否包含回答问题所需的信息
□ 6. 检查 Character ID 映射是否可用
```

---

**文档结束**

*下一步*：评审通过后，从 Phase 0 开始实施。
