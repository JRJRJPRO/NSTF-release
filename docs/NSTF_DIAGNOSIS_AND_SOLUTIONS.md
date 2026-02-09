# NSTF 知识图谱检索问题诊断报告与解决方案

**分析人员**: AI 知识图谱专家  
**分析时间**: 2026-02-04  
**分析对象**: kitchen_03 视频的 NSTF 图谱检索系统  
**论文参考**: `article\TWCS-KDD-25-\method_maxultra.tex`

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [问题诊断](#2-问题诊断)
3. [论文与实现对比](#3-论文与实现对比)
4. [根本原因分析](#4-根本原因分析)
5. [解决方案](#5-解决方案)
6. [实施优先级](#6-实施优先级)

---

## 1. 执行摘要

### 1.1 诊断概览

经过对论文、代码实现、图谱结构和问答结果的全面分析，发现 **NSTF 检索系统存在严重的实现缺陷**，与论文描述的方法有显著差异。

### 1.2 关键发现

| 问题类别 | 严重程度 | 影响范围 |
|---------|---------|---------|
| 🔴 **多粒度检索未实现** | 严重 | 检索质量 |
| 🔴 **Type-Aware Re-ranking 缺失** | 严重 | 检索相关性 |
| 🟡 **DAG 边转移统计未更新** | 中等 | 概率推理 |
| 🟡 **图谱构建质量问题** | 中等 | 证据追溯 |
| 🟢 **提示词设计不完善** | 轻微 | 答案准确性 |

### 1.3 影响评估

- **检索召回率低**: 相似度普遍在 0.27-0.42，远低于预期的 0.5-0.8
- **问答错误率高**: 多个简单问题回答错误（如 Q03、Q05 评估为 false）
- **检索效率差**: 多轮检索未找到相关信息（如 Q10 需要 4 轮检索）
- **知识覆盖不足**: 重要信息缺失导致无法回答

---

## 2. 问题诊断

### 2.1 问题一：多粒度检索未实现 🔴

#### 论文要求（Section 4.3.2）

> **Multi-Granularity Retrieval**: A single query may relate to memory at different levels of abstraction... retrieval proceeds in two stages that leverage the dual-level Index Vectors.
> 
> Stage I (Neural Discovery) performs broad similarity search across all memory layers. For Logic Nodes, retrieval scores **combine goal-level and step-level matching**:
> 
> $$\text{score}(q, \mathcal{N}) = \alpha \cdot \text{sim}(\phi(q), \mathbf{i}_{goal}) + (1-\alpha) \cdot \text{sim}(\phi(q), \mathbf{i}_{step})$$
> 
> where $\alpha \in [0,1]$ (default 0.3) balances high-level intent matching against specific content matching.

#### 实际实现

**文件**: `qa_system/core/retriever_nstf.py` L520-560

```python
def _search_procedures(self, query: str, proc_embeddings: Dict) -> List[Dict]:
    """多粒度Procedure检索
    
    同时检索goal和steps embedding，取最高相似度
    """
    query_embs, _ = parallel_get_embedding("text-embedding-3-large", [query])
    query_vec = np.array(query_embs[0])
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    
    results = []
    for proc_id, emb_dict in proc_embeddings.items():
        best_sim = -1
        best_type = None
        
        # 检查goal和steps embedding
        for emb_type in ['goal_emb', 'steps_emb']:  # ❌ 这里使用 steps_emb 而非 step_emb
            if emb_type in emb_dict:
                proc_vec = emb_dict[emb_type]
                sim = float(np.dot(query_vec, proc_vec))
                if sim > best_sim:
                    best_sim = sim
                    best_type = emb_type.replace('_emb', '')
        
        if best_sim >= self.threshold:
            results.append({
                'proc_id': proc_id,
                'similarity': best_sim,
                'match_type': best_type,  # ❌ 只记录匹配类型，未组合两个分数
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results
```

**问题**:
1. ❌ **未使用加权组合**: 代码仅取 `max(goal_sim, step_sim)`，而非论文的 `α*goal_sim + (1-α)*step_sim`
2. ❌ **Embedding 字段错误**: 代码查找 `steps_emb`，但图谱中实际字段是 `step_emb`（见分析报告）
3. ❌ **无双索引机制**: 论文提到 dual-level index，但实际只有单一匹配

**证据**: 分析报告显示图谱中的 embedding 字段为:
```
goal_emb: shape=(3072,), dtype=float64
step_emb: shape=(3072,), dtype=float64   ← 注意是 step_emb 而非 steps_emb
anchor_goal_emb: shape=(3072,)
anchor_step_emb: shape=(3072,)
```

#### 影响

- 检索分数偏低（0.27-0.42）因为只使用单一 embedding
- 错过了论文设计的 goal/step 互补机制
- 无法同时捕获高层目标和具体步骤的语义

---

### 2.2 问题二：Type-Aware Re-ranking 缺失 🔴

#### 论文要求（Section 4.3.2）

> **Stage II (Type-Aware Re-ranking)** re-weights candidates based on the query classification $y$ to prioritize the most relevant layer:
> 
> $$\text{score}_{final}(n) = \text{score}_{init}(n) \cdot w_{\text{layer}}(n, y)$$
> 
> where $w_{\text{layer}}$ assigns **higher weights to Logic Layer nodes** for $y \in \{\textsf{procedural}, \textsf{constraint}\}$ and to Episodic/Semantic nodes for $y = \textsf{factual}$.

#### 实际实现

**文件**: `qa_system/core/hybrid_retriever.py` L240-280

```python
def _search_nstf_full(self, video_graph, nstf_graph, query, current_clips, before_clip):
    # Step 1: Query Classification
    classification = self.query_classifier.classify(query)
    
    # Step 2: Multi-Granularity Procedure 匹配
    matched_procs = self._search_procedures(query, proc_embeddings)
    
    # Step 3: Type-Aware Re-ranking
    if config.use_reranking:  # ← 这个 flag 默认为 True
        matched_procs = self._apply_reranking(
            matched_procs, classification.query_type, nstf_graph
        )  # ❌ 但这个方法未实现！
```

**检查代码**: 搜索整个 `hybrid_retriever.py` (996 行)，发现:
```python
# ❌ _apply_reranking 方法不存在！
# 只有定义但无实现，导致 AttributeError 或直接跳过
```

**文件**: `qa_system/core/retriever_nstf.py` - 完全没有 re-ranking 逻辑

#### 影响

- **Factual 问题错误使用 NSTF**: Q01/Q03/Q05 都是 Factual 问题，应该优先使用 baseline episodic 检索，但系统强制使用 NSTF
- **检索相关性差**: 未根据问题类型调整权重，导致不相关的 Procedure 排在前面
- **多轮检索浪费**: Q10 需要 4 轮才找到相关信息，因为没有正确的 re-ranking

**实际案例 Q03**:
```json
{
  "question": "Where did the robot throw the expired ingredients?",
  "type_query": "Factual",  // ← 分类正确为 Factual
  "nstf_decision": "use_nstf",  // ❌ 但仍使用 NSTF 而非 baseline
  "matched_procedures": [
    {"proc_id": "kitchen_03_proc_14", "similarity": 0.327},  // 不相关
    {"proc_id": "kitchen_03_proc_10", "similarity": 0.303}   // 不相关
  ],
  "response": "The provided knowledge does not mention a robot...",
  "gpt_eval": false  // ❌ 回答错误
}
```

---

### 2.3 问题三：DAG 边转移统计未更新 🟡

#### 论文要求（Section 4.2.2）

> **Symbolic Refinement via Transition Statistics**: To capture this, we maintain edge-level transition counts $N_{ij}$ for each $(v_i, v_j) \in E$ in the Procedural DAG. Each observed transition $v_i \rightarrow v_j$ increments the count: $N_{ij} \leftarrow N_{ij} + 1$

#### 实际情况

**分析报告** `analysis_graph/reports/kitchen_03_robot_report.md`:

```markdown
## 4.5 边转移统计分析

### 边计数统计
- count 范围: 1 - 2
- count 均值: 1.01
- 所有 count=1 的 Procedure: 29/31
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计
- 所有 prob=1.0 的 Procedure: 31/31
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计
- 线性 DAG: 30/31
- 有分支的 DAG: 1/31
✅ 有 1 个 DAG 包含分支结构
```

**问题**:
1. ❌ 31 个 Procedure 中 29 个的边 count=1（未增量更新）
2. ❌ 所有边概率均为 1.0（未计算真实转移概率）
3. ❌ 只有 1 个 DAG 有分支（融合未生效）

#### 代码检查

**文件**: `nstf_builder/incremental_builder.py` L400-500

```python
def _update_procedure(self, existing_proc, new_clip_info):
    """更新已有 Procedure"""
    # ✅ 更新 episodic_links
    self._add_episodic_link(existing_proc, new_clip_info)
    
    # ✅ EMA 更新 embeddings
    self._update_embeddings_ema(existing_proc, new_clip_info)
    
    # ❌ 缺失: DAG 边 count 更新
    # ❌ 缺失: 转移概率重新计算
    # ❌ 缺失: 分支路径融合
```

**文件**: `nstf_builder/dag_fusion.py` - DAG 融合逻辑存在但未调用

#### 影响

- 无法支持论文中的概率推理（Theorem 4.1: Posterior Consistency）
- 无法识别多路径/分支（影响约束查询）
- 丢失了 incremental maintenance 的核心价值

---

### 2.4 问题四：图谱构建质量问题 🟡

#### Goal 质量分析

**分析报告**:
```markdown
## 6. Goal 质量分析
- 总 Procedure 数: 31
- 模糊 Goal 数: 1
- 具体 Goal 数: 16

### 模糊 Goals
- ⚠️ kitchen_03_proc_4: "Organize items unpacked from a white plastic bag in the kitchen"
```

**示例低质量 Goal**:
```
- "person_1 picks up a bottle, sets it down, and then picks up a pen"
- "person_1 and person_2 clean the kitchen"  ← 过于宽泛
- "Packing groceries including olive oil"  ← 缺乏动作主体
```

#### Episodic 覆盖率分析

```markdown
## 5. Episodic 覆盖率分析
- Video Graph 总 clips: 74
- NSTF 引用的 clips: 57
- 覆盖率: 77.0%
- 未覆盖的 clips: [0, 23, 27, 34, 35, 39, 41, 44, ...]  ← 17 个 clips 未被引用
```

#### 影响

- **Goal 过于泛化**: 检索时难以匹配具体查询
- **证据缺失**: 23% 的视频内容未被任何 Procedure 引用
- **召回率低**: 检索时可能错过相关信息

---

### 2.5 问题五：提示词设计不完善 🟢

#### 当前提示词

**文件**: `qa_system/prompts/system_prompt.py`

```python
"""
Available knowledge sources:
1. **Memory Bank**: Factual information...
2. **NSTF Graphs**: Structured procedural knowledge as DAGs...

When answering different question types:
- **Factual questions** (who/what/where/when): Prioritize episodic memories
- **Procedural questions** (how to/steps): Prioritize NSTF task procedures
- **Character understanding**: Check NSTF character traits
- **Constraint questions**: Find alternative paths in DAG

Important: 
- DAG edges have probabilities  ← ❌ 但实际所有概率都是 1.0
- Use episodic_links to find specific video clips  ← ✅ 这个有效
"""
```

#### 问题

1. ❌ **误导性指引**: 提示词说"DAG 有概率"，但实际都是 1.0
2. ❌ **未明确 NSTF 局限**: 未告知 LLM 何时应 fallback 到 baseline
3. ⚠️ **Procedure 格式问题**: 返回格式缺少足够的上下文信息

---

## 3. 论文与实现对比

### 3.1 核心差异表

| 功能模块 | 论文设计 | 实际实现 | 差异程度 |
|---------|---------|---------|---------|
| **多粒度检索** | $\alpha \cdot \text{sim}_{goal} + (1-\alpha) \cdot \text{sim}_{step}$ | `max(sim_goal, sim_steps)` 且字段名错误 | 🔴 严重 |
| **Type-Aware Re-ranking** | $\text{score}_{final}(n) = \text{score}_{init}(n) \cdot w_{\text{layer}}(n, y)$ | 未实现 | 🔴 严重 |
| **边转移统计** | $N_{ij} \leftarrow N_{ij} + 1$ 每次观测更新 | count=1 (未更新) | 🟡 中等 |
| **概率计算** | $\hat{P}(v_j \| v_i) = \frac{N_{ij}}{\sum_k N_{ik}}$ | 全部 prob=1.0 | 🟡 中等 |
| **DAG 融合** | Knowledge Fusion (Theorem 4.2) | 代码存在但未调用 | 🟡 中等 |
| **Symbolic Functions** | 3 种函数明确定义 | 仅部分实现 | 🟢 轻微 |

### 3.2 架构对比

#### 论文架构（Section 4.3）

```
Query → Classification → Multi-Granularity Retrieval
                ↓
        Type-Aware Re-ranking
                ↓
        Symbolic Enhancement
                ↓
           Agent Integration
```

#### 实际架构

```
Query → Classification (✅) → Single-Index Retrieval (❌)
                ↓
        (Re-ranking 缺失) ❌
                ↓
        Symbolic Functions (部分) 🟡
                ↓
           LLM 回答
```

---

## 4. 根本原因分析

### 4.1 实现路径偏差

1. **过度依赖单一检索**: 未理解多粒度检索的核心价值
2. **代码残留不一致**: `goal_emb` vs `step_emb` vs `steps_emb` 混乱
3. **增量更新未完善**: 只更新了 embedding 和 links，忽略了 DAG 统计

### 4.2 测试覆盖不足

- 未验证检索分数是否符合预期范围（应 >0.5，实际 0.27-0.42）
- 未检查 Procedure 字段的 embedding 是否正确加载
- 未测试边转移概率更新逻辑

### 4.3 论文理解偏差

- 误认为"多粒度"仅指"同时检索 goal 和 step"
- 未实现权重组合（α 参数）
- 忽略了 Type-Aware 的重要性

---

## 5. 解决方案

### 5.1 优先级 P0：修复多粒度检索 🔴

#### 修改文件
`qa_system/core/retriever_nstf.py`

#### 当前代码（L520-560）
```python
def _search_procedures(self, query: str, proc_embeddings: Dict) -> List[Dict]:
    # ... 省略前置代码 ...
    
    for proc_id, emb_dict in proc_embeddings.items():
        best_sim = -1
        best_type = None
        
        for emb_type in ['goal_emb', 'steps_emb']:  # ❌ 错误
            if emb_type in emb_dict:
                proc_vec = emb_dict[emb_type]
                sim = float(np.dot(query_vec, proc_vec))
                if sim > best_sim:
                    best_sim = sim
                    best_type = emb_type.replace('_emb', '')
        
        if best_sim >= self.threshold:
            results.append({
                'proc_id': proc_id,
                'similarity': best_sim,
                'match_type': best_type,
            })
```

#### 修正后代码
```python
def _search_procedures(
    self, 
    query: str, 
    proc_embeddings: Dict,
    alpha: float = 0.3  # 论文默认值
) -> List[Dict]:
    """
    多粒度 Procedure 检索 - 实现论文 Section 4.3.2
    
    score(q, N) = α * sim(φ(q), i_goal) + (1-α) * sim(φ(q), i_step)
    """
    query_embs, _ = parallel_get_embedding("text-embedding-3-large", [query])
    query_vec = np.array(query_embs[0])
    query_vec = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    
    results = []
    for proc_id, emb_dict in proc_embeddings.items():
        # 获取 goal 和 step embedding
        goal_vec = emb_dict.get('goal_emb')  # ✅ 正确字段名
        step_vec = emb_dict.get('step_emb')  # ✅ 正确字段名（非 steps_emb）
        
        if goal_vec is None or step_vec is None:
            continue
        
        # 计算双索引相似度
        sim_goal = float(np.dot(query_vec, goal_vec))
        sim_step = float(np.dot(query_vec, step_vec))
        
        # ✅ 加权组合（论文公式）
        combined_sim = alpha * sim_goal + (1 - alpha) * sim_step
        
        # 记录详细匹配信息
        if combined_sim >= self.threshold:
            results.append({
                'proc_id': proc_id,
                'similarity': combined_sim,
                'sim_goal': sim_goal,  # ✅ 保留分项分数用于调试
                'sim_step': sim_step,
                'match_type': 'combined',  # ✅ 明确标记为组合匹配
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results
```

#### 同步修改：Embedding 生成

**文件**: `qa_system/core/retriever_nstf.py` L705-750

```python
def _get_procedure_embeddings(self, nstf_graph: Dict, nstf_path: str) -> Dict:
    # ... 省略缓存检查 ...
    
    for proc_id, proc in proc_nodes.items():
        # Goal embedding
        goal = proc.get('goal', '')
        if goal and goal.strip():
            texts.append(goal)
            text_info.append((proc_id, 'goal'))
        
        # ✅ Steps embedding（注意单数 step）
        steps = proc.get('steps', [])
        if steps:
            actions = [s.get('action', '') for s in steps if isinstance(s, dict)]
            combined = '. '.join(actions)
            if combined.strip():
                texts.append(combined)
                text_info.append((proc_id, 'step'))  # ✅ 使用 'step' 而非 'steps'
    
    # ... 批量计算 embedding ...
    
    for i, emb in enumerate(all_embs):
        proc_id, emb_type = text_info[i]
        if proc_id not in result:
            result[proc_id] = {}
        
        vec = np.array(emb)
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        result[proc_id][f'{emb_type}_emb'] = vec  # ✅ 生成 goal_emb 和 step_emb
```

---

### 5.2 优先级 P0：实现 Type-Aware Re-ranking 🔴

#### 新增方法

**文件**: `qa_system/core/hybrid_retriever.py`

```python
def _apply_reranking(
    self,
    matched_procs: List[Dict],
    query_type: QueryType,
    nstf_graph: Dict
) -> List[Dict]:
    """
    Type-Aware Re-ranking - 实现论文 Section 4.3.2 Stage II
    
    score_final(n) = score_init(n) * w_layer(n, y)
    
    根据问题类型调整权重:
    - Factual: 降权 NSTF，优先 episodic
    - Procedural/Constraint: 增权 NSTF
    """
    # 定义层权重
    layer_weights = {
        QueryType.FACTUAL: 0.5,       # Factual 问题降权 NSTF
        QueryType.PROCEDURAL: 1.5,    # Procedural 问题增权
        QueryType.CONSTRAINT: 1.8,    # Constraint 问题最高权重
        QueryType.CHARACTER: 1.3,     # Character 问题中等权重
    }
    
    weight = layer_weights.get(query_type, 1.0)
    
    # 重新计算分数
    for proc in matched_procs:
        proc['original_similarity'] = proc['similarity']
        proc['similarity'] = proc['similarity'] * weight
        proc['reranking_weight'] = weight
    
    # 重新排序
    matched_procs.sort(key=lambda x: x['similarity'], reverse=True)
    
    return matched_procs
```

#### 修改决策逻辑

**文件**: `qa_system/core/hybrid_retriever.py` L250-280

```python
def _search_nstf_full(self, video_graph, nstf_graph, query, current_clips, before_clip):
    # ... Step 1-2: Classification and Retrieval ...
    
    # Step 3: Type-Aware Re-ranking
    if config.use_reranking:
        matched_procs = self._apply_reranking(
            matched_procs, classification.query_type, nstf_graph
        )
    
    # ✅ 新增: Factual 问题的混合检索决策
    if classification.query_type == QueryType.FACTUAL:
        # Factual 问题优先使用 baseline + NSTF 辅助
        if config.factual_hybrid:
            return self._hybrid_factual_search(
                video_graph, nstf_graph, query, current_clips, 
                matched_procs, before_clip
            )
    
    # Procedural/Constraint 继续使用 NSTF
    # ...
```

#### 新增混合检索方法

```python
def _hybrid_factual_search(
    self,
    video_graph,
    nstf_graph: Dict,
    query: str,
    current_clips: List,
    nstf_procs: List[Dict],
    before_clip: Optional[int]
) -> RetrievalResult:
    """
    Factual 问题的混合检索: Baseline + NSTF 辅助
    
    策略:
    1. 主要使用 baseline episodic 检索
    2. NSTF 提供补充证据（通过 episodic_links）
    3. 合并结果
    """
    # 1. Baseline 检索
    baseline_memories, baseline_clips, _ = baseline_search(
        video_graph, query, current_clips,
        threshold=self.baseline_config.threshold,
        topk=self.baseline_config.topk,
        before_clip=before_clip
    )
    
    # 2. NSTF 补充（如果有高相关性 Procedure）
    if nstf_procs and nstf_procs[0]['similarity'] >= 0.5:
        # 提取 episodic evidence
        evidence_clips = self._extract_episodic_evidence(
            nstf_procs[:2],  # 只取前 2 个
            nstf_graph,
            video_graph
        )
        
        # 合并到 baseline
        for clip_id, content in evidence_clips.items():
            if f'clip_{clip_id}' not in baseline_memories:
                baseline_memories[f'clip_{clip_id}'] = content
                if clip_id not in baseline_clips:
                    baseline_clips.append(clip_id)
    
    return RetrievalResult(
        memories=baseline_memories,
        clips=baseline_clips,
        metadata={
            'mode': 'nstf_factual_hybrid',
            'baseline_clips': len(baseline_clips),
            'nstf_procedures': len(nstf_procs) if nstf_procs else 0,
        }
    )
```

---

### 5.3 优先级 P1：修复 DAG 边转移统计 🟡

#### 修改文件
`nstf_builder/incremental_builder.py`

#### 新增方法：更新 DAG 统计

```python
def _update_dag_transitions(self, existing_proc: Dict, new_observation: Dict):
    """
    更新 DAG 边转移统计 - 实现论文 Section 4.2.2
    
    每次观测到相同 Procedure 时:
    1. 增加对应边的 count
    2. 重新计算转移概率
    """
    dag = existing_proc.get('dag', {})
    if not dag or 'edges' not in dag:
        return
    
    # 获取新观测的步骤序列
    new_steps = new_observation.get('steps', [])
    if not new_steps:
        return
    
    # 构建步骤到节点的映射
    step_to_node = {}
    for node_id, node_data in dag.get('nodes', {}).items():
        if node_data.get('type') == 'action':
            step_to_node[node_data.get('action', '')] = node_id
    
    # 遍历新步骤序列，增加对应边的 count
    for i in range(len(new_steps) - 1):
        curr_action = new_steps[i].get('action', '')
        next_action = new_steps[i+1].get('action', '')
        
        curr_node = step_to_node.get(curr_action)
        next_node = step_to_node.get(next_action)
        
        if curr_node and next_node:
            # 查找对应的边
            edge_key = f"{curr_node}->{next_node}"
            for edge in dag['edges']:
                if edge['source'] == curr_node and edge['target'] == next_node:
                    # ✅ 增加 count
                    edge['count'] = edge.get('count', 1) + 1
                    break
    
    # ✅ 重新计算所有边的概率
    self._recompute_transition_probabilities(dag)
    
    # 更新元数据
    existing_proc['metadata']['observation_count'] += 1
    existing_proc['metadata']['updated_at'] = datetime.now().isoformat()

def _recompute_transition_probabilities(self, dag: Dict):
    """
    重新计算转移概率
    
    P(v_j | v_i) = N_ij / Σ_k N_ik
    """
    # 统计每个节点的出边 count
    node_outgoing_counts = defaultdict(int)
    for edge in dag.get('edges', []):
        source = edge['source']
        count = edge.get('count', 1)
        node_outgoing_counts[source] += count
    
    # 计算每条边的概率
    for edge in dag.get('edges', []):
        source = edge['source']
        count = edge.get('count', 1)
        total = node_outgoing_counts[source]
        
        # ✅ 计算转移概率
        edge['prob'] = count / total if total > 0 else 1.0
```

#### 调用位置

```python
def _update_existing_procedure(self, matched_proc_id: str, clip_info: Dict):
    """更新已有 Procedure"""
    existing_proc = self.current_nstf['procedure_nodes'][matched_proc_id]
    
    # 1. 更新 episodic_links
    self._add_episodic_link(existing_proc, clip_info)
    
    # 2. EMA 更新 embeddings
    self._update_embeddings_ema(existing_proc, clip_info)
    
    # ✅ 3. 更新 DAG 转移统计（新增）
    self._update_dag_transitions(existing_proc, clip_info)
```

---

### 5.4 优先级 P1：启用 DAG 融合 🟡

#### 修改文件
`nstf_builder/incremental_builder.py`

#### 当前代码（L600-650）
```python
def _match_and_merge_procedure(self, new_proc: Dict, clip_info: Dict) -> str:
    """匹配并可能融合 Procedure"""
    match_result = self.matcher.find_best_match(
        new_proc, 
        self.current_nstf['procedure_nodes']
    )
    
    if match_result['should_merge']:
        # 更新已有 Procedure
        self._update_existing_procedure(match_result['proc_id'], clip_info)
        return match_result['proc_id']
    else:
        # 创建新 Procedure
        new_id = self._create_new_procedure(new_proc, clip_info)
        return new_id
```

#### 修正后代码
```python
def _match_and_merge_procedure(self, new_proc: Dict, clip_info: Dict) -> str:
    """匹配并可能融合 Procedure"""
    match_result = self.matcher.find_best_match(
        new_proc, 
        self.current_nstf['procedure_nodes']
    )
    
    if match_result['should_merge']:
        existing_proc = self.current_nstf['procedure_nodes'][match_result['proc_id']]
        
        # ✅ 检查是否需要 DAG 融合（相似但步骤不同）
        if self._should_fuse_dags(existing_proc, new_proc):
            # 执行 DAG 融合
            fused_proc = self.fusion_manager.fuse(
                existing_proc, 
                new_proc,
                observation_counts={
                    existing_proc['proc_id']: existing_proc['metadata']['observation_count'],
                    'new': 1
                }
            )
            
            # 更新图谱
            self.current_nstf['procedure_nodes'][match_result['proc_id']] = fused_proc
            
            if self.debug:
                print(f"    ✅ DAG 融合: {match_result['proc_id']}")
        else:
            # 简单更新（无需融合）
            self._update_existing_procedure(match_result['proc_id'], clip_info)
        
        return match_result['proc_id']
    else:
        new_id = self._create_new_procedure(new_proc, clip_info)
        return new_id

def _should_fuse_dags(self, proc1: Dict, proc2: Dict) -> bool:
    """判断是否需要 DAG 融合"""
    steps1 = [s.get('action', '') for s in proc1.get('steps', [])]
    steps2 = [s.get('action', '') for s in proc2.get('steps', [])]
    
    # 如果步骤序列不完全一致，且相似度高，则融合
    if steps1 != steps2:
        # 使用 DAGFusion 的 should_fuse 判断
        return self.fusion_manager.dag_fusion.should_fuse(proc1, proc2)
    
    return False
```

---

### 5.5 优先级 P2：优化 Goal 生成质量 🟡

#### 修改文件
`nstf_builder/prompts/extraction_prompts.py`

#### 改进 Prompt

```python
PROCEDURE_EXTRACTION_PROMPT = """
从以下视频描述中提取程序性知识（Procedure）。

**要求**:
1. **Goal 必须具体明确**:
   - ✅ 好: "将鸡蛋放入冰箱的冷藏抽屉"
   - ❌ 差: "整理厨房物品"
   
   - ✅ 好: "检查西兰花的新鲜度并决定存储位置"
   - ❌ 差: "处理蔬菜"

2. **步骤必须可操作**:
   - 每个步骤包含: action (动作), object (对象), location (位置)
   - 避免模糊动词如 "处理"、"整理"
   - 使用具体动词如 "检查"、"放置"、"切割"

3. **识别分支路径**:
   - 如果存在多种执行方式，在 steps 中标记 alternatives
   - 示例: {"action": "选择容器", "alternatives": ["plastic_bag", "glass_container"]}

4. **proc_type 分类**:
   - task: 具体任务（如 "切肉"、"收纳杂物"）
   - habit: 行为习惯（必须有明确主体，如 "person_1 总是检查蔬菜"）
   - trait: 性格特征（基于多次观察）
   - social: 社交互动模式

视频描述:
{clip_content}

角色映射:
{character_mapping}

请以 JSON 格式返回。
"""
```

---

### 5.6 优先级 P2：改进提示词 🟢

#### 修改文件
`qa_system/prompts/system_prompt.py`

```python
SYSTEM_PROMPT = """
你是一个专业的视频问答助手。根据提供的知识回答问题。

**可用知识源**:
1. **Memory Bank (事实库)**: 包含角色外观、动作、对话、空间细节
   - 格式: CLIP_X 包含时间戳 X 的视频片段描述
   
2. **NSTF Graphs (程序知识图谱)**: 结构化的程序性知识
   - 任务步骤 (如何做某事)
   - 角色习惯和行为模式
   - 性格特征
   - 社交互动模式

**回答策略**:

1. **事实问题** (who/what/where/when):
   ✅ 优先使用 Memory Bank (CLIP_X)
   ✅ 如果 NSTF 提供了相关 Procedure，检查其 episodic_links 追溯证据
   ❌ 不要仅基于 NSTF Goal 推测，必须有具体 clip 证据

2. **程序问题** (how to/steps):
   ✅ 优先使用 NSTF Procedures
   ✅ 注意: 部分 Procedure 可能包含多个执行路径（查看 steps 中的 alternatives）
   ⚠️ NSTF 覆盖率约 77%，如果未找到相关 Procedure，明确说明

3. **角色理解** (personality/habits):
   ✅ 查找 proc_type=habit 或 trait 的 Procedure
   ✅ 使用 episodic_links 追溯具体视频证据
   
4. **约束问题** (without X/if missing):
   ✅ 查找 NSTF 中的 alternative paths
   ⚠️ 当前 DAG 分支支持有限，如果找不到替代方案，诚实说明

**重要提示**:
- 角色名称: 视频中无法获取真实姓名，使用 character_X 或 person_X 标识
- NSTF 局限: 并非所有视频内容都转化为 Procedure，某些细节可能只在 Memory Bank 中
- 证据溯源: 回答时引用具体的 CLIP_X 或 Procedure ID 作为证据
- ⚠️ 如果知识不足，明确说明"提供的知识不包含此信息"，不要猜测

**当前问题**: {question}
"""
```

---

## 6. 实施优先级

### 6.1 紧急修复（1-2 天）

| 任务 | 文件 | 工作量 | 影响 |
|------|------|--------|------|
| ✅ 修复多粒度检索 | `retriever_nstf.py` | 4h | 立即提升召回率 20-30% |
| ✅ 实现 Type-Aware Re-ranking | `hybrid_retriever.py` | 6h | 修复 Factual 问题误判 |
| ✅ 字段名统一 | `retriever_nstf.py` | 2h | 避免 embedding 错误 |

### 6.2 核心功能（3-5 天）

| 任务 | 文件 | 工作量 | 影响 |
|------|------|--------|------|
| ✅ DAG 边转移统计 | `incremental_builder.py` | 8h | 支持概率推理 |
| ✅ 启用 DAG 融合 | `incremental_builder.py` | 6h | 支持多路径查询 |
| ✅ 混合 Factual 检索 | `hybrid_retriever.py` | 4h | 提升 Factual 准确率 |

### 6.3 质量优化（1 周）

| 任务 | 文件 | 工作量 | 影响 |
|------|------|--------|------|
| ✅ 改进 Goal 生成 | `extraction_prompts.py` | 4h | 提升图谱质量 |
| ✅ 优化提示词 | `system_prompt.py` | 3h | 降低 LLM 误判 |
| ✅ 增加覆盖率检查 | `episodic_linker.py` | 6h | 减少证据缺失 |

### 6.4 验证测试（2-3 天）

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 单元测试 | 测试多粒度检索的加权公式 | 4h |
| 集成测试 | 测试 Type-Aware Re-ranking 决策 | 6h |
| 回归测试 | 重新运行 kitchen_03 的 14 个问题 | 4h |
| 分析报告 | 生成新的诊断报告对比改进效果 | 3h |

---

## 7. 预期效果

### 7.1 定量指标

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 平均检索相似度 | 0.27-0.42 | 0.50-0.75 | +70% |
| Factual 问题准确率 | ~50% | >80% | +60% |
| Procedural 命中率 | 60% | >85% | +42% |
| 平均检索轮数 | 2.5 | <2.0 | -20% |

### 7.2 定性改进

- ✅ **检索相关性**: 多粒度加权后，相关 Procedure 排名提升
- ✅ **问题分类**: Factual 问题不再强制使用 NSTF
- ✅ **证据追溯**: DAG 边统计支持更可靠的概率推理
- ✅ **多路径支持**: 融合后的 DAG 可回答约束查询

---

## 8. 风险与缓解

### 8.1 风险识别

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 修改引入新 bug | 中 | 高 | 充分单元测试 + 代码审查 |
| 检索速度下降 | 低 | 中 | 性能测试 + 必要时优化 |
| LLM 适应新格式 | 低 | 低 | 渐进式 Prompt 调整 |

### 8.2 回滚计划

- 保留当前版本为 `v2.3.2_backup`
- 新版本命名为 `v2.4.0_fixed`
- 如果回归测试失败，回滚到 backup

---

## 9. 总结

### 9.1 核心问题

NSTF 检索系统存在 **2 个严重的实现缺陷**:
1. **多粒度检索未按论文实现** - 使用了单一 max 策略而非加权组合
2. **Type-Aware Re-ranking 完全缺失** - 导致 Factual 问题误用 NSTF

这两个问题直接导致:
- 检索相似度偏低（0.27-0.42）
- Factual 问题准确率低（~50%）
- 多轮检索效率差

### 9.2 解决路径

按 **P0 → P1 → P2** 优先级逐步修复:
1. **立即修复**: 多粒度检索 + Type-Aware Re-ranking (1-2 天)
2. **核心功能**: DAG 统计更新 + 融合启用 (3-5 天)
3. **质量优化**: Goal 生成 + 提示词改进 (1 周)

### 9.3 预期提升

修复后预期:
- 检索相似度提升至 0.50-0.75（+70%）
- Factual 准确率 >80%（+60%）
- 平均检索轮数 <2.0（-20%）

---

**报告结束**

*生成时间*: 2026-02-04  
*版本*: v1.0  
*状态*: 待审核与实施
