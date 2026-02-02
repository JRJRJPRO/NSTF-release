# NSTF Graph Construction V2 方案评审报告

> **评审状态**: 已完成（v2 修订）  
> **评审日期**: 2026-02-02  
> **评审者**: KG/问答系统专家  
> **基于文档**: NSTF_GRAPH_CONSTRUCTION_V2.md

---

## 核心假设（与作者确认后）

在评审前，先明确以下假设：

| 假设 | 说明 | 影响 |
|------|------|------|
| **Episodic 信息充足** | 原始 episodic 节点中已包含足够的细节信息 | 问题聚焦在构建/提取/链接方式 |
| **追溯是核心机制** | Procedure 本身可以抽象，但通过 episodic_links 追溯到具体证据后，信息量就够了 | episodic_links 的正确性是关键 |
| **增量更新解决稀疏** | 多个 clips 贡献到同一 Procedure，解决单次提取信息不足的问题 | Procedure 匹配准确性很重要 |
| **属性迭代设计** | 先拟定一批属性，根据实验结果决定保留哪些 | 需要设计评估框架 |

---

## 执行摘要

基于上述假设，V2 方案的整体方向是正确的。核心链路应该是：

```
Query → 匹配 Procedure → 通过 episodic_links 追溯 → 返回 Procedure + Episodic 内容 → LLM 生成答案
```

**核心结论**：
- ✅ 问题诊断准确，episodic_links 失效是直接原因
- ✅ 增量更新解决稀疏的思路可行
- ⚠️ 存在 4 个需要关注的技术风险
- ⚠️ 需要完善 episodic_links 的建立和验证机制
- 📋 属性设计建议采用"最小可行集 + 扩展"策略

---

## 1. 技术风险分析（基于新假设修订）

### 1.1 🔴 风险 #1：episodic_links 建立机制不够健壮

**问题描述**：

既然追溯到 episodic 是核心机制，那么 **episodic_links 的正确性和完整性** 就是整个系统的生命线。

当前 V2 方案中 episodic_links 的建立方式：

```python
# extractor.py 中的处理
source_clips = procedure.get('source_clips', [])  # 来自 LLM 检测结果
episodic_links = [{"clip_id": c, "relevance": "source"} for c in source_clips]
```

**潜在问题**：

1. **LLM 返回的 source_clips 可能不准确**
   - LLM 在 `detect_procedures` 阶段要同时完成：检测 Procedure + 识别来源 clips
   - 当内容分批处理时，LLM 只能看到当前批次，无法关联其他批次的 clips

2. **链接粒度问题**
   - 当前链接是 clip 级别，但一个 clip 可能包含多个 episodic 节点
   - 应该链接到具体的 episodic 节点，而非整个 clip

3. **链接缺乏验证**
   - 没有机制验证 source_clips 中的内容确实与该 Procedure 相关

**建议改进**：

```python
class EpisodicLinker:
    """增强的 episodic 链接器"""
    
    def build_verified_links(
        self,
        procedure: Dict,
        all_episodic_contents: List[Dict],
        video_graph
    ) -> List[EpisodicLink]:
        """
        构建经过验证的 episodic_links
        
        两阶段策略:
        1. 初始链接: 从 LLM 返回的 source_clips
        2. 验证+扩展: 用向量相似度验证并发现遗漏的相关 clips
        """
        links = []
        
        # 阶段 1: LLM 指定的 source_clips
        llm_clips = set(procedure.get('source_clips', []))
        
        # 阶段 2: 向量相似度验证+扩展
        proc_text = f"{procedure['goal']}. {procedure.get('description', '')}"
        proc_emb = self.embed(proc_text)
        
        for item in all_episodic_contents:
            clip_id = item['clip_id']
            content = item['content']
            content_emb = self.embed(content)
            
            sim = cosine_similarity(proc_emb, content_emb)
            
            if clip_id in llm_clips:
                # LLM 指定的，验证相似度
                if sim >= 0.25:  # 较低阈值，只过滤明显错误
                    links.append(EpisodicLink(
                        clip_id=clip_id,
                        node_id=item.get('node_id'),  # 链接到具体节点
                        relevance='source',
                        similarity=sim,
                        verified=True
                    ))
                else:
                    print(f"  ⚠️ Rejected link: clip_{clip_id} (sim={sim:.3f})")
            
            elif sim >= 0.40:  # 发现 LLM 遗漏的相关 clips
                links.append(EpisodicLink(
                    clip_id=clip_id,
                    node_id=item.get('node_id'),
                    relevance='discovered',  # 标记为自动发现
                    similarity=sim,
                    verified=True
                ))
        
        return links
```

**关键点**：
- 链接到 **node_id** 而非仅 clip_id，粒度更细
- **双重来源**：LLM 指定 + 向量发现
- **验证机制**：过滤明显错误的链接

---

### 1.2 🟡 风险 #2：增量更新的 Procedure 匹配需要更鲁棒

**问题描述**：

增量更新的前提是正确判断"这个 clip 应该更新哪个已有 Procedure"。V2 方案使用 goal embedding 相似度：

```python
if cosine_similarity(detected_emb, proc.embeddings['goal_emb']) >= 0.75:
    return proc  # 匹配成功
```

**风险**：
- 相似但不同的任务可能被错误合并（如 "Making coffee" vs "Making tea"）
- 相同任务的不同表述可能被错误分开（如 "Cook rice" vs "Prepare rice"）

**建议（与之前一致，但强调验证机制）**：

```python
def match_existing_procedure_v2(self, nstf_graph, detected, clip_content):
    """多信号融合匹配 + 人工可审核"""
    
    candidates = []
    for proc in nstf_graph.procedure_nodes.values():
        signals = {}
        
        # 信号 1: Goal 语义相似度
        signals['goal_sim'] = cosine_similarity(
            self.embed(detected['goal']), 
            proc.embeddings['goal_emb']
        )
        
        # 信号 2: 类型匹配
        signals['type_match'] = 1.0 if detected['type'] == proc.proc_type else 0.5
        
        # 信号 3: 关键动词重叠 (新增)
        detected_verbs = extract_verbs(detected['goal'])
        proc_verbs = extract_verbs(proc.goal)
        signals['verb_overlap'] = jaccard(detected_verbs, proc_verbs)
        
        # 加权得分
        score = (
            0.5 * signals['goal_sim'] + 
            0.2 * signals['type_match'] + 
            0.3 * signals['verb_overlap']
        )
        
        candidates.append({
            'proc': proc,
            'score': score,
            'signals': signals,
            'decision': 'merge' if score >= 0.70 else 'separate'
        })
    
    # 返回最佳候选（如果超过阈值）
    best = max(candidates, key=lambda x: x['score'])
    
    # 记录匹配决策，便于后续审核
    self.log_match_decision(detected, best)
    
    return best['proc'] if best['score'] >= 0.70 else None
```

**增加可审核性**：
- 记录每次匹配决策的详细信号
- 可以后续人工审核，调整阈值或添加规则

---

### 1.3 🟡 风险 #3：检索时 episodic_links 返回策略

**问题描述**：

假设 episodic 信息充足，那么检索时应该返回：
1. Procedure 的结构化信息（goal, steps 等）
2. **所有相关的 episodic 内容**（通过 episodic_links 追溯）

当前 V2 方案的 `_extract_episodic_evidence()` 存在 bug（已诊断），但修复后还需要考虑：

**问题 1：返回多少 episodic 节点？**
- 全部返回可能 token 过多
- 只返回 top-k 可能遗漏关键信息

**问题 2：如何排序？**
- 按 similarity？按时间顺序？按 relevance 类型？

**建议**：

```python
def retrieve_with_episodic(
    self,
    query: str,
    matched_procs: List[Dict],
    nstf_graph: Dict,
    video_graph,
    max_episodic_per_proc: int = 5,      # 每个 Procedure 最多返回 5 个
    total_max_episodic: int = 10,         # 总共最多返回 10 个
    prioritize_by: str = 'relevance'      # 排序方式
) -> Dict:
    """
    返回 Procedure + 追溯的 Episodic 内容
    """
    memories = {}
    all_episodic = []
    
    # 1. 格式化 Procedure 结构
    proc_info = self._format_procedures(matched_procs, nstf_graph)
    memories['NSTF_Procedures'] = proc_info
    
    # 2. 收集所有 episodic_links
    for match in matched_procs:
        proc = nstf_graph['procedure_nodes'].get(match['proc_id'], {})
        for link in proc.get('episodic_links', [])[:max_episodic_per_proc]:
            link['proc_id'] = match['proc_id']
            link['proc_similarity'] = match['similarity']
            all_episodic.append(link)
    
    # 3. 排序
    if prioritize_by == 'relevance':
        # source > discovered > update
        relevance_order = {'source': 3, 'discovered': 2, 'update': 1}
        all_episodic.sort(
            key=lambda x: (relevance_order.get(x['relevance'], 0), x.get('similarity', 0)),
            reverse=True
        )
    elif prioritize_by == 'similarity':
        all_episodic.sort(key=lambda x: x.get('similarity', 0), reverse=True)
    elif prioritize_by == 'temporal':
        all_episodic.sort(key=lambda x: x['clip_id'])
    
    # 4. 获取 episodic 内容
    for link in all_episodic[:total_max_episodic]:
        clip_id = link['clip_id']
        content = self._get_episodic_content(video_graph, clip_id, link.get('node_id'))
        if content:
            key = f"CLIP_{clip_id}"
            if key not in memories:
                memories[key] = content
    
    return memories
```

**关键配置项**（可调参）：
- `max_episodic_per_proc`: 每个 Procedure 最多追溯几个 episodic
- `total_max_episodic`: 总共最多返回几个 episodic
- `prioritize_by`: 排序策略（可做消融实验）

---

### 1.4 🟡 风险 #4：Character ID 映射仍需解决

**问题描述**：

从实验结果看，episodic 内容中使用 `<character_2>` 等占位符：

```json
"<character_2> and <character_3> are in a modern kitchen..."
```

但问题使用真实人名：

```
"What vegetables did Saxon and Tamera buy?"
```

**即使 episodic 信息充足，LLM 也无法将两者对应**。

**这不是 V2 方案的问题，但如果不解决，会严重影响人物相关问题的准确率**。

**建议**：

```python
# 方案 A: 构建时替换 (推荐)
def resolve_character_ids(content: str, video_graph) -> str:
    """在构建 NSTF 图谱时将 character ID 替换为真实名字"""
    char_mapping = video_graph.metadata.get('character_mapping', {})
    # {'<character_2>': 'Saxon', '<character_3>': 'Tamera'}
    
    for char_id, name in char_mapping.items():
        content = content.replace(char_id, name)
    return content

# 方案 B: 检索时补充映射信息
def add_character_context(memories: Dict, video_graph) -> Dict:
    """在返回的 memories 中补充 character 映射信息"""
    char_mapping = video_graph.metadata.get('character_mapping', {})
    if char_mapping:
        mapping_str = "Character Mapping: " + ", ".join(
            f"{k}={v}" for k, v in char_mapping.items()
        )
        memories['CHARACTER_INFO'] = mapping_str
    return memories
```

---

## 2. 属性设计建议：最小可行集 + 扩展

基于"先拟定几个，根据测试结果决定保留哪些"的策略，建议分层设计：

### 2.1 Procedure 节点属性

| 层级 | 属性 | 必要性 | 说明 |
|------|------|--------|------|
| **核心层** | `proc_id` | 必须 | 唯一标识 |
| | `goal` | 必须 | 触发条件/目标描述 |
| | `proc_type` | 必须 | task/habit/trait/social |
| | `steps` | 必须 | 步骤列表 |
| | `episodic_links` | 必须 | **关键：追溯到 episodic 的链接** |
| | `embeddings.goal_emb` | 必须 | 用于检索匹配 |
| **扩展层** | `description` | 推荐 | 简要描述 |
| | `edges` | 可选 | DAG 边（如果能提取到） |
| | `embeddings.steps_emb` | 推荐 | steps 聚合 embedding |
| | `metadata.observation_count` | 推荐 | 被观测次数（增量更新用） |
| | `metadata.source_clips` | 推荐 | 来源 clip 列表 |
| **实验层** | `metadata.confidence` | 待验证 | 整体置信度 |
| | `metadata.created_at` | 待验证 | 创建时间 |
| | `metadata.updated_at` | 待验证 | 更新时间 |

### 2.2 Step 节点属性

| 层级 | 属性 | 必要性 | 说明 |
|------|------|--------|------|
| **核心层** | `step_id` | 必须 | 步骤标识 |
| | `action` | 必须 | 动作描述 |
| **扩展层** | `triggers` | 可选 | 触发条件 |
| | `outcomes` | 可选 | 执行结果 |
| **实验层** | `required_tools` | 待验证 | 所需工具 |
| | `required_items` | 待验证 | 所需物品 |
| | `duration_seconds` | 待验证 | 持续时间 |
| | `success_rate` | 待验证 | 成功率 |

### 2.3 EpisodicLink 属性

| 层级 | 属性 | 必要性 | 说明 |
|------|------|--------|------|
| **核心层** | `clip_id` | 必须 | 关联的 clip ID |
| | `relevance` | 必须 | source/discovered/update |
| **扩展层** | `node_id` | 推荐 | 具体的 episodic 节点 ID（更细粒度） |
| | `similarity` | 推荐 | 与 Procedure 的相似度 |
| **实验层** | `content_preview` | 待验证 | 内容预览（便于调试） |
| | `verified` | 待验证 | 是否经过验证 |

### 2.4 评估框架

为了决定保留哪些属性，建议设计评估实验：

```python
# 属性消融实验框架
ATTRIBUTE_CONFIGS = {
    'minimal': {
        'proc': ['proc_id', 'goal', 'proc_type', 'steps', 'episodic_links', 'embeddings.goal_emb'],
        'step': ['step_id', 'action'],
        'link': ['clip_id', 'relevance'],
    },
    'extended': {
        'proc': ['...minimal...', 'description', 'embeddings.steps_emb', 'metadata.observation_count'],
        'step': ['...minimal...', 'triggers', 'outcomes'],
        'link': ['...minimal...', 'node_id', 'similarity'],
    },
    'full': {
        'proc': ['...extended...', 'edges', 'metadata.confidence', '...'],
        'step': ['...extended...', 'required_tools', 'duration_seconds', '...'],
        'link': ['...extended...', 'content_preview', 'verified'],
    },
}

def evaluate_attribute_config(config_name: str, test_questions: List) -> Dict:
    """评估不同属性配置的效果"""
    nstf_graph = build_nstf_with_config(ATTRIBUTE_CONFIGS[config_name])
    results = run_qa_evaluation(nstf_graph, test_questions)
    return {
        'accuracy': results['accuracy'],
        'graph_size_kb': get_graph_size(nstf_graph),
        'build_time_sec': results['build_time'],
        'avg_retrieval_time_ms': results['avg_retrieval_time'],
    }
```

**评估维度**：
1. **准确率提升**：该属性是否提升了问答准确率
2. **存储开销**：该属性增加了多少图谱大小
3. **构建成本**：该属性需要额外的 LLM 调用吗
4. **检索利用率**：该属性在检索/回答中被使用的频率

---

## 3. 实验设计建议（修订版）

### 3.1 消融实验组别

基于核心假设，消融实验应聚焦于：

| 组别 | Procedure | episodic_links | 增量更新 | 验证目标 |
|------|-----------|----------------|----------|---------|
| **Baseline** | ✗ | ✗ | ✗ | 对照组 |
| **NSTF-NoLinks** | ✓ | ✗ | ✗ | Procedure 结构本身的价值 |
| **NSTF-Links** | ✓ | ✓ | ✗ | episodic_links 追溯的价值 |
| **NSTF-Incr** | ✓ | ✓ | ✓ | 增量更新的价值 |

**关键对比**：
- NSTF-Links vs NSTF-NoLinks → 证明追溯机制的价值
- NSTF-Incr vs NSTF-Links → 证明增量更新的价值

### 3.2 episodic_links 验证实验

专门验证 episodic_links 的质量：

```python
def evaluate_episodic_links(nstf_graph, ground_truth_mapping):
    """
    评估 episodic_links 的质量
    
    ground_truth_mapping: {
        'proc_id': [list of clip_ids that should be linked]
    }
    """
    metrics = {
        'precision': [],  # 链接的 clips 中有多少是正确的
        'recall': [],     # 应该链接的 clips 中有多少被链接了
        'link_count': [], # 每个 Procedure 有多少链接
    }
    
    for proc_id, proc in nstf_graph['procedure_nodes'].items():
        linked_clips = set(link['clip_id'] for link in proc.get('episodic_links', []))
        true_clips = set(ground_truth_mapping.get(proc_id, []))
        
        if linked_clips:
            precision = len(linked_clips & true_clips) / len(linked_clips)
        else:
            precision = 0
            
        if true_clips:
            recall = len(linked_clips & true_clips) / len(true_clips)
        else:
            recall = 1.0 if not linked_clips else 0
        
        metrics['precision'].append(precision)
        metrics['recall'].append(recall)
        metrics['link_count'].append(len(linked_clips))
    
    return {
        'avg_precision': np.mean(metrics['precision']),
        'avg_recall': np.mean(metrics['recall']),
        'avg_link_count': np.mean(metrics['link_count']),
    }
```

### 3.3 按问题类型分析

确保测试集覆盖不同类型的问题：

| 问题类型 | 示例 | NSTF 预期优势 | 需要的能力 |
|----------|------|--------------|-----------|
| 事实类 | "What color is the cup?" | 中性 | episodic 检索 |
| 步骤类 | "How to store groceries?" | **高** | Procedure 结构 |
| 细节类 | "Where is spinach placed?" | **高** | episodic_links 追溯 |
| 人物类 | "What did Saxon do?" | 依赖 Character ID 映射 | 映射 + 检索 |
| 聚合类 | "What vegetables were bought?" | 中等 | 多 episodic 聚合 |

---

## 4. 关键遗漏（仍需关注）

### 4.1 Character ID 映射

（如前所述，这不是 V2 方案的问题，但必须解决）

### 4.2 Baseline 检索失效的根因

从实验结果看，即使 fallback 到 Baseline 也经常检索不到正确内容：

```json
"retrieval_trace": [
  {"query": "vegetables Saxon Tamera bought", "nstf_decision": "fallback", "clips": []}
]
```

这说明可能存在：
1. Baseline 向量检索的阈值设置问题
2. 原始 episodic 内容的表述与查询词不匹配
3. 检索范围被截断（before_clip 限制）

**建议**：在优化 NSTF 的同时，也要检查 Baseline 检索为何失效。

---

## 5. 优先级排序的行动建议（修订版）

### 立即执行（Phase 0，1-2天）

| 任务 | 原因 | 预期收益 |
|------|------|---------|
| 修复 episodic_links bug | 当前完全失效，修复后才能验证追溯机制 | **高** |
| 添加 Character ID 映射 | 解决人物相关问题，成本低 | **中** |
| 验证 Baseline 检索失效原因 | 确认不是原始数据问题 | **高** |

### 短期优化（Phase 1，3-5天）

| 任务 | 原因 | 预期收益 |
|------|------|---------|
| 实现 EpisodicLinker（验证+扩展机制） | 确保 episodic_links 正确且完整 | **高** |
| 优化检索返回策略（排序+数量控制） | 确保返回的 episodic 内容相关且不过多 | **中** |
| 设计属性评估框架 | 为后续属性筛选做准备 | **中** |

### 中期改进（Phase 2，5-7天）

| 任务 | 原因 | 预期收益 |
|------|------|---------|
| 实现增量更新（多信号融合匹配） | 解决 Procedure 稀疏问题 | **中-高** |
| 运行消融实验（NSTF-NoLinks vs NSTF-Links） | 验证追溯机制价值 | **高** |
| 属性消融实验 | 确定最终保留哪些属性 | **中** |

### 可选/长期（Phase 3）

| 任务 | 原因 | 预期收益 |
|------|------|---------|
| DAG 结构优化（如果 edges 确实有用） | 当前 edges 多为空 | **低-中** |
| 跨 Clip 信息聚合 | 支持需要枚举/聚合的问题 | **中** |

---

## 6. 总结（修订版）

基于与作者确认的核心假设：

1. **Episodic 信息充足** → 重点放在 **如何正确建立和使用 episodic_links**

2. **追溯是核心机制** → episodic_links 的质量是关键：
   - 需要验证机制确保链接正确
   - 需要扩展机制发现 LLM 遗漏的相关 clips
   - 检索时需要合理的返回策略（数量+排序）

3. **增量更新解决稀疏** → 方向正确，但需要：
   - 多信号融合匹配，避免语义漂移
   - 记录匹配决策便于审核

4. **属性迭代设计** → 建议采用"核心层 + 扩展层 + 实验层"策略：
   - 核心层必须实现
   - 扩展层推荐实现
   - 实验层根据测试结果决定

**最关键的下一步**：先修复 episodic_links bug 并验证，确认追溯机制能正常工作后，再进行后续优化。

---

## 附录：核心链路验证清单

在开始实施前，建议先手动验证以下链路：

```
□ 1. 选择一个测试问题（如 kitchen_03_Q01）
□ 2. 手动检查对应的 NSTF 图谱中是否有相关 Procedure
□ 3. 检查该 Procedure 的 episodic_links 是否有效
□ 4. 手动获取 episodic_links 指向的 clip 内容
□ 5. 验证这些 clip 内容是否包含回答问题所需的信息
□ 6. 如果包含，说明问题在于链路中某个环节失效
□ 7. 如果不包含，说明假设不成立，需要重新审视方案
```

---

*文档结束*

