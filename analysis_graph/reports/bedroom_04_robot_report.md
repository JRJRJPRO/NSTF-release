# NSTF 图谱分析报告

**视频:** `bedroom_04`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:30  
**NSTF 路径:** `data/nstf_graphs/robot/bedroom_04_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/bedroom_04_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/bedroom_04.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `bedroom_04`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **7**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 7/7 | 100% |
| type | ✅ | 7/7 | 100% |
| goal | ✅ | 7/7 | 100% |
| description | ✅ | 7/7 | 100% |
| proc_type | ✅ | 7/7 | 100% |
| embeddings | ✅ | 7/7 | 100% |
| dag | ✅ | 7/7 | 100% |
| steps | ✅ | 7/7 | 100% |
| episodic_links | ✅ | 7/7 | 100% |
| metadata | ✅ | 7/7 | 100% |

### proc_type 分布

- `task`: 4
- `social`: 3

### Steps 统计

- 总数: **19**
- 范围: 1 - 5
- 平均: 2.7
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 7 (avg: 4.7)
- edges 数量: 2 - 6 (avg: 3.7)

### Episodic Links 统计

- 数量范围: 1 - 1
- 平均: 1.0
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **7/7**
- Steps/DAG 一致: **7/7**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 1
- count 均值: 1.00
- 所有 count=1 的 Procedure: 7/7
⚠️ 所有 Procedure 的 count 都未更新！

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 7/7
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 7/7
- 有分支的 DAG: **0/7**
⚠️ 没有任何 DAG 有分支结构！

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **55**
- NSTF 引用的 clips: **7**
- 覆盖率: **12.7%**
❌ 覆盖率过低 (<30%)！大量视频内容未被程序覆盖
- 未覆盖的 clips: `[0, 1, 5, 6, 7, 8, 9, 10, 11, 12]...` (共 48 个)

## 6. Goal 质量分析

- 总 Procedure 数: **7**
- 模糊 Goal 数: 0
- 具体 Goal 数: 2
⚠️ 只有 2/7 个 Goal 包含具体信息

### 所有 Goals

- Pour milk from a green carton into a small white cup
- Transporting the bowl of milk through the house
- person_1 expresses a complaint to person_2
- person_1 instructs person_2 to clean the floor
- Picking up the small white device from the nightstand
- person_1 provides verbal affirmations during an interaction with another individual
- Person_1 places a 'Napoleon' poster on the bed and a small brown bottle and a small white container on the bedside table.

## 7. Character Mapping 分析

- 映射条目数: **16**
- face_* 映射: 3
- voice_* 映射: 13
- 映射到的 person 数: 3
- Person IDs: `['person_1', 'person_2', 'person_3']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `bedroom_04_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Pour milk from a green carton into a small white cup
- description: A person wearing black gloves and a red bracelet pours milk from a green carton with Chinese charact...

**Steps 详情:**
- 数量: 1
- Step 1: `{action='pours milk', object='milk, green carton, small white cup', location='countertop'}`

**DAG 结构详情:**
- 节点数: 3, 边数: 2

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`2`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:02:33.320139
- `updated_at`: 2026-02-04T13:02:33.320163
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [2]
- `version`: 2.3.2

### Procedure 2: `bedroom_04_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Transporting the bowl of milk through the house
- description: A person prepares a white bowl, fills it with milk, and then carries it through various rooms of a h...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='wipes', object='white bowl', location='kitchen'}`
- Step 2: `{action='carries', object='bowl of milk', location='kitchen'}`
- Step 3: `{action='carries', object='bowl of milk', location='dining area'}`
- Step 4: `{action='enters', object='bowl of milk', location='living room'}`
- Step 5: `{action='walks through', object='bowl of milk', location='hallway'}`

**DAG 结构详情:**
- 节点数: 7, 边数: 6

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"
- `[step_3]`: type=`action`, label="N/A"
- `[step_4]`: type=`action`, label="N/A"
- `[step_5]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → step_3 (prob=1.0)`
- Edge 4: `step_3 → step_4 (prob=1.0)`
- Edge 5: `step_4 → step_5 (prob=1.0)`
- Edge 6: `step_5 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`3`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:02:50.008701
- `updated_at`: 2026-02-04T13:02:50.008725
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [3]
- `version`: 2.3.2

### Procedure 3: `bedroom_04_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 expresses a complaint to person_2
- description: person_1 initiates a social interaction to express a complaint to person_2, using a piece of paper a...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='holds a piece of paper', object='a piece of paper', location='N/A'}`
- Step 2: `{action='gestures towards person_1', object='N/A', location='N/A'}`
- Step 3: `{action='states "Have something to complain with you."', object='N/A', location='N/A'}`

**DAG 结构详情:**
- 节点数: 5, 边数: 4

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"
- `[step_3]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → step_3 (prob=1.0)`
- Edge 4: `step_3 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`4`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:03:10.298932
- `updated_at`: 2026-02-04T13:03:10.298956
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [4]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (1 个)

- ❌ Episodic 覆盖率过低: 12.7%

### 警告 (3 个)

- ⚠️ 所有边的转移计数未被更新
- ⚠️ 所有 DAG 都是线性结构，无分支
- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱存在 1 个问题，建议修复**