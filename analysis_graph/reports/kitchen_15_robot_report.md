# NSTF 图谱分析报告

**视频:** `kitchen_15`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:33  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_15_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_15_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_15.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_15`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **16**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 16/16 | 100% |
| type | ✅ | 16/16 | 100% |
| goal | ✅ | 16/16 | 100% |
| description | ✅ | 16/16 | 100% |
| proc_type | ✅ | 16/16 | 100% |
| embeddings | ✅ | 16/16 | 100% |
| dag | ✅ | 16/16 | 100% |
| steps | ✅ | 16/16 | 100% |
| episodic_links | ✅ | 16/16 | 100% |
| metadata | ✅ | 16/16 | 100% |

### proc_type 分布

- `social`: 8
- `task`: 7
- `trait`: 1

### Steps 统计

- 总数: **42**
- 范围: 1 - 5
- 平均: 2.6
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 7 (avg: 4.6)
- edges 数量: 2 - 6 (avg: 3.6)

### Episodic Links 统计

- 数量范围: 1 - 12
- 平均: 2.6
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **16/16**
- Steps/DAG 一致: **16/16**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 2
- count 均值: 1.07
- 所有 count=1 的 Procedure: 14/16
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 16/16
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 16/16
- 有分支的 DAG: **0/16**
⚠️ 没有任何 DAG 有分支结构！

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **62**
- NSTF 引用的 clips: **41**
- 覆盖率: **66.1%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[1, 3, 5, 7, 9, 21, 26, 30, 32, 34]...` (共 21 个)

## 6. Goal 质量分析

- 总 Procedure 数: **16**
- 模糊 Goal 数: 1
- 具体 Goal 数: 4

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `kitchen_15_proc_3`: Prepare to handle items in the kitchen
⚠️ 只有 4/16 个 Goal 包含具体信息

### 所有 Goals

- person_3 and person_4 settle into the room and begin a conversation
- person_1 and person_2 discuss plans to make a turkey
- Prepare to handle items in the kitchen
- person_3 dries a towel and hangs it on a hook above the sink
- person_6 preparing food on a black plate
- person_3 requests butter from person_4, and person_4 acknowledges the request.
- person_1 advises an unnamed person to reduce carving
- Slicing an onion
- Clean the white countertop in the kitchen
- Characterize person_2's meticulous and health-conscious personality.
- Put the butter into the microwave
- person_10 and person_3 engage in a conversation where person_10 instructs person_3 to take out the bowl.
- Establish agreement for a joint activity between person_6 and person_7
- person_11 obtains scissors from person_5 for food preparation
- person_2 requests a small bowl from person_1
- person_12 prepares a whole chicken

## 7. Character Mapping 分析

- 映射条目数: **41**
- face_* 映射: 2
- voice_* 映射: 39
- 映射到的 person 数: 16
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_12', 'person_13', 'person_14', 'person_15', 'person_16', 'person_2', 'person_3']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_15_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_3 and person_4 settle into the room and begin a conversation
- description: person_3 and person_4 enter a room, person_3 (wearing a white dress) briefly approaches the kitchen ...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='walk into', object='N/A', location='room'}`
- Step 2: `{action='walks towards', object='kitchen counter', location='kitchen area'}`
- Step 3: `{action='sits down', object='N/A', location='small round table'}`
- Step 4: `{action='sits down', object='N/A', location='small round table'}`
- Step 5: `{action='asks', object='N/A', location='small round table'}`

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
- Link 1: clip_id=`0`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T11:46:40.495900
- `updated_at`: 2026-02-04T11:46:40.495924
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [0]
- `version`: 2.3.2

### Procedure 2: `kitchen_15_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 and person_2 discuss plans to make a turkey
- description: person_1, wearing a light gray t-shirt, and person_2, wearing a white blouse, are sitting at a small...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='washes dishes', object='dishes', location='sink'}`
- Step 2: `{action='states 'I wash my hand.'', object='N/A', location='kitchen'}`
- Step 3: `{action='replies 'Yes.'', object='N/A', location='kitchen'}`
- Step 4: `{action='states 'It's very difficult for us, so we need to watch the teaching videos.'', object='N/A', location='kitchen'}`

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
- Link 1: clip_id=`2`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`24`, relevance=`update`, similarity=`0.5597`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T11:47:02.546373
- `updated_at`: 2026-02-04T11:53:06.132948
- `source`: incremental_nstf
- `observation_count`: 2
- `source_clips`: [2, 24]
- `version`: 2.3.2

### Procedure 3: `kitchen_15_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Prepare to handle items in the kitchen
- description: person_6 and person_5 are in a kitchen with white countertops and light green cabinets. They put on ...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='asks about ingredient quantity', object='brown bottle', location='counter'}`
- Step 2: `{action='confirms ingredient quantity', object='brown bottle', location='N/A'}`
- Step 3: `{action='expresses excitement', object='N/A', location='N/A'}`
- Step 4: `{action='offers to make the hot dish', object='hot dish', location='kitchen'}`

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
- 数量: 12
- Link 1: clip_id=`4`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`8`, relevance=`update`, similarity=`0.5601`
- Link 3: clip_id=`11`, relevance=`update`, similarity=`0.6129`
- Link 4: clip_id=`12`, relevance=`update`, similarity=`0.6284`
- ... 还有 8 个链接

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T11:47:58.914720
- `updated_at`: 2026-02-04T11:59:23.577827
- `source`: incremental_nstf
- `observation_count`: 12
- `source_clips`: [4, 8, 11, 12, 13, 19, 27, 35, 48, 52, 54, 57]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (2 个)

- ⚠️ 所有 DAG 都是线性结构，无分支
- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱基本完整，但有 2 个警告需要关注**