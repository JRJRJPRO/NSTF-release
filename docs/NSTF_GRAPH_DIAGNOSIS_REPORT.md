# NSTF 图谱诊断报告

**分析日期**: 2026-02-04  
**分析对象**: kitchen_03_nstf.pkl  
**分析文件**: 
- 论文: `article/TWCS-KDD-25-/method_maxultra.tex`
- 构建代码: `NSTF_MODEL/nstf_builder/`
- 分析程序: `NSTF_MODEL/analysis_graph/analyze_nstf.py`
- 分析结果: `NSTF_MODEL/analysis_graph/reports/kitchen_03_robot_report.md`

---

## 一、问题汇总

根据分析报告，发现以下问题：

| 问题ID | 严重程度 | 问题描述 | 影响 |
|--------|----------|----------|------|
| P1 | 🔴 严重 | `kitchen_03_proc_19` 的 DAG 结构为空（0节点0边） | 无法进行符号推理 |
| P2 | 🔴 严重 | `kitchen_03_proc_19` 缺少 `step_emb`、`proc_type` | 双层检索失效 |
| P3 | 🟡 中等 | 27/30 个 Procedure 的边 count=1 未更新 | 转移概率无意义 |
| P4 | 🟡 中等 | 28/30 个 DAG 是线性结构，仅 1 个有分支 | 未体现多路径融合 |

---

## 二、根因分析

### 问题 P1 & P2: DAG 融合时丢失结构

**现象**: `kitchen_03_proc_19` 经过融合后，DAG 变成空的 `{nodes: {}, edges: []}`

**根因**: `dag_fusion.py` 的 `fuse()` 方法**没有正确合并 DAG 结构**

**证据**:

1. 查看 `dag_fusion.py` 第 153-176 行的 `fuse()` 方法返回值：

```python
# 构建融合后的 procedure
fused_proc = {
    'proc_id': proc1.get('proc_id', 'fused_proc'),
    'type': 'procedure',
    'goal': self._merge_goals(...),
    'steps': merged_steps,
    'edges': merged_edges,           # ← 只合并了 edges 列表
    'episodic_links': merged_links,
    'embeddings': {
        'goal_emb': merged_embedding  # ← 只有 goal_emb，缺少 step_emb！
    },
    ...
    # ⚠️ 关键问题：没有 'dag' 字段！
    # ⚠️ 关键问题：没有 'proc_type' 字段！
}
```

2. 融合后的 `fused_proc` 缺少以下关键字段：
   - **`dag`**: 完整的 DAG 结构（包含 nodes 和 edges）
   - **`step_emb`**: 步骤均值向量
   - **`proc_type`**: 程序类型（task/habit/trait/social）
   - **`anchor_goal_emb`** / **`anchor_step_emb`**: 锚点向量

3. 分析报告中的 `fusion_info` 证实了融合发生：
```
fusion_info:
  source_procs: ['kitchen_03_proc_19', 'kitchen_03_proc_22']
  num_matched_steps: 0
  num_new_steps: 4
  total_steps: 8
```

**论文要求 vs 实现差异**:

| 论文规范 | 实际实现 | 问题 |
|---------|---------|------|
| 融合后保留完整 DAG 结构 `(V, E, A)` | 只保留 `edges` 列表，丢失 `dag.nodes` | DAG 不完整 |
| 双层 Index Vectors `{i_goal, i_step}` | 融合时只保留 `goal_emb` | step_emb 丢失 |
| proc_type 字段必填 | 融合时未复制 | 字段缺失 |

---

### 问题 P3: 边转移计数未更新

**现象**: 27/30 个 Procedure 的所有边 count=1，概率全为 1.0

**根因**: `_update_dag_edge_counts()` 的步骤推断逻辑失效

**证据**:

1. `incremental_builder.py` 第 560-608 行的 `_infer_observed_steps()` 方法使用了 0.6 的高阈值：
```python
MATCH_THRESHOLD = 0.6  # ← 阈值过高
```

2. 当新观测的 steps 与已有 DAG 节点相似度低于 0.6 时，推断失败，边计数不会更新

3. 分析报告显示只有 3/30 的 Procedure 有 count>1 的边

**论文要求**:
```
N_ij ← N_ij + 1  (每次观测到转移时增加计数)
P(v_j|v_i) = N_ij / Σ_k N_ik
```

---

### 问题 P4: 多路径 DAG 缺失

**现象**: 28/30 个 DAG 是线性的 (START→step1→step2→...→GOAL)

**根因**: 
1. 单 clip 只能观测到线性序列
2. `ProcedureMatcher` 的匹配阈值 0.70 可能导致相似程序被判定为不同，从而创建新节点而非合并
3. DAG 融合时的步骤对齐阈值 0.75 过高，导致很多步骤无法对齐

**证据**:

`procedure_matcher.py` 第 30-35 行：
```python
def __init__(
    self,
    match_threshold: float = 0.70,  # ← 可能需要调低
    ...
)
```

`dag_fusion.py` 第 19-22 行：
```python
def __init__(
    self,
    similarity_threshold: float = 0.75,  # ← 步骤对齐阈值
    ...
)
```

---

## 三、分析程序评估

分析程序 `analyze_nstf.py` 基本正确，但有以下改进建议：

### 3.1 已正确检测的问题
- ✅ 字段填充率检查 (发现了 proc_type, dag 缺失)
- ✅ DAG 结构完整性检查 (发现了 START/GOAL 缺失)
- ✅ steps 与 dag.nodes 一致性检查
- ✅ 边转移统计分析

### 3.2 建议增强的检测项

| 检测项 | 当前状态 | 建议 |
|--------|----------|------|
| 融合后字段完整性 | ❌ 未检测 | 检查 fusion_info 存在时，验证所有必需字段 |
| step_emb 与 steps 一致性 | ❌ 未检测 | 当 steps>0 时，step_emb 应存在 |
| 锚点向量检查 | ❌ 未检测 | 增量更新后应有 anchor_*_emb |

---

## 四、解决方案

### 4.1 修复 DAG 融合 (dag_fusion.py)

**修复点 1**: 在 `fuse()` 方法中构建完整 DAG

```python
# 在 fused_proc 中添加：

# 1. 从 merged_steps 重建 DAG 结构
fused_dag = self._construct_merged_dag(merged_steps, merged_edges)

fused_proc = {
    ...
    'dag': fused_dag,  # ← 添加完整 DAG
    'proc_type': proc1.get('proc_type') or proc2.get('proc_type') or 'task',  # ← 添加 proc_type
    'embeddings': {
        'goal_emb': merged_embedding,
        'step_emb': self._merge_step_embeddings(proc1, proc2),  # ← 添加 step_emb
        'anchor_goal_emb': proc1.get('embeddings', {}).get('anchor_goal_emb'),
        'anchor_step_emb': proc1.get('embeddings', {}).get('anchor_step_emb'),
    },
    ...
}
```

**修复点 2**: 添加 `_construct_merged_dag()` 方法

```python
def _construct_merged_dag(self, steps: List[Dict], edges: List[Dict]) -> Dict:
    """从合并后的 steps 和 edges 构建完整 DAG"""
    nodes = {
        'START': {'type': 'control', 'attributes': {}},
        'GOAL': {'type': 'control', 'attributes': {}}
    }
    
    for s in steps:
        step_id = s.get('step_id', '')
        if step_id:
            nodes[step_id] = {
                'type': 'action',
                'action': s.get('action', ''),
                'attributes': {
                    'object': s.get('object', ''),
                    'location': s.get('location', ''),
                    'actor': s.get('actor', ''),
                }
            }
    
    # 转换 edges 格式
    dag_edges = []
    for e in edges:
        dag_edges.append({
            'from': e.get('from_step', e.get('from', '')),
            'to': e.get('to_step', e.get('to', '')),
            'count': e.get('observation_count', e.get('count', 1)),
            'probability': e.get('probability', 1.0),
        })
    
    return {'nodes': nodes, 'edges': dag_edges}
```

**修复点 3**: 添加 `_merge_step_embeddings()` 方法

```python
def _merge_step_embeddings(self, proc1: Dict, proc2: Dict) -> np.ndarray:
    """合并 step embeddings"""
    emb1 = proc1.get('embeddings', {}).get('step_emb')
    emb2 = proc2.get('embeddings', {}).get('step_emb')
    
    if emb1 is None and emb2 is None:
        # 从 steps 重新计算
        steps = proc1.get('steps', []) + proc2.get('steps', [])
        if steps:
            actions = [s.get('action', '') for s in steps if isinstance(s, dict)]
            if actions:
                embs = batch_get_normalized_embeddings(actions)
                merged = np.mean(embs, axis=0)
                return merged / (np.linalg.norm(merged) + 1e-8)
        return np.zeros(3072)
    
    if emb1 is None:
        return emb2
    if emb2 is None:
        return emb1
    
    # EMA 合并
    merged = self.ema_alpha * emb2 + (1 - self.ema_alpha) * emb1
    return merged / (np.linalg.norm(merged) + 1e-8)
```

### 4.2 降低阈值以增加多路径 DAG

**incremental_builder.py**:
```python
# _infer_observed_steps() 中
MATCH_THRESHOLD = 0.5  # 从 0.6 降低到 0.5
```

**config/default.json**:
```json
{
    "match_threshold": 0.65,        // 从 0.70 降低
    "step_align_threshold": 0.70,   // 从 0.75 降低
    "fusion_similarity_threshold": 0.75  // 从 0.80 降低
}
```

### 4.3 增强分析程序

在 `analyze_nstf.py` 中添加融合后完整性检查：

```python
def analyze_fusion_integrity(self) -> None:
    """检查融合后的 Procedure 完整性"""
    for proc_id, proc in proc_nodes.items():
        if 'fusion_info' in proc:
            # 融合后的节点应有完整字段
            required_after_fusion = ['dag', 'proc_type', 'steps']
            for field in required_after_fusion:
                if field not in proc or not proc[field]:
                    self.errors.append(f"{proc_id}: 融合后缺少 {field}")
            
            # 检查 embeddings 完整性
            embs = proc.get('embeddings', {})
            if 'step_emb' not in embs:
                self.errors.append(f"{proc_id}: 融合后缺少 step_emb")
```

---

## 五、验证清单

修复后，重新构建图谱并验证：

```bash
# 1. 重新构建
python experiments/build_nstf.py --dataset robot --videos kitchen_03 --mode incremental --force

# 2. 重新分析
python -m analysis_graph.analyze_nstf kitchen_03 --dataset robot

# 3. 检查关键指标
```

| 指标 | 修复前 | 期望修复后 |
|------|--------|-----------|
| DAG 完整 (有 nodes+edges) | 29/30 | 30/30 |
| step_emb 存在 | 29/30 | 30/30 |
| proc_type 存在 | 29/30 | 30/30 |
| 有分支的 DAG | 1/30 | ≥5/30 |
| count>1 的 Procedure | 3/30 | ≥10/30 |

---

## 六、总结

### 问题分类

| 分类 | 问题 | 根因 |
|------|------|------|
| **代码设计与论文不一致** | - | - |
| **代码实现错误/疏忽** | P1, P2 | DAG 融合时未复制关键字段 |
| **分析程序问题** | - | 基本正确，建议增强 |
| **参数配置问题** | P3, P4 | 阈值过高导致更新/融合不充分 |

### 优先级建议

1. **紧急**: 修复 `dag_fusion.py` 的 `fuse()` 方法 (P1, P2)
2. **重要**: 调整阈值参数 (P3, P4)
3. **建议**: 增强分析程序的检测能力

---

*报告生成时间: 2026-02-04*
