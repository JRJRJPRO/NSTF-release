# NSTF 图谱实现分析报告

**分析日期**: 2026-02-04  
**分析者**: Claude AI  
**分析对象**: NSTF_MODEL/nstf_builder 模块及其产出图谱
**状态**: ✅ 已修复 (V2.3.2)

---

## 〇、修复摘要 (V2.3.2)

| 问题 | 修复状态 | 修复位置 |
|-----|---------|---------|
| 缺少查询函数 F | ✅ 已修复 | `symbolic_query.py` (新增) |
| DAG 转移计数未更新 | ✅ 已修复 | `incremental_builder.py` |
| proc_type 允许无效组合值 | ✅ 已修复 | `incremental_builder.py`, `extractor.py` |
| 分析程序版本检查过期 | ✅ 已修复 | `analyze_nstf.py` |
| 缺少 steps/dag 一致性检查 | ✅ 已修复 | `analyze_nstf.py` |

---

## 一、概述

本报告对照论文 `method_maxultra.tex` (NS-Mem框架)，分析 `nstf_builder` 的实现代码与实际产出图谱 (`kitchen_03_nstf.pkl`)，识别潜在问题。

### 分析维度
1. **设计意图一致性** - 代码设计是否符合论文架构
2. **实现细节正确性** - 代码执行是否产生预期结果
3. **分析程序准确性** - 分析工具是否正确反映图谱状态
4. **潜在隐藏问题** - 分析未覆盖但可能存在的问题

---

## 二、论文核心要求 vs 实现对照

### 2.1 Logic Node 结构 (§4.1.3)

| 论文要求 | 代码实现 | 图谱实际 | 状态 |
|---------|---------|---------|------|
| `id` - 唯一标识 | ✓ `proc_id` | ✓ `kitchen_03_proc_1` 等 | ✅ 正确 |
| `c` - 目标描述 | ✓ `goal` | ⚠️ 部分过于抽象 | ⚠️ 需改进 |
| `I` - 双层 Index Vectors | ✓ `goal_emb`, `step_emb` | ✓ shape=(3072,) | ✅ 正确 |
| `G` - Procedural DAG | ✓ `dag.nodes`, `dag.edges` | ✓ 含 START/GOAL | ✅ 正确 |
| `F` - 查询函数 | ❌ 未实现 | ❌ 缺失 | ❌ **问题1** |
| `episodic_links` | ✓ 实现 | ✓ 有证据链接 | ✅ 正确 |

### 2.2 SK-Gen 蒸馏流程 (§4.2.2)

| 论文步骤 | 代码实现 | 状态 |
|---------|---------|------|
| Step 1: Action Sequence Extraction | ✓ `get_clip_content()` | ✅ |
| Step 2: PrefixSpan Pattern Mining | ⚠️ `SemanticPatternMiner` 可选 | ⚠️ **问题2** |
| Step 3: LLM Knowledge Verification | ✓ `ProcedureExtractor.detect_in_clip()` | ✅ |
| Step 4: DAG Construction | ✓ `_construct_dag()` | ✅ |
| Step 5: Index Generation | ✓ 双层 embedding | ✅ |

### 2.3 增量维护 (§4.2.3)

| 论文要求 | 代码实现 | 状态 |
|---------|---------|------|
| Matching (神经发现) | ✓ `ProcedureMatcher.match_existing()` | ✅ |
| Gating (阈值过滤) | ✓ `match_threshold=0.70` | ✅ |
| Neural Refinement (EMA) | ✓ `update_with_anchored_ema()` | ✅ |
| Symbolic Refinement (转移计数) | ✓ `_update_dag_edge_counts()` | ⚠️ **问题3** |

### 2.4 DAG 融合 (§4.2.4)

| 论文要求 | 代码实现 | 状态 |
|---------|---------|------|
| Node Alignment (Hungarian) | ✓ `DAGFusion._align_steps()` | ✅ |
| Edge Union | ✓ `_merge_edges()` | ✅ |
| Statistic Pooling | ⚠️ 部分实现 | ⚠️ **问题4** |

---

## 三、发现的问题

### 问题1: 缺少确定性查询函数 F (设计意图不一致)

**论文要求** (§4.3.3):
> 每个 Logic Node $\mathcal{N} = (id, c, \mathbf{I}, \mathcal{G}, \mathcal{F})$ 包含查询函数 $\mathcal{F}$，包括：
> - `getProcedureWithEvidence(goal)` 
> - `queryStepSequence(goal, constraints)`
> - `aggregateCharacterBehaviors(person)`

**代码现状**:
- `ProcedureNode` 字典中**没有** `functions` 或 `F` 字段
- 没有实现确定性查询函数的类或模块
- 图谱只有数据，没有关联的操作接口

**证据** - 分析 [incremental_builder.py#L267-L300](nstf_builder/incremental_builder.py):
```python
return {
    'proc_id': proc_id,
    'type': 'procedure',
    'goal': goal,
    ...
    'dag': dag,
    'embeddings': {...},
    # ❌ 缺少 'functions' 或 'F'
}
```

**影响**: 论文声称的"确定性推理"无法实现，Agent 无法调用 `queryStepSequence` 等函数进行约束查询。

**建议修复**:
```python
# 在 qa_system/ 或 nstf_builder/ 中添加
class SymbolicQueryFunctions:
    @staticmethod
    def getProcedureWithEvidence(proc: Dict) -> Tuple[Dict, List]:
        return proc['dag'], proc['episodic_links']
    
    @staticmethod
    def queryStepSequence(proc: Dict, constraints: Dict) -> List[List[str]]:
        # 实现路径枚举和约束过滤
        ...
    
    @staticmethod
    def aggregateCharacterBehaviors(nstf_graph: Dict, person: str) -> List[Dict]:
        # 实现跨 procedure 聚合
        ...
```

---

### 问题2: PrefixSpan 模式挖掘未实际使用 (实现与论文不一致)

**论文要求** (§4.2.2 Step 2):
> 我们应用 PrefixSpan... 发现重复的程序模式

**代码现状**:
- `pattern_miner.py` 存在但 `incremental_builder.py` 中**未调用**
- 增量构建完全依赖 LLM 逐 clip 检测
- 配置 `use_pattern_mining: true` 但实际未生效

**证据** - 分析 [incremental_builder.py#L611-L700](nstf_builder/incremental_builder.py):
```python
# build() 方法中：
for i, clip_id in enumerate(clips):
    clip_content = self.get_clip_content(graph, clip_id)
    detected = self.extractor.detect_in_clip(clip_content)  # 只用 LLM
    # ❌ 没有调用 pattern_miner.mine_patterns()
```

**影响**: 
- 失去了频繁模式挖掘的去噪能力
- 完全依赖 LLM 判断，可能引入噪声
- 论文中的支持度阈值 $\sigma$ 参数无意义

**建议修复**:
```python
# 在 build() 开始时运行 pattern mining
if self.config.get('use_pattern_mining', False):
    from .pattern_miner import SemanticPatternMiner
    miner = SemanticPatternMiner(min_support=self.config.get('pattern_min_support', 0.2))
    all_contents = [self.get_clip_content(graph, c) for c in clips]
    action_sequences = miner.extract_action_sequences(all_contents)
    frequent_patterns = miner.mine_patterns(action_sequences)
    # 用 frequent_patterns 指导后续的 LLM 验证
```

---

### 问题3: DAG 转移计数更新逻辑不完整 (实现细节错误)

**论文要求** (§4.2.3):
> 每次观测到转移 $v_i \rightarrow v_j$，增加计数: $N_{ij} \leftarrow N_{ij} + 1$

**代码现状** - [incremental_builder.py#L548-L580](nstf_builder/incremental_builder.py):
```python
def _update_dag_edge_counts(self, proc: Dict, detected: Dict):
    new_edges = detected.get('edges', [])  # ⚠️ 问题: detected 经常没有 edges
    
    for new_edge in new_edges:
        # 只有当 detected 提供 edges 时才更新
        ...
```

**问题分析**:
1. `detect_in_clip()` 通常不返回完整的 `edges`
2. 即使返回，也只是新检测到的边，不是"观测到已有边"
3. 实际上大部分更新时 `new_edges` 是空列表

**证据** - 图谱分析报告显示:
```
Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
...
```
所有边的 `prob=1.0`，说明转移计数从未被更新（始终是初始值 count=1）

**建议修复**:
```python
def _update_dag_edge_counts(self, proc: Dict, detected: Dict):
    """
    正确的更新逻辑：
    1. 解析新观测的 action sequence
    2. 映射到已有 DAG 节点
    3. 对匹配的转移增加计数
    """
    dag = proc.get('dag')
    edges = dag.get('edges', [])
    
    # 从 detected 中提取 action 序列
    new_steps = detected.get('steps', [])
    if not new_steps:
        return
    
    # 将 action 映射到已有 step_id
    action_to_step = self._build_action_step_mapping(dag['nodes'])
    observed_sequence = []
    for step in new_steps:
        action = step.get('action', '')
        matched_step_id = self._find_matching_step(action, action_to_step)
        if matched_step_id:
            observed_sequence.append(matched_step_id)
    
    # 更新边计数
    for i in range(len(observed_sequence) - 1):
        from_step = observed_sequence[i]
        to_step = observed_sequence[i + 1]
        for edge in edges:
            if edge.get('from') == from_step and edge.get('to') == to_step:
                edge['count'] = edge.get('count', 1) + 1
                break
    
    self._recompute_edge_probabilities(dag)
```

---

### 问题4: DAG 融合时的统计池化不完整 (实现细节错误)

**论文要求** (§4.2.4):
> statistic pooling: 通过贝叶斯共轭合并转移计数

**代码现状** - [dag_fusion.py#L350-L400](nstf_builder/dag_fusion.py):
```python
def _merge_edges(self, edges1, edges2, ...):
    # 只是简单合并边，没有正确的贝叶斯统计池化
    ...
```

**问题分析**:
- 代码只做了边的 union，没有正确合并 count
- 没有实现论文中的贝叶斯后验计算

**建议修复**:
```python
def _merge_edge_statistics(self, count1, count2, prior_alpha=1.0):
    """
    贝叶斯统计池化：
    posterior_count = count1 + count2 + prior_alpha - 1
    """
    return count1 + count2  # 简化版：直接相加计数
```

---

### 问题5: Goal 描述过于抽象 (LLM Prompt 问题)

**论文要求** (§4.1.2):
> textualized description $\mathbf{d}$... capturing observable actions, dialogues, and scene details

**图谱实际**:
```
⚠️ kitchen_03_proc_2: Robot to place the item 'Jesus' into the 'spinach' (leafy greens container)
⚠️ kitchen_03_proc_6: Manage kitchen items by checking a cabinet...
⚠️ kitchen_03_proc_10: Access the refrigerator to retrieve an item...
```

**证据**: 分析报告显示 `只有 8/27 个 Goal 包含具体信息`

**原因分析** - [extractor.py#L95-L140](nstf_builder/extractor.py):
- Prompt 已要求 "SPECIFIC goal"
- 但 LLM 仍然返回抽象描述
- 没有后处理验证 Goal 质量

**建议修复**:
```python
def _validate_goal_specificity(self, goal: str) -> bool:
    """检查 Goal 是否足够具体"""
    vague_keywords = ['something', 'things', 'stuff', 'item', 'object', 'an item']
    goal_lower = goal.lower()
    return not any(kw in goal_lower for kw in vague_keywords)

def extract_structure(self, contents, procedure):
    ...
    result = self._parse_json(response)
    
    # 质量验证
    if result and not self._validate_goal_specificity(result.get('goal', '')):
        # 重新请求，强调具体性
        retry_prompt = f"The goal '{result['goal']}' is too vague. Rewrite with SPECIFIC objects..."
        result = self._get_gemini_response(retry_prompt)
    
    return result
```

---

### 问题6: proc_type 允许无效值 (分析程序过于宽松)

**Schema 定义**:
```python
VALID_PROC_TYPES = {'task', 'habit', 'trait', 'social'}
```

**图谱实际**:
```
⚠️ kitchen_03_proc_23: 无效 proc_type 'task|social'
```

**问题**: `'task|social'` 不在有效集合中，但只是 warning 而非 error。

**原因** - [analyze_nstf.py#L247](analysis_graph/analyze_nstf.py):
```python
if proc_type and proc_type not in VALID_PROC_TYPES:
    self.warnings.append(...)  # ⚠️ 只是 warning
```

**建议修复**:
- Builder 端：强制 proc_type 只能是单一值
- 分析端：将无效 proc_type 升级为 error

---

### 问题7: 锚点 Embedding 保存但未使用于检索 (设计实现不一致)

**代码现状**:
```python
embeddings = {
    'goal_emb': ...,
    'step_emb': ...,
    'anchor_goal_emb': ...,  # 存在
    'anchor_step_emb': ...,  # 存在
}
```

**问题**: `anchor_*_emb` 只用于漂移检测，但论文中的检索公式只用 `goal_emb` 和 `step_emb`。

这本身不是错误，但可能造成困惑。建议在 README 中说明锚点 embedding 的用途。

---

## 四、分析程序潜在问题

### 4.1 未检查的项目

| 检查项 | analyze_nstf.py 是否检查 | 建议 |
|-------|-------------------------|------|
| steps 与 dag.nodes 一致性 | ❌ | 添加检查 |
| 边的 count > 0 | ❌ | 添加检查 |
| episodic_links 的 clip_id 有效性 | ❌ | 验证 clip_id 存在于 video_graph |
| 双层 embedding 正交性 | ❌ | 检查 goal_emb 与 step_emb 相似度 |
| DAG 可达性 | ❌ | 检查 START → GOAL 是否可达 |

### 4.2 建议添加的检查

```python
def check_steps_dag_consistency(self, proc):
    """检查 steps 列表与 dag.nodes 是否一致"""
    step_ids_from_steps = {s['step_id'] for s in proc.get('steps', []) if isinstance(s, dict)}
    step_ids_from_dag = {k for k in proc['dag']['nodes'].keys() if k not in ['START', 'GOAL']}
    
    if step_ids_from_steps != step_ids_from_dag:
        return f"Steps 与 DAG 不一致: steps有 {step_ids_from_steps}, dag有 {step_ids_from_dag}"
    return None

def check_dag_reachability(self, dag):
    """检查 START 到 GOAL 是否可达"""
    # 使用 BFS 检查
    ...
```

---

## 五、问题优先级排序

| 优先级 | 问题 | 类型 | 影响程度 |
|-------|------|------|---------|
| 🔴 P0 | 缺少查询函数 F | 设计缺失 | Agent 无法执行确定性推理 |
| 🟠 P1 | DAG 转移计数未更新 | 实现错误 | 概率推理无效 |
| 🟠 P1 | PrefixSpan 未使用 | 实现遗漏 | 失去去噪能力 |
| 🟡 P2 | Goal 过于抽象 | Prompt 问题 | 检索质量下降 |
| 🟡 P2 | 统计池化不完整 | 实现不完整 | 融合精度受损 |
| 🟢 P3 | proc_type 无效值 | 验证宽松 | 数据一致性 |

---

## 六、建议的修复方案

### 阶段1: 紧急修复 (解决 P0)

1. **实现 SymbolicQueryFunctions 类** - 在 `qa_system/` 中添加确定性查询函数
2. **集成到 Agent 接口** - 让 Agent 可以调用 `CallFunction(f, args)`

### 阶段2: 核心修复 (解决 P1)

1. **修复 DAG 转移计数更新** - 实现正确的 action → step 映射和计数更新
2. **集成 PrefixSpan** - 在增量构建前运行模式挖掘

### 阶段3: 质量提升 (解决 P2)

1. **Goal 质量验证** - 添加后处理检查和重试逻辑
2. **完善统计池化** - 实现正确的贝叶斯后验计算

### 阶段4: 工具改进

1. **增强分析程序** - 添加 steps/dag 一致性检查、可达性检查
2. **添加单元测试** - 验证各组件的正确性

---

## 七、结论

### 整体评估

| 维度 | 评分 | 说明 |
|-----|------|------|
| 架构一致性 | 🟡 75% | 大部分符合论文，但缺少 F |
| 实现正确性 | 🟠 65% | 核心流程正确，但有细节问题 |
| 分析完整性 | 🟡 70% | 覆盖主要字段，但缺少深度检查 |
| 文档完整性 | 🟢 85% | README 详尽，版本记录清晰 |

### 关键发现

1. **最严重问题**: 缺少确定性查询函数 `F`，这是论文核心创新点之一
2. **实现偏差**: 虽然有 PrefixSpan 代码，但增量构建未实际调用
3. **数据质量**: DAG 转移概率始终为 1.0，说明增量更新的统计功能未生效
4. **图谱有效**: 尽管有上述问题，图谱结构基本正确，可用于基础检索

### 建议

按优先级修复问题，优先实现 **查询函数 F** 和 **修复转移计数更新**，这两项对论文复现最关键。

---

*报告生成时间: 2026-02-04*
