# NSTF 图谱分析报告

**视频:** `kitchen_17`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:34  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_17_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_17_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_17.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_17`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **21**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 21/21 | 100% |
| type | ✅ | 21/21 | 100% |
| goal | ✅ | 21/21 | 100% |
| description | ✅ | 21/21 | 100% |
| proc_type | ✅ | 21/21 | 100% |
| embeddings | ✅ | 21/21 | 100% |
| dag | ✅ | 21/21 | 100% |
| steps | ✅ | 21/21 | 100% |
| episodic_links | ✅ | 21/21 | 100% |
| metadata | ✅ | 21/21 | 100% |

### proc_type 分布

- `task`: 13
- `social`: 6
- `trait`: 2

### Steps 统计

- 总数: **72**
- 范围: 1 - 7
- 平均: 3.4
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 5.4)
- edges 数量: 2 - 8 (avg: 4.4)

### Episodic Links 统计

- 数量范围: 1 - 6
- 平均: 1.6
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **21/21**
- Steps/DAG 一致: **21/21**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 2
- count 均值: 1.03
- 所有 count=1 的 Procedure: 20/21
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 21/21
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 21/21
- 有分支的 DAG: **0/21**
⚠️ 没有任何 DAG 有分支结构！

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **65**
- NSTF 引用的 clips: **34**
- 覆盖率: **52.3%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[0, 1, 2, 5, 6, 9, 10, 15, 20, 26]...` (共 31 个)

## 6. Goal 质量分析

- 总 Procedure 数: **21**
- 模糊 Goal 数: 5
- 具体 Goal 数: 9

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `kitchen_17_proc_4`: person_11 to assemble something on the counter
- ⚠️ `kitchen_17_proc_5`: person_1 organizes and puts away items and a light green bowl
- ⚠️ `kitchen_17_proc_8`: Organizing items in the kitchen area
- ⚠️ `kitchen_17_proc_11`: Clear all the things inside the refrigerator
- ⚠️ `kitchen_17_proc_15`: Wash dishes and find a storage location for a washed item

### 所有 Goals

- Demonstrate person_1's aversion to mess and unhygienic conditions in the kitchen
- person_1 checks the contents of the refrigerator in the kitchen
- person_1 requests a 'look' from person_2, and person_2 expresses compliance.
- person_11 to assemble something on the counter
- person_1 organizes and puts away items and a light green bowl
- Clean the bathroom mirror and transition to the kitchen area for further activities
- person_1 and person_2 communicate about household chores and mutual assistance in the kitchen.
- Organizing items in the kitchen area
- Secure metal tools in double-layered plastic bags
- person_2 cleaning the staircase
- Clear all the things inside the refrigerator
- person_1 shows affection or comfort to person_2
- Performing actions related to a red cabinet and retrieving a green bottle
- To demonstrate person_1's meticulous and detail-oriented trait regarding audio clarity
- Wash dishes and find a storage location for a washed item
- person_8 cleans the lower part of the red refrigerator
- person_2 informs person_1 that the trash on the counter needs to be placed in the box of the list.
- Accessing an upper cabinet and then sitting at the kitchen counter
- Retrieve and hand over a green package of instant noodles from the red cabinet.
- person_1, person_2, and person_3 decide what to eat for dinner
- person_1 introduces the dining hall to person_2

## 7. Character Mapping 分析

- 映射条目数: **60**
- face_* 映射: 2
- voice_* 映射: 58
- 映射到的 person 数: 13
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_12', 'person_13', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_17_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `trait`
- goal: Demonstrate person_1's aversion to mess and unhygienic conditions in the kitchen
- description: person_1 enters a cluttered kitchen, observes empty coffee cups and used plates, and expresses disgu...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='enters and observes', object='N/A', location='kitchen'}`
- Step 2: `{action='comments on', object='empty coffee cups, used plates', location='counter'}`
- Step 3: `{action='expresses disgust', object='N/A', location='kitchen'}`

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
- Link 1: clip_id=`3`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:31:09.578123
- `updated_at`: 2026-02-04T14:31:09.578145
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [3]
- `version`: 2.3.2

### Procedure 2: `kitchen_17_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_1 checks the contents of the refrigerator in the kitchen
- description: person_1, while in a kitchen with red cabinets and a white countertop, and holding a phone, looks ar...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='looks around', object='N/A', location='kitchen'}`
- Step 2: `{action='walks towards', object='refrigerator', location='kitchen'}`
- Step 3: `{action='contemplates action', object='N/A', location='kitchen'}`
- Step 4: `{action='opens', object='refrigerator', location='kitchen'}`
- Step 5: `{action='observes contents', object='refrigerator contents', location='refrigerator'}`

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
- 数量: 3
- Link 1: clip_id=`4`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`19`, relevance=`update`, similarity=`0.7347`
- Link 3: clip_id=`32`, relevance=`update`, similarity=`0.697`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:31:31.595209
- `updated_at`: 2026-02-04T14:38:37.998726
- `source`: incremental_nstf
- `observation_count`: 3
- `source_clips`: [4, 19, 32]
- `version`: 2.3.2

### Procedure 3: `kitchen_17_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 requests a 'look' from person_2, and person_2 expresses compliance.
- description: person_1, wearing a light beige hoodie and loose gray pants, is initially standing near the door loo...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='looks at phone', object='phone', location='near the door'}`
- Step 2: `{action='asks', object='N/A', location='near the door'}`
- Step 3: `{action='says', object='N/A', location='near the counter'}`

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
- Link 1: clip_id=`7`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:32:11.028205
- `updated_at`: 2026-02-04T14:32:11.028228
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [7]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (1 个)

- ⚠️ 所有 DAG 都是线性结构，无分支

### 总体评估

⚠️ **图谱基本完整，但有 1 个警告需要关注**