# NSTF 图谱分析报告

**视频:** `kitchen_16`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:33  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_16_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_16_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_16.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_16`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **30**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 30/30 | 100% |
| type | ✅ | 30/30 | 100% |
| goal | ✅ | 30/30 | 100% |
| description | ✅ | 30/30 | 100% |
| proc_type | ✅ | 30/30 | 100% |
| embeddings | ✅ | 30/30 | 100% |
| dag | ✅ | 30/30 | 100% |
| steps | ✅ | 30/30 | 100% |
| episodic_links | ✅ | 30/30 | 100% |
| metadata | ✅ | 30/30 | 100% |

### proc_type 分布

- `task`: 16
- `social`: 10
- `trait`: 3
- `habit`: 1

### Steps 统计

- 总数: **112**
- 范围: 1 - 9
- 平均: 3.7
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 11 (avg: 5.7)
- edges 数量: 2 - 10 (avg: 4.8)

### Episodic Links 统计

- 数量范围: 1 - 14
- 平均: 2.0
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **30/30**
- Steps/DAG 一致: **30/30**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 4
- count 均值: 1.04
- 所有 count=1 的 Procedure: 27/30
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 29/30

### DAG 分支结构统计

- 线性 DAG: 28/30
- 有分支的 DAG: **2/30**
✅ 有 2 个 DAG 包含分支结构

**分支结构示例:**
- `kitchen_16_proc_8`: step_2→2条边
- `kitchen_16_proc_14`: step_3→2条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **79**
- NSTF 引用的 clips: **59**
- 覆盖率: **74.7%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[3, 12, 13, 21, 26, 28, 30, 32, 38, 40, 42, 44, 50, 62, 68, 72, 73, 75, 77, 78]`

## 6. Goal 质量分析

- 总 Procedure 数: **30**
- 模糊 Goal 数: 2
- 具体 Goal 数: 11

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `kitchen_16_proc_15`: Reorganize and store a bag of sugar and other items in a kitchen drawer
- ⚠️ `kitchen_16_proc_30`: person_2 communicates with person_1 regarding an item

### 所有 Goals

- person_1 prepares for kitchen work, including requesting a hair scarf from person_2.
- Demonstrate person_1's thoughtful and neighborly trait.
- Maintain a tidy kitchen counter
- person_1 retrieves several packages from the refrigerator in the kitchen
- Prepare strawberries for a smoothie
- Wash and place a strawberry and a blueberry
- Discuss adding mangoes to berries while considering potential allergies
- Coordinate fruit preparation and manage flower arrangement
- Load a white bowl into the kitchen sink
- Retrieve and hand over the small orange and white bag of sugar to person_7
- person_1 verbally responds to an implied request from person_2
- Preparing food at the stove
- person_6 seeks permission from person_1 to use the microwave
- Adding measured sugar to three cracked eggs in a bowl
- Reorganize and store a bag of sugar and other items in a kitchen drawer
- person_2 and person_3 enter the kitchen area
- Person 1 to obtain information about the location of corn oil from Person 2
- person_1 washes their hands in the kitchen
- person_1 to initiate a request for assistance from person_9
- Person_1 prepares food
- person_1 successfully hands two egg cartons to person_2 in the kitchen
- Characterize person_1's personality during a casual cooking session.
- Demonstrating indecisiveness in food preference selection
- Cleaning the tabletop
- Clean a black frying pan in a kitchen sink
- person_1 informs person_3 about the oven's preheating status
- Partially bake bright orange batter in a toaster oven
- Share a prepared sandwich between person_1 and person_2
- person_1 and person_1 engage in breakfast conversation and plan their next activity.
- person_2 communicates with person_1 regarding an item

## 7. Character Mapping 分析

- 映射条目数: **46**
- face_* 映射: 2
- voice_* 映射: 44
- 映射到的 person 数: 15
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_12', 'person_13', 'person_14', 'person_15', 'person_2', 'person_3', 'person_4']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_16_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_1 prepares for kitchen work, including requesting a hair scarf from person_2.
- description: person_1 enters the kitchen, dons protective gear, requests a hair scarf from person_2, emphasizes k...

**Steps 详情:**
- 数量: 9
- Step 1: `{action='walks', object='N/A', location='kitchen'}`
- Step 2: `{action='puts on', object='yellow apron', location='N/A'}`
- Step 3: `{action='asks', object='hair scarf', location='N/A'}`
- Step 4: `{action='puts on', object='black gloves', location='N/A'}`
- Step 5: `{action='explains', object='N/A', location='kitchen'}`
- ... 还有 4 个步骤

**DAG 结构详情:**
- 节点数: 11, 边数: 10

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"
- `[step_3]`: type=`action`, label="N/A"
- `[step_4]`: type=`action`, label="N/A"
- `[step_5]`: type=`action`, label="N/A"
- `[step_6]`: type=`action`, label="N/A"
- ... 还有 3 个节点

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → step_3 (prob=1.0)`
- Edge 4: `step_3 → step_4 (prob=1.0)`
- Edge 5: `step_4 → step_5 (prob=1.0)`
- Edge 6: `step_5 → step_6 (prob=1.0)`
- ... 还有 4 条边

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`0`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:48:58.235372
- `updated_at`: 2026-02-04T13:48:58.235395
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [0]
- `version`: 2.3.2

### Procedure 2: `kitchen_16_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `trait`
- goal: Demonstrate person_1's thoughtful and neighborly trait.
- description: person_1 surveys the kitchen environment and then expresses a thoughtful intention to bake a fruit c...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='stands near the stove and looks around the kitchen', object='N/A', location='kitchen'}`
- Step 2: `{action='states that a new neighbor moved here', object='N/A', location='kitchen'}`
- Step 3: `{action='states intention to make a fruit cake for the new neighbor', object='N/A', location='kitchen'}`

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
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:49:19.046496
- `updated_at`: 2026-02-04T13:49:19.046520
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [1]
- `version`: 2.3.2

### Procedure 3: `kitchen_16_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `habit`
- goal: Maintain a tidy kitchen counter
- description: person_1 expresses the importance of keeping the kitchen counter tidy, initiates tidying, and later ...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='states importance of tidiness', object='kitchen counter', location='kitchen'}`
- Step 2: `{action='begins tidying', object='kitchen counter', location='kitchen'}`
- Step 3: `{action='asks question about effort of putting things back', object='trash bin', location='kitchen'}`

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
- Link 1: clip_id=`2`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:49:41.323355
- `updated_at`: 2026-02-04T13:49:41.323377
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