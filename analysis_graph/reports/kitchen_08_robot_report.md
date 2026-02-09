# NSTF 图谱分析报告

**视频:** `kitchen_08`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:32  
**NSTF 路径:** `data/nstf_graphs/robot/kitchen_08_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/kitchen_08_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/kitchen_08.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `kitchen_08`
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

- `task`: 11
- `social`: 3
- `habit`: 1
- `trait`: 1

### Steps 统计

- 总数: **53**
- 范围: 1 - 6
- 平均: 3.3
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 8 (avg: 5.3)
- edges 数量: 2 - 7 (avg: 4.4)

### Episodic Links 统计

- 数量范围: 1 - 10
- 平均: 2.1
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **16/16**
- Steps/DAG 一致: **16/16**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 2
- count 均值: 1.04
- 所有 count=1 的 Procedure: 14/16
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 15/16

### DAG 分支结构统计

- 线性 DAG: 15/16
- 有分支的 DAG: **1/16**
✅ 有 1 个 DAG 包含分支结构

**分支结构示例:**
- `kitchen_08_proc_2`: START→2条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **76**
- NSTF 引用的 clips: **33**
- 覆盖率: **43.4%**
⚠️ 覆盖率较低 (<50%)
- 未覆盖的 clips: `[0, 1, 3, 4, 5, 6, 7, 8, 9, 12]...` (共 43 个)

## 6. Goal 质量分析

- 总 Procedure 数: **16**
- 模糊 Goal 数: 3
- 具体 Goal 数: 10

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `kitchen_08_proc_10`: person_2 assesses food items in the refrigerator and comments on food waste.
- ⚠️ `kitchen_08_proc_15`: Clean kitchenware and organize kitchen items
- ⚠️ `kitchen_08_proc_16`: Organizing items in a white kitchen cabinet

### 所有 Goals

- Retrieve vegetables from the refrigerator and move away
- person_2 to wash vegetables
- Prepare food in the kitchen
- person_1 and person_2 discuss morning drinks and breakfast options.
- Cooking at the stove
- Stir contents in a frying pan on the stove
- Cook a meal
- person_2 prepares a thermos drink/meal at the table
- person_2 directs X regarding refrigerator organization
- person_2 assesses food items in the refrigerator and comments on food waste.
- person_2 requests accompaniment and supervision for a future supermarket trip
- Store the vacuum-sealed meat package in the refrigerator and then walk to the kitchen sink
- person_1 transitions to a seated position at the table
- Demonstrate person_3's proactive trait
- Clean kitchenware and organize kitchen items
- Organizing items in a white kitchen cabinet

## 7. Character Mapping 分析

- 映射条目数: **18**
- face_* 映射: 0
- voice_* 映射: 18
- 映射到的 person 数: 10
- Person IDs: `['person_1', 'person_10', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6', 'person_7', 'person_8', 'person_9']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `kitchen_08_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Retrieve vegetables from the refrigerator and move away
- description: A person opens the refrigerator, takes out vegetables, closes the refrigerator, and then walks away ...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='opens', object='refrigerator', location='kitchen'}`
- Step 2: `{action='takes out', object='vegetables', location='refrigerator'}`
- Step 3: `{action='closes', object='refrigerator', location='kitchen'}`
- Step 4: `{action='walks toward', object='N/A', location='kitchen'}`

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
- 数量: 3
- Link 1: clip_id=`2`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`42`, relevance=`update`, similarity=`0.5362`
- Link 3: clip_id=`72`, relevance=`update`, similarity=`0.6061`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T15:12:56.516715
- `updated_at`: 2026-02-04T15:25:04.530952
- `source`: incremental_nstf
- `observation_count`: 3
- `source_clips`: [2, 42, 72]
- `version`: 2.3.2

### Procedure 2: `kitchen_08_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_2 to wash vegetables
- description: person_2 is performing the task of washing vegetables at the sink in a brightly lit kitchen and dini...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='moves', object='N/A', location='kitchen island'}`
- Step 2: `{action='places', object='yellow package', location='counter'}`
- Step 3: `{action='prepares food', object='food', location='sink'}`
- Step 4: `{action='speaks', object='N/A', location='N/A'}`

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
- Edge 2: `START → step_3 (prob=0.3333333333333333)`
- Edge 3: `step_1 → step_2 (prob=1.0)`
- Edge 4: `step_2 → step_4 (prob=1.0)`
- Edge 5: `step_3 → GOAL (prob=1.0)`
- Edge 6: `step_4 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 10
- Link 1: clip_id=`10`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`11`, relevance=`update`, similarity=`0.5607`
- Link 3: clip_id=`13`, relevance=`update`, similarity=`0.6375`
- Link 4: clip_id=`24`, relevance=`update`, similarity=`0.7056`
- ... 还有 6 个链接

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T15:13:30.512642
- `updated_at`: 2026-02-04T15:22:43.213970
- `source`: incremental_nstf
- `observation_count`: 10
- `source_clips`: [10, 11, 13, 24, 25, 29, 40, 54, 59, 62]
- `version`: 2.3.2

### Procedure 3: `kitchen_08_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Prepare food in the kitchen
- description: A person in a white shirt and dark pants is preparing food in a brightly lit kitchen.

**Steps 详情:**
- 数量: 5
- Step 1: `{action='opens package', object='yellow package of instant noodles', location='dining table'}`
- Step 2: `{action='places bowl', object='small white bowl', location='dining table'}`
- Step 3: `{action='places container', object='metal container', location='dining table'}`
- Step 4: `{action='picks up smartphone', object='smartphone', location='dining table'}`
- Step 5: `{action='looks at smartphone', object='smartphone', location='dining table'}`

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
- 数量: 6
- Link 1: clip_id=`20`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`31`, relevance=`update`, similarity=`0.567`
- Link 3: clip_id=`55`, relevance=`update`, similarity=`0.6049`
- Link 4: clip_id=`60`, relevance=`update`, similarity=`0.7045`
- ... 还有 2 个链接

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T15:14:37.152320
- `updated_at`: 2026-02-04T15:23:57.143559
- `source`: incremental_nstf
- `observation_count`: 6
- `source_clips`: [20, 31, 55, 60, 61, 65]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (1 个)

- ⚠️ Episodic 覆盖率较低: 43.4%

### 总体评估

⚠️ **图谱基本完整，但有 1 个警告需要关注**