# NSTF 图谱分析报告

**视频:** `kitchen_22`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:34  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_22_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_22_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_22.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_22`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **22**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 22/22 | 100% |
| type | ✅ | 22/22 | 100% |
| goal | ✅ | 22/22 | 100% |
| description | ✅ | 22/22 | 100% |
| proc_type | ✅ | 22/22 | 100% |
| embeddings | ✅ | 22/22 | 100% |
| dag | ✅ | 22/22 | 100% |
| steps | ✅ | 22/22 | 100% |
| episodic_links | ✅ | 22/22 | 100% |
| metadata | ✅ | 22/22 | 100% |

### proc_type 分布

- `task`: 19
- `social`: 3

### Steps 统计

- 总数: **77**
- 范围: 1 - 6
- 平均: 3.5
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 8 (avg: 5.5)
- edges 数量: 2 - 7 (avg: 4.5)

### Episodic Links 统计

- 数量范围: 1 - 6
- 平均: 1.5
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **22/22**
- Steps/DAG 一致: **22/22**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 4
- count 均值: 1.06
- 所有 count=1 的 Procedure: 20/22
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 22/22
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 22/22
- 有分支的 DAG: **0/22**
⚠️ 没有任何 DAG 有分支结构！

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **40**
- NSTF 引用的 clips: **33**
- 覆盖率: **82.5%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[0, 15, 16, 17, 31, 32, 39]`

## 6. Goal 质量分析

- 总 Procedure 数: **22**
- 模糊 Goal 数: 2
- 具体 Goal 数: 11

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `kitchen_22_proc_10`: Cook something in a black frying pan on the stove
- ⚠️ `kitchen_22_proc_17`: Clear items from the kitchen counter

### 所有 Goals

- Preparing a meal (brai)
- person_2 and person_7 interact regarding food preparation and assistance
- Change radish to winter melon by instructing robots
- person_2 cleans specific areas in the kitchen
- person_6 successfully communicates a request to person_2 to save food for him
- Interacting with a drawer and a tote bag on the kitchen island
- Prepare ingredients for a meal
- Chopping red meat on a white cutting board
- Slicing red chili peppers
- Cook something in a black frying pan on the stove
- Moving food around in a yellow frying pan
- Perform initial cooking steps in a yellow wok by adding ingredients, stirring, seasoning, and adding water
- Place the green cutting board on the main countertop
- Peel and segment an orange
- Complete the juicing process using a juicer
- Pour light orange liquid into a small, clear glass
- Clear items from the kitchen counter
- Transfer cooked meat from black MABAL wok to white bowl
- Serve a meal to person_1
- Serving orange juice and food on the dining table
- person_2 rinses a knife and cutting board
- Participating in a shared moment at the dining table

## 7. Character Mapping 分析

- 映射条目数: **11**
- face_* 映射: 0
- voice_* 映射: 11
- 映射到的 person 数: 7
- Person IDs: `['person_1', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6', 'person_7']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_22_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Preparing a meal (brai)
- description: A sequence of actions involving retrieving an item from a refrigerator, unpacking groceries, and a c...

**Steps 详情:**
- 数量: 6
- Step 1: `{action='Reaching into refrigerator', object='N/A', location='Refrigerator'}`
- Step 2: `{action='Closing refrigerator door', object='Refrigerator door', location='Refrigerator'}`
- Step 3: `{action='Unpacking groceries', object='Groceries, beige bag with red handles', location='Modern kitchen'}`
- Step 4: `{action='Entering kitchen', object='N/A', location='Modern kitchen'}`
- Step 5: `{action='Asking about cooking', object='N/A', location='Modern kitchen'}`
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
- 数量: 3
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`9`, relevance=`update`, similarity=`0.536`
- Link 3: clip_id=`10`, relevance=`update`, similarity=`0.5518`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T11:37:32.130100
- `updated_at`: 2026-02-04T11:40:15.618754
- `source`: incremental_nstf
- `observation_count`: 3
- `source_clips`: [1, 9, 10]
- `version`: 2.3.2

### Procedure 2: `kitchen_22_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_2 and person_7 interact regarding food preparation and assistance
- description: person_2, while preparing food, asks person_7 for spices. person_7 offers assistance, to which perso...

**Steps 详情:**
- 数量: 6
- Step 1: `{action='asks for item', object='spices', location='N/A'}`
- Step 2: `{action='offers assistance', object='N/A', location='N/A'}`
- Step 3: `{action='gives ultimatum', object='N/A', location='N/A'}`
- Step 4: `{action='places item', object='shopping bag', location='counter'}`
- Step 5: `{action='opens object', object='cabinet', location='above the stove'}`
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
- `created_at`: 2026-02-04T11:38:05.162675
- `updated_at`: 2026-02-04T11:38:05.162704
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [2]
- `version`: 2.3.2

### Procedure 3: `kitchen_22_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Change radish to winter melon by instructing robots
- description: person_2 initiates a request to person_2 to change an ingredient from radish to winter melon. In res...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='asks', object='['radish', 'winter melon']', location='kitchen'}`
- Step 2: `{action='agrees, tells', object='N/A', location='kitchen'}`
- Step 3: `{action='instructs', object='winter melon', location='kitchen'}`

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
- `created_at`: 2026-02-04T11:38:35.071750
- `updated_at`: 2026-02-04T11:38:35.071773
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [3]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (1 个)

- ⚠️ 所有 DAG 都是线性结构，无分支

### 总体评估

⚠️ **图谱基本完整，但有 1 个警告需要关注**