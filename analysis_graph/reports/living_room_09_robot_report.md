# NSTF 图谱分析报告

**视频:** `living_room_09`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:34  
**NSTF 路径:** `data/nstf_graphs/robot/living_room_09_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/living_room_09_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/living_room_09.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `living_room_09`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **26**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 26/26 | 100% |
| type | ✅ | 26/26 | 100% |
| goal | ✅ | 26/26 | 100% |
| description | ✅ | 26/26 | 100% |
| proc_type | ✅ | 26/26 | 100% |
| embeddings | ✅ | 26/26 | 100% |
| dag | ✅ | 26/26 | 100% |
| steps | ✅ | 26/26 | 100% |
| episodic_links | ✅ | 26/26 | 100% |
| metadata | ✅ | 26/26 | 100% |

### proc_type 分布

- `social`: 11
- `task`: 10
- `trait`: 5

### Steps 统计

- 总数: **71**
- 范围: 1 - 7
- 平均: 2.7
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 4.7)
- edges 数量: 2 - 8 (avg: 3.8)

### Episodic Links 统计

- 数量范围: 1 - 3
- 平均: 1.2
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **26/26**
- Steps/DAG 一致: **26/26**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 2
- count 均值: 1.01
- 所有 count=1 的 Procedure: 25/26
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 24/26

### DAG 分支结构统计

- 线性 DAG: 24/26
- 有分支的 DAG: **2/26**
✅ 有 2 个 DAG 包含分支结构

**分支结构示例:**
- `living_room_09_proc_19`: START→3条边
- `living_room_09_proc_23`: step_1→2条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **72**
- NSTF 引用的 clips: **31**
- 覆盖率: **43.1%**
⚠️ 覆盖率较低 (<50%)
- 未覆盖的 clips: `[0, 2, 4, 5, 6, 7, 12, 14, 15, 17]...` (共 41 个)

## 6. Goal 质量分析

- 总 Procedure 数: **26**
- 模糊 Goal 数: 3
- 具体 Goal 数: 9

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `living_room_09_proc_11`: person_2 adjusts items on the glass coffee table
- ⚠️ `living_room_09_proc_21`: person_2 is attentive to both immediate tasks and external events
- ⚠️ `living_room_09_proc_25`: person_2 demonstrates deliberation in object placement

### 所有 Goals

- Robot fetches milk and bread from the refrigerator
- person_2 gets a snack from the glass coffee table to address hunger
- Placing the plastic bag of groceries on the coffee table
- Tidy up the clothes on the desk
- Open, observe from, and close the black-framed window on the balcony
- person_2 responds to Sam's arrival
- person_2 asks person_2 about recent nervousness, leading to person_2 expressing health concerns and beginning to explain further.
- person_2 and person_2 to plan an outing to try authentic sushi and see cherry blossoms
- person_2 utters the phrase 'and um, on wat' in the living room
- Get a bottle of orange juice from the stainless steel refrigerator
- person_2 adjusts items on the glass coffee table
- Deciding on takeout lunch options
- person_2 to receive lunch recommendations from the robot
- Share attention on a phone between person_1 and person_2
- person_2 proposes moving food from the coffee table to the dining table
- Someone takes purple clothes from the desk in the living room and cleans the table.
- Understand the planning preference of one of the individuals referred to as person_2
- person_2 suggests a picnic in the mountains to another individual
- Infer the disorganized trait of the living room's resident(s)
- person_2 and the other individual interact regarding shoe placement and departure.
- person_2 is attentive to both immediate tasks and external events
- Characterize person_1's living environment as untidy
- person_2 finds the blind box
- person_2 arrives at person_1's apartment and initiates a gift exchange
- person_2 demonstrates deliberation in object placement
- Move a piece of paper from the coffee table in the living room to the bedroom

## 7. Character Mapping 分析

- 映射条目数: **22**
- face_* 映射: 2
- voice_* 映射: 20
- 映射到的 person 数: 5
- Person IDs: `['person_1', 'person_2', 'person_3', 'person_4', 'person_5']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `living_room_09_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Robot fetches milk and bread from the refrigerator
- description: person_2 instructs a robot to retrieve milk and bread from the refrigerator.

**Steps 详情:**
- 数量: 2
- Step 1: `{action='asks', object='milk, bread', location='refrigerator'}`
- Step 2: `{action='fetches', object='milk, bread', location='refrigerator'}`

**DAG 结构详情:**
- 节点数: 4, 边数: 3

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:00:19.988000
- `updated_at`: 2026-02-04T12:00:19.988024
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [1]
- `version`: 2.3.2

### Procedure 2: `living_room_09_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_2 gets a snack from the glass coffee table to address hunger
- description: person_2 expresses feeling hungry and then picks up a snack from the glass coffee table.

**Steps 详情:**
- 数量: 2
- Step 1: `{action='expresses being a little bit hungry', object='N/A', location='living room'}`
- Step 2: `{action='picks up', object='snack', location='glass coffee table'}`

**DAG 结构详情:**
- 节点数: 4, 边数: 3

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `step_1 → step_2 (prob=1.0)`
- Edge 3: `step_2 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`3`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:00:38.236183
- `updated_at`: 2026-02-04T12:00:38.236206
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [3]
- `version`: 2.3.2

### Procedure 3: `living_room_09_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Placing the plastic bag of groceries on the coffee table
- description: person_1 retrieves a plastic bag of groceries from the refrigerator, closes the refrigerator door, w...

**Steps 详情:**
- 数量: 7
- Step 1: `{action='expresses intent', object='book, phone', location='balcony'}`
- Step 2: `{action='moves', object='N/A', location='balcony to interior of the apartment'}`
- Step 3: `{action='modifies plan', object='N/A', location='interior of the apartment'}`
- Step 4: `{action='walks', object='N/A', location='living room'}`
- Step 5: `{action='places items', object='book, phone', location='coffee table'}`
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
- Link 1: clip_id=`8`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`9`, relevance=`update`, similarity=`0.5023`
- Link 3: clip_id=`64`, relevance=`update`, similarity=`0.4747`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:01:05.262122
- `updated_at`: 2026-02-04T12:10:52.794065
- `source`: incremental_nstf
- `observation_count`: 3
- `source_clips`: [8, 9, 64]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (1 个)

- ⚠️ Episodic 覆盖率较低: 43.1%

### 总体评估

⚠️ **图谱基本完整，但有 1 个警告需要关注**