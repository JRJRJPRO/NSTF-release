# NSTF 图谱分析报告

**视频:** `kitchen_09`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:32  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_09_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_09_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_09.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_09`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **37**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 37/37 | 100% |
| type | ✅ | 37/37 | 100% |
| goal | ✅ | 37/37 | 100% |
| description | ✅ | 37/37 | 100% |
| proc_type | ✅ | 37/37 | 100% |
| embeddings | ✅ | 37/37 | 100% |
| dag | ✅ | 37/37 | 100% |
| steps | ✅ | 37/37 | 100% |
| episodic_links | ✅ | 37/37 | 100% |
| metadata | ✅ | 37/37 | 100% |

### proc_type 分布

- `task`: 24
- `social`: 12
- `habit`: 1

### Steps 统计

- 总数: **138**
- 范围: 1 - 7
- 平均: 3.7
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 5.7)
- edges 数量: 2 - 9 (avg: 4.8)

### Episodic Links 统计

- 数量范围: 1 - 10
- 平均: 1.7
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **37/37**
- Steps/DAG 一致: **37/37**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 5
- count 均值: 1.05
- 所有 count=1 的 Procedure: 33/37
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 37/37
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 35/37
- 有分支的 DAG: **2/37**
✅ 有 2 个 DAG 包含分支结构

**分支结构示例:**
- `kitchen_09_proc_17`: START→3条边
- `kitchen_09_proc_19`: step_2→2条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **72**
- NSTF 引用的 clips: **64**
- 覆盖率: **88.9%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[13, 17, 18, 23, 25, 31, 35, 39]`

## 6. Goal 质量分析

- 总 Procedure 数: **37**
- 模糊 Goal 数: 0
- 具体 Goal 数: 14

### 所有 Goals

- Get Jason and Rose to get up quickly
- Confirming person_2's habit of regularly washing dishes, as revealed by person_1's inquiry.
- Person_5 to obtain a glass of water with person_10's assistance
- person_3 (Rose) places a glass on the table
- Person_1 and person_2 exchange the white electric kettle
- Discussing a preference for coffee while person_2 prepares tea
- State the number of drinks found in the refrigerator
- person_3 checks the contents of the refrigerator
- person_1 finding food from the refrigerator for person_2
- Person 2 washes dishes
- Complete collaborative dishwashing in the kitchen
- Communicate the status of the trash can to others.
- Collaboratively prepare a meal
- Person_1 cooking at the stove
- Social interaction between person_3 and person_1
- Wash dishes in the black kitchen sink
- Preparing a meal in the modern kitchen
- Offer a banana to person_2
- person_2 to successfully make new eggs and dispose of the burnt eggs.
- Cleaning a black frying pan and a wooden spatula
- Cook two cracked eggs in a black non-stick frying pan
- person_1 receives food from person_17 and confirms permission to eat.
- Making an avocado and spread sandwich
- Serve a cut sandwich to person_2
- Person_3 serves breakfast to person_1 and opens the electric pressure cooker
- Pour a cup of milk for Rose
- Retrieve a clear glass from a drawer and move towards the dark gray refrigerator
- person_1 offers a clear plastic cup of milk to person_2
- person_2 advises person_1 and person_3 on healthy exercise and eating habits
- person_9 and person_10 communicate verbally during a meal
- person_2 opens and closes the drawer under the speckled white countertop
- person_2 and person_1 discuss meal options and ingredients
- person_2 delivers bread to person_1
- person_9 retrieves lettuce and cucumber from the refrigerator and places lettuce in a bowl
- person_2 requests person_1 to boil chicken breast
- person_2 and person_14 collaboratively assess the readiness of food.
- Coordinating meal-related activities among person_1, person_2, person_3, and person_4.

## 7. Character Mapping 分析

- 映射条目数: **28**
- face_* 映射: 2
- voice_* 映射: 26
- 映射到的 person 数: 19
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_12', 'person_13', 'person_14', 'person_15', 'person_16', 'person_17', 'person_18']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_09_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: Get Jason and Rose to get up quickly
- description: person_2 instructs Jason and Rose to get up quickly.

**Steps 详情:**
- 数量: 1
- Step 1: `{action='says', object='N/A', location='modern kitchen'}`

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
- Link 1: clip_id=`0`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:09:55.983323
- `updated_at`: 2026-02-04T14:09:55.983346
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [0]
- `version`: 2.3.2

### Procedure 2: `kitchen_09_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `habit`
- goal: Confirming person_2's habit of regularly washing dishes, as revealed by person_1's inquiry.
- description: The video clip shows person_2 actively washing dishes in the kitchen. This action is followed by per...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='washing dishes', object='dishes', location='sink'}`
- Step 2: `{action='enters', object='N/A', location='kitchen'}`
- Step 3: `{action='asks', object='N/A', location='kitchen'}`
- Step 4: `{action='confirms', object='N/A', location='kitchen'}`

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
- 数量: 2
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`14`, relevance=`update`, similarity=`0.54`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:10:10.871779
- `updated_at`: 2026-02-04T14:13:54.342623
- `source`: incremental_nstf
- `observation_count`: 2
- `source_clips`: [1, 14]
- `version`: 2.3.2

### Procedure 3: `kitchen_09_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Person_5 to obtain a glass of water with person_10's assistance
- description: Person_5 requests a glass cup from person_10, who acknowledges and brings it. Person_5 then fills th...

**Steps 详情:**
- 数量: 6
- Step 1: `{action='asks person_10 to bring her glass cup', object='glass cup', location='N/A'}`
- Step 2: `{action='replies 'Got it.' to person_5's request', object='N/A', location='N/A'}`
- Step 3: `{action='brings the glass cup to person_5', object='glass cup', location='modern kitchen'}`
- Step 4: `{action='uses a white electric kettle to fill a glass with water', object='glass, water, white electric kettle', location='modern kitchen'}`
- Step 5: `{action='thanks person_10', object='N/A', location='N/A'}`
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
- `created_at`: 2026-02-04T14:10:32.608959
- `updated_at`: 2026-02-04T14:10:32.608983
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [2]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (0 个)

✅ 无警告

### 总体评估

✅ **图谱结构完整，无明显问题**