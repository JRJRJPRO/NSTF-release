# NSTF 图谱分析报告

**视频:** `living_room_10`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:35  
**NSTF 路径:** `data/nstf_graphs/robot/living_room_10_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/living_room_10_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/living_room_10.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `living_room_10`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **28**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 28/28 | 100% |
| type | ✅ | 28/28 | 100% |
| goal | ✅ | 28/28 | 100% |
| description | ✅ | 28/28 | 100% |
| proc_type | ✅ | 28/28 | 100% |
| embeddings | ✅ | 28/28 | 100% |
| dag | ✅ | 28/28 | 100% |
| steps | ✅ | 28/28 | 100% |
| episodic_links | ✅ | 28/28 | 100% |
| metadata | ✅ | 28/28 | 100% |

### proc_type 分布

- `task`: 14
- `social`: 10
- `trait`: 3
- `habit`: 1

### Steps 统计

- 总数: **82**
- 范围: 1 - 9
- 平均: 2.9
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 11 (avg: 4.9)
- edges 数量: 2 - 10 (avg: 4.1)

### Episodic Links 统计

- 数量范围: 1 - 4
- 平均: 1.4
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **28/28**
- Steps/DAG 一致: **28/28**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 3
- count 均值: 1.09
- 所有 count=1 的 Procedure: 24/28
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 25/28

### DAG 分支结构统计

- 线性 DAG: 25/28
- 有分支的 DAG: **3/28**
✅ 有 3 个 DAG 包含分支结构

**分支结构示例:**
- `living_room_10_proc_3`: START→2条边
- `living_room_10_proc_14`: START→2条边
- `living_room_10_proc_24`: START→3条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **61**
- NSTF 引用的 clips: **39**
- 覆盖率: **63.9%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[0, 1, 2, 3, 7, 9, 18, 24, 26, 27]...` (共 22 个)

## 6. Goal 质量分析

- 总 Procedure 数: **28**
- 模糊 Goal 数: 3
- 具体 Goal 数: 4

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `living_room_10_proc_7`: Arrange items on the wooden cabinet near the window
- ⚠️ `living_room_10_proc_24`: person_3 consistently holds a phone while engaging with gift-related items
- ⚠️ `living_room_10_proc_25`: Unpack items from a cardboard box
⚠️ 只有 4/28 个 Goal 包含具体信息

### 所有 Goals

- Exhibit person_7's positive and appreciative personality
- Retrieve the small, light green and w from the TV stand
- person_6 cleaning the TV screen
- person_6 initiates a conversation with person_7 about the weather
- Observe the cityscape from the balcony
- Open the green Christmas box and use the smartphone at the table
- Arrange items on the wooden cabinet near the window
- Prepare Christmas decorations and clean the living room
- Decorate the Christmas tree
- person_1 places the white electric kettle on a side table near the entrance
- person_1 gives a black folder to person_2
- Decorate a small artificial Christmas tree with white snowflake decorations
- person_13 and person_1 agree to collaborate on choosing decorations
- Characterize person_3's leadership during the Christmas tree decorating process.
- Person_3 enters the living room from the balcony
- Place a white box containing yellow star
- person_11 expresses appreciation for the living room environment
- Facilitate festive communication and make a personal request
- person_1 observes person_2 and person_3 discussing near the TV console in a living room
- person_3 takes a selfie with person_1 and person_2
- person_3 receives and opens gifts with person_1 and person_2
- person_9 offers a green book to person_2
- person_3 expresses gratitude to person_1 and person_2 for meeting them
- person_3 consistently holds a phone while engaging with gift-related items
- Unpack items from a cardboard box
- Conduct a photo shoot of person_3, person_1, and person_2 using the Christmas tree and city view as backgrounds
- person_3 suggests taking photos with the Christmas tree
- Collaborate on a photoshoot involving person_2, person_3, and person_4

## 7. Character Mapping 分析

- 映射条目数: **45**
- face_* 映射: 3
- voice_* 映射: 42
- 映射到的 person 数: 20
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_12', 'person_13', 'person_14', 'person_15', 'person_16', 'person_17', 'person_18']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `living_room_10_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `trait`
- goal: Exhibit person_7's positive and appreciative personality
- description: person_7 consistently demonstrates a positive and appreciative personality through their verbal expr...

**Steps 详情:**
- 数量: 2
- Step 1: `{action='express appreciation', object='N/A', location='living room'}`
- Step 2: `{action='agree with appreciation', object='N/A', location='living room'}`

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
- Link 1: clip_id=`4`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:13:05.603103
- `updated_at`: 2026-02-04T12:13:05.603124
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [4]
- `version`: 2.3.2

### Procedure 2: `living_room_10_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Retrieve the small, light green and w from the TV stand
- description: Person_2 gets up from the floor, walks towards the TV stand, and picks up a small, light green and w...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='gets up', object='N/A', location='floor'}`
- Step 2: `{action='walks', object='N/A', location='TV stand'}`
- Step 3: `{action='picks up', object='small, light green and w', location='TV stand'}`

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
- Link 1: clip_id=`5`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:13:24.459291
- `updated_at`: 2026-02-04T12:13:24.459312
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [5]
- `version`: 2.3.2

### Procedure 3: `living_room_10_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_6 cleaning the TV screen
- description: person_6 is cleaning the TV screen with a white cloth in a brightly lit living room.

**Steps 详情:**
- 数量: 4
- Step 1: `{action='cleaning', object='windows', location='balcony'}`
- Step 2: `{action='decorating', object='small Christmas tree', location='near the TV'}`
- Step 3: `{action='adjusting', object='ornaments, small Christmas tree', location='near the TV'}`
- Step 4: `{action='placing', object='ornaments, small boxes', location='near the TV'}`

**DAG 结构详情:**
- 节点数: 6, 边数: 6

Nodes:
- `[START]`: type=`control`, label="N/A"
- `[GOAL]`: type=`control`, label="N/A"
- `[step_1]`: type=`action`, label="N/A"
- `[step_2]`: type=`action`, label="N/A"
- `[step_3]`: type=`action`, label="N/A"
- `[step_4]`: type=`action`, label="N/A"

Edges:
- Edge 1: `START → step_1 (prob=0.6666666666666666)`
- Edge 2: `START → step_2 (prob=0.3333333333333333)`
- Edge 3: `step_1 → GOAL (prob=1.0)`
- Edge 4: `step_2 → step_3 (prob=1.0)`
- Edge 5: `step_3 → step_4 (prob=1.0)`
- Edge 6: `step_4 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 3
- Link 1: clip_id=`6`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`22`, relevance=`update`, similarity=`0.6034`
- Link 3: clip_id=`25`, relevance=`update`, similarity=`0.5591`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:13:35.619217
- `updated_at`: 2026-02-04T12:18:49.650642
- `source`: incremental_nstf
- `observation_count`: 3
- `source_clips`: [6, 22, 25]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (1 个)

- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱基本完整，但有 1 个警告需要关注**