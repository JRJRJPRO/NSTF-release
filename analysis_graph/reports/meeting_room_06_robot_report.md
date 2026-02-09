# NSTF 图谱分析报告

**视频:** `meeting_room_06`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:36  
**NSTF 路径:** `data/nstf_graphs/robot/meeting_room_06_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/meeting_room_06_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/meeting_room_06.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `meeting_room_06`
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

- `social`: 13
- `task`: 6
- `trait`: 2

### Steps 统计

- 总数: **54**
- 范围: 1 - 7
- 平均: 2.6
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 4.6)
- edges 数量: 2 - 8 (avg: 3.7)

### Episodic Links 统计

- 数量范围: 1 - 8
- 平均: 1.7
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **21/21**
- Steps/DAG 一致: **21/21**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 6
- count 均值: 1.14
- 所有 count=1 的 Procedure: 19/21
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 20/21

### DAG 分支结构统计

- 线性 DAG: 20/21
- 有分支的 DAG: **1/21**
✅ 有 1 个 DAG 包含分支结构

**分支结构示例:**
- `meeting_room_06_proc_7`: START→3条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **65**
- NSTF 引用的 clips: **36**
- 覆盖率: **55.4%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[2, 6, 7, 11, 12, 14, 16, 17, 18, 19]...` (共 29 个)

## 6. Goal 质量分析

- 总 Procedure 数: **21**
- 模糊 Goal 数: 0
- 具体 Goal 数: 4
⚠️ 只有 4/21 个 Goal 包含具体信息

### 所有 Goals

- person_3 settling into a table in the conference room
- person_3 requests sugar cubes
- Obtain a nearly full paper cup of water and place it on the wooden table
- Preparing tea at a wooden table
- Prepare a cup of instant coffee
- person_1 hands a document to person_2, and person_2 acknowledges the receipt.
- person_3 initiates a discussion about the plan
- person_1 proposes categorizing clients by age group to person_2
- person_3 communicates that middle-aged groups are more concerned about product
- person_3 addresses the room
- Establish promotion channels
- Decide the target group according to age and consumption habits
- Characterize person_4 as enthusiastic and supportive of creative ideas
- Two individuals discuss Customer Segmentation in a conference room.
- person_3 addresses person_4
- person_1 hands a smartphone to person_2 and secures a pen in the black backpack.
- person_5 gives the coiled white charging cable and white power adapter to person_6
- person_3 and person_3 engage in conversation
- Engage in a discussion between person_1 and person_2
- person_3 expresses financial caution regarding budget allocation
- Facilitate discussion and review of meeting notes, including target group division, between person_1 and person_2

## 7. Character Mapping 分析

- 映射条目数: **17**
- face_* 映射: 0
- voice_* 映射: 17
- 映射到的 person 数: 11
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6', 'person_7', 'person_8']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `meeting_room_06_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_3 settling into a table in the conference room
- description: person_3 enters the conference room, sits at a table, and places their black bag on the floor.

**Steps 详情:**
- 数量: 3
- Step 1: `{action='walks into the frame', object='N/A', location='conference room (from the right)'}`
- Step 2: `{action='sits down', object='N/A', location='one of the tables'}`
- Step 3: `{action='puts', object='black bag', location='floor next to the table'}`

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
- Link 1: clip_id=`0`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T15:00:16.852709
- `updated_at`: 2026-02-04T15:00:16.852731
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [0]
- `version`: 2.3.2

### Procedure 2: `meeting_room_06_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_3 requests sugar cubes
- description: person_3 verbally communicates a desire for sugar cubes to another individual in the room.

**Steps 详情:**
- 数量: 1
- Step 1: `{action='asks for', object='sugar cubes', location='room'}`

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
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T15:00:27.086881
- `updated_at`: 2026-02-04T15:00:27.086904
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [1]
- `version`: 2.3.2

### Procedure 3: `meeting_room_06_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Obtain a nearly full paper cup of water and place it on the wooden table
- description: A person wearing black gloves pours water from a large blue water jug, which sits on a black water d...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='Pours water', object='water, large blue water jug, paper cup', location='black water dispenser base'}`
- Step 2: `{action='Fills the paper cup', object='paper cup, water', location='black water dispenser base'}`
- Step 3: `{action='Places the filled cup', object='filled paper cup', location='wooden table'}`

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
- `created_at`: 2026-02-04T15:00:42.591202
- `updated_at`: 2026-02-04T15:00:42.591223
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [3]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (1 个)

- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱基本完整，但有 1 个警告需要关注**