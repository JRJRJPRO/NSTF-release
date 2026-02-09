# NSTF 图谱分析报告

**视频:** `kitchen_03`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:31  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_03_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_03_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_03.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_03`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **31**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 31/31 | 100% |
| type | ✅ | 31/31 | 100% |
| goal | ✅ | 31/31 | 100% |
| description | ✅ | 31/31 | 100% |
| proc_type | ✅ | 31/31 | 100% |
| embeddings | ✅ | 31/31 | 100% |
| dag | ✅ | 31/31 | 100% |
| steps | ✅ | 31/31 | 100% |
| episodic_links | ✅ | 31/31 | 100% |
| metadata | ✅ | 31/31 | 100% |

### proc_type 分布

- `task`: 19
- `social`: 7
- `trait`: 3
- `habit`: 2

### Steps 统计

- 总数: **120**
- 范围: 1 - 8
- 平均: 3.9
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 10 (avg: 5.9)
- edges 数量: 2 - 9 (avg: 4.9)

### Episodic Links 统计

- 数量范围: 1 - 10
- 平均: 1.8
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **31/31**
- Steps/DAG 一致: **31/31**
✅ 所有 Procedure 都有有效的 DAG 结构

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
- 有分支的 DAG: **1/31**
✅ 有 1 个 DAG 包含分支结构

**分支结构示例:**
- `kitchen_03_proc_20`: START→2条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **74**
- NSTF 引用的 clips: **57**
- 覆盖率: **77.0%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[0, 23, 27, 34, 35, 39, 41, 44, 49, 53, 57, 59, 60, 63, 65, 67, 73]`

## 6. Goal 质量分析

- 总 Procedure 数: **31**
- 模糊 Goal 数: 1
- 具体 Goal 数: 16

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `kitchen_03_proc_4`: Organize items unpacked from a white plastic bag in the kitchen

### 所有 Goals

- Store groceries in the refrigerator
- Person_2's habit of checking produce before storing
- person_1 uses a smartphone for searching while unpacking groceries
- Organize items unpacked from a white plastic bag in the kitchen
- Preserving broccoli for later use
- person_1 and person_2 discuss past meat purchases
- Two individuals (both referred to as person_1) attempt to recall a shared memory.
- person_1 approaches person_2 and person_3 at the counter
- person_1 cuts a piece of meat on a wooden cutting board in the kitchen.
- Package raw meat and a white bag into a larger container
- Sort plastic bags at the kitchen counter
- Prepare chicken patty for a chicken side dish
- Unpack and verify purchased groceries by person_1
- Dispose of the plastic bag
- person_7 instructs person_14 to put the milk
- Packing groceries including olive oil
- person_1 shows their home office to person_8, including details requested by person_8
- person_5 expresses sudden interest in juice
- Plan what to eat this week
- person_1 proposes an action to person_2
- Collaboratively plan a simple meal for Friday
- person_1 picks up a bottle, sets it down, and then picks up a pen from the kitchen counter.
- Initiating and preparing to make a shopping list for next week
- Collaborate on household planning for grocery shopping
- To describe person_1's communication behavior of gesturing with person_1's hands while speaking.
- Identify person_1's patient and encouraging demeanor
- Cleaning and organizing the white table and its immediate surroundings
- person_1 and person_2 clean the kitchen
- Retrieve a yellow folder from the cabinet, place it on the counter, and return to the cabinet
- Pick up the purple tissue box from the white countertop
- Plan to put the rubbish, clean the kitchen, and check when the supermarket closes

## 7. Character Mapping 分析

- 映射条目数: **67**
- face_* 映射: 2
- voice_* 映射: 65
- 映射到的 person 数: 13
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_12', 'person_13', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_03_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Store groceries in the refrigerator
- description: person_1 and person_2 are in a modern kitchen. person_1 suggests storing items in the refrigerator, ...

**Steps 详情:**
- 数量: 7
- Step 1: `{action='hold', object='carton of eggs', location='modern kitchen'}`
- Step 2: `{action='open', object='white reusable shopping bag', location='modern kitchen'}`
- Step 3: `{action='check quantity', object='eggs', location='modern kitchen'}`
- Step 4: `{action='check integrity', object='eggs', location='modern kitchen'}`
- Step 5: `{action='ask for storage location', object='N/A', location='modern kitchen'}`
- ... 还有 2 个步骤

**DAG 结构详情:**
- 节点数: 9, 边数: 8

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"
- `[step_3]`: type=`action`, label="N/A"
- `[step_4]`: type=`action`, label="N/A"
- `[step_5]`: type=`action`, label="N/A"
- `[step_6]`: type=`action`, label="N/A"
- ... 还有 1 个节点

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → step_3 (prob=1.0)`
- Edge 4: `step_3 → step_4 (prob=1.0)`
- Edge 5: `step_4 → step_5 (prob=1.0)`
- Edge 6: `step_5 → step_6 (prob=1.0)`
- ... 还有 2 条边

**Episodic Links 详情:**
- 数量: 3
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`5`, relevance=`update`, similarity=`0.7377`
- Link 3: clip_id=`28`, relevance=`update`, similarity=`0.7117`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T10:36:35.095106
- `updated_at`: 2026-02-04T10:45:40.248613
- `source`: incremental_nstf
- `observation_count`: 3
- `source_clips`: [1, 5, 28]
- `version`: 2.3.2

### Procedure 2: `kitchen_03_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `habit`
- goal: Person_2's habit of checking produce before storing
- description: Person_2 consistently examines produce for freshness and damage, verbally confirming the check and t...

**Steps 详情:**
- 数量: 6
- Step 1: `{action='receives', object='green melon', location='modern kitchen'}`
- Step 2: `{action='says', object='N/A', location='modern kitchen'}`
- Step 3: `{action='examines', object='melon', location='modern kitchen'}`
- Step 4: `{action='says', object='N/A', location='modern kitchen'}`
- Step 5: `{action='puts', object='melon', location='crisper drawer'}`
- ... 还有 1 个步骤

**DAG 结构详情:**
- 节点数: 8, 边数: 7

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"
- `[step_3]`: type=`action`, label="N/A"
- `[step_4]`: type=`action`, label="N/A"
- `[step_5]`: type=`action`, label="N/A"
- `[step_6]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → step_3 (prob=1.0)`
- Edge 4: `step_3 → step_4 (prob=1.0)`
- Edge 5: `step_4 → step_5 (prob=1.0)`
- Edge 6: `step_5 → step_6 (prob=1.0)`
- ... 还有 1 条边

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`2`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T10:36:58.638220
- `updated_at`: 2026-02-04T10:36:58.638244
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [2]
- `version`: 2.3.2

### Procedure 3: `kitchen_03_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `habit`
- goal: person_1 uses a smartphone for searching while unpacking groceries
- description: person_1 demonstrates a habit of holding and using a smartphone for searching, specifically mentioni...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='unpacking', object='groceries', location='modern kitchen'}`
- Step 2: `{action='holding', object='smartphone', location='N/A'}`
- Step 3: `{action='saying 'I like to search for the Jesus.'', object='N/A', location='N/A'}`
- Step 4: `{action='unpacking (while potentially using the smartphone for searching)', object='groceries', location='modern kitchen'}`

**DAG 结构详情:**
- 节点数: 6, 边数: 5

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"
- `[step_3]`: type=`action`, label="N/A"
- `[step_4]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → step_3 (prob=1.0)`
- Edge 4: `step_3 → step_4 (prob=1.0)`
- Edge 5: `step_4 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`3`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T10:37:29.052486
- `updated_at`: 2026-02-04T10:37:29.052511
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [3]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (0 个)

✅ 无警告

### 总体评估

✅ **图谱结构完整，无明显问题**