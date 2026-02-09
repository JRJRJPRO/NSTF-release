# NSTF 图谱分析报告

**视频:** `kitchen_11`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:33  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_11_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_11_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_11.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_11`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **27**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 27/27 | 100% |
| type | ✅ | 27/27 | 100% |
| goal | ✅ | 27/27 | 100% |
| description | ✅ | 27/27 | 100% |
| proc_type | ✅ | 27/27 | 100% |
| embeddings | ✅ | 27/27 | 100% |
| dag | ✅ | 27/27 | 100% |
| steps | ✅ | 27/27 | 100% |
| episodic_links | ✅ | 27/27 | 100% |
| metadata | ✅ | 27/27 | 100% |

### proc_type 分布

- `task`: 17
- `social`: 9
- `trait`: 1

### Steps 统计

- 总数: **115**
- 范围: 1 - 7
- 平均: 4.3
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 6.3)
- edges 数量: 2 - 8 (avg: 5.2)

### Episodic Links 统计

- 数量范围: 1 - 12
- 平均: 2.1
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **27/27**
- Steps/DAG 一致: **27/27**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 3
- count 均值: 1.09
- 所有 count=1 的 Procedure: 21/27

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 26/27

### DAG 分支结构统计

- 线性 DAG: 25/27
- 有分支的 DAG: **2/27**
✅ 有 2 个 DAG 包含分支结构

**分支结构示例:**
- `kitchen_11_proc_4`: START→2条边
- `kitchen_11_proc_19`: step_2→2条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **77**
- NSTF 引用的 clips: **56**
- 覆盖率: **72.7%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[3, 5, 7, 13, 15, 18, 19, 22, 23, 25]...` (共 21 个)

## 6. Goal 质量分析

- 总 Procedure 数: **27**
- 模糊 Goal 数: 3
- 具体 Goal 数: 8

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `kitchen_11_proc_18`: Retrieve a clear plastic bottle and access kitchen storage for a task
- ⚠️ `kitchen_11_proc_21`: Collect dirty items from the dining area and transport them to the kitchen
- ⚠️ `kitchen_11_proc_25`: Organize items on the dining table
⚠️ 只有 8/27 个 Goal 包含具体信息

### 所有 Goals

- person_1 cooks at the stove
- Cleaning the kitchen
- Prepare food by moving between the stove/countertop and sink
- Wash dishes at the sink
- Unpack groceries on the kitchen island
- Demonstrate person_1's organized and methodical nature
- Person_1 offers a cup to person_2 (Robo) and expresses gratitude
- person_1 and person_2 decide on their current meal and plan for a future meal
- person_1 advises person_2 on healthy eating habits during a meal
- person_1 and person_1 share a meal and converse about a super pet
- person_1 and person_2 negotiate a request from person_1
- Setting the dining table with a bowl of lettuce, a plate with sliced oranges, a plate of sliced tomatoes, and a glass of water for person_2
- Storing the vacuum cleaner on the wall mount in the kitchen
- Discussing and proposing leisure activities including getting a pet, hiking, and playing
- Collaboratively plan trip preparations between person_1 and person_2
- Emptying and beginning to sort contents from the refrigerator's bottom drawer onto the kitchen counter
- Retrieve a clear plastic bottle and access kitchen storage for a task
- Preparing a meal involving bread
- Spread dark red jam onto a slice of white bread
- Collect dirty items from the dining area and transport them to the kitchen
- person_3 tidies up the kitchen area
- person_1 prepares for a shot involving a wicker basket
- Set the black table with a white bowl
- Organize items on the dining table
- Discussing the implications of being home for an extended period, specifically regarding food
- Clean and store two textured glass glasses
- person_1 and person_4 cooperate to manage a forgotten sunshade

## 7. Character Mapping 分析

- 映射条目数: **39**
- face_* 映射: 3
- voice_* 映射: 36
- 映射到的 person 数: 4
- Person IDs: `['person_1', 'person_2', 'person_3', 'person_4']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_11_proc_4`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_1 cooks at the stove
- description: person_1, dressed in a gray outfit, is actively cooking at the stove in a modern kitchen setting. Si...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='cooking', object='N/A', location='kitchen'}`
- Step 2: `{action='moving', object='N/A', location='kitchen'}`
- Step 3: `{action='tending', object='stove', location='kitchen'}`
- Step 4: `{action='using', object='various utensils', location='kitchen'}`
- Step 5: `{action='cook', object='stove', location='near the stove'}`

**DAG 结构详情:**
- 节点数: 7, 边数: 4

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
- Edge 2: `step_1 → GOAL (prob=1.0)`
- Edge 3: `START → step_5 (prob=1.0)`
- Edge 4: `step_5 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 4
- Link 1: clip_id=`4`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`9`, relevance=`update`, similarity=`0.7106`
- Link 3: clip_id=`11`, relevance=`update`, similarity=`0.782`
- Link 4: clip_id=`20`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:43:45.836403
- `last_updated`: 2026-02-04T13:02:11.610480
- `source`: nstf_fusion
- `original_sources`: ['incremental_nstf', 'incremental_nstf']
- `fusion_count`: 1

**Fusion Info:**
- `source_procs`: ['kitchen_11_proc_4', 'kitchen_11_proc_6']
- `num_matched_steps`: 0
- `num_new_steps`: 1
- `total_steps`: 5
- `total_edges`: 4

### Procedure 2: `kitchen_11_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Cleaning the kitchen
- description: A person with long dark hair, wearing a dark gray or black jacket, cleans the kitchen by wiping the ...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='wiping', object='counter', location='near the sink'}`
- Step 2: `{action='moving', object='N/A', location='to the stove area'}`
- Step 3: `{action='adjusting', object='items', location='on the counter near the stove area'}`
- Step 4: `{action='adjusting', object='items', location='inside a cabinet near the stove area'}`

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
- Link 1: clip_id=`0`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`46`, relevance=`update`, similarity=`0.5307`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:42:51.365263
- `updated_at`: 2026-02-04T12:53:21.586539
- `source`: incremental_nstf
- `observation_count`: 2
- `source_clips`: [0, 46]
- `version`: 2.3.2

### Procedure 3: `kitchen_11_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Prepare food by moving between the stove/countertop and sink
- description: Person_1, identified as having long dark hair and wearing a gray dress, is engaged in food preparati...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='initiate food preparation', object='food', location='stove and countertop area'}`
- Step 2: `{action='move to sink', object='N/A', location='sink'}`
- Step 3: `{action='perform food preparation actions', object='food', location='sink'}`
- Step 4: `{action='move back to stove and countertop area', object='N/A', location='stove and countertop area'}`
- Step 5: `{action='continue food preparation', object='food', location='stove and countertop area'}`

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
- 数量: 12
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`6`, relevance=`update`, similarity=`0.6004`
- Link 3: clip_id=`8`, relevance=`update`, similarity=`0.6329`
- Link 4: clip_id=`10`, relevance=`update`, similarity=`0.6873`
- ... 还有 8 个链接

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:43:15.226451
- `updated_at`: 2026-02-04T13:01:03.018789
- `source`: incremental_nstf
- `observation_count`: 12
- `source_clips`: [1, 6, 8, 10, 12, 17, 21, 27, 28, 52, 60, 70]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (1 个)

- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱基本完整，但有 1 个警告需要关注**