# NSTF 图谱分析报告

**视频:** `living_room_12`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:35  
**NSTF 路径:** `data/nstf_graphs/robot/living_room_12_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/living_room_12_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/living_room_12.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `living_room_12`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **14**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 14/14 | 100% |
| type | ✅ | 14/14 | 100% |
| goal | ✅ | 14/14 | 100% |
| description | ✅ | 14/14 | 100% |
| proc_type | ✅ | 14/14 | 100% |
| embeddings | ✅ | 14/14 | 100% |
| dag | ✅ | 14/14 | 100% |
| steps | ✅ | 14/14 | 100% |
| episodic_links | ✅ | 14/14 | 100% |
| metadata | ✅ | 14/14 | 100% |

### proc_type 分布

- `task`: 10
- `trait`: 2
- `social`: 2

### Steps 统计

- 总数: **48**
- 范围: 1 - 7
- 平均: 3.4
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 5.4)
- edges 数量: 2 - 8 (avg: 4.4)

### Episodic Links 统计

- 数量范围: 1 - 5
- 平均: 1.6
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **14/14**
- Steps/DAG 一致: **14/14**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 2
- count 均值: 1.05
- 所有 count=1 的 Procedure: 12/14
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 14/14
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 14/14
- 有分支的 DAG: **0/14**
⚠️ 没有任何 DAG 有分支结构！

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **72**
- NSTF 引用的 clips: **23**
- 覆盖率: **31.9%**
⚠️ 覆盖率较低 (<50%)
- 未覆盖的 clips: `[2, 3, 4, 5, 6, 7, 9, 10, 11, 12]...` (共 49 个)

## 6. Goal 质量分析

- 总 Procedure 数: **14**
- 模糊 Goal 数: 0
- 具体 Goal 数: 4
⚠️ 只有 4/14 个 Goal 包含具体信息

### 所有 Goals

- To maintain an orderly and clean living environment
- Establish person_1's trait as a cleaning expert in the modern living room.
- person_1 organizes books on the white marble coffee table
- person_2 selects the 'Givenchy' and 'Chanel' books and places them in a designated area.
- Prepare to clean the balcony railing while preventing scratches
- person_1 hands papers to person_2
- To initiate problem-solving for an unspecified issue by identifying a potential resource.
- Organizing the green spray bottle and accessing the drawer under the white countertop
- Tidy the living room by arranging pillows on the light beige sofa
- Retrieve a small, white device with a digital display from a compartment beneath the television
- Transporting a black slipper from the glass-topped table to the living room
- Inform Chloe about the arrival of her decorative painting
- person_2 presents a framed piece of calligraphy to person_1
- Covering the beige couch with a gray and white sheet

## 7. Character Mapping 分析

- 映射条目数: **29**
- face_* 映射: 2
- voice_* 映射: 27
- 映射到的 person 数: 9
- Person IDs: `['person_1', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6', 'person_7', 'person_8', 'person_9']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `living_room_12_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `trait`
- goal: To maintain an orderly and clean living environment
- description: person_2 demonstrates a strong preference for order and cleanliness, reacting negatively to a clutte...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='enters', object='N/A', location='living room'}`
- Step 2: `{action='observes', object='living room', location='living room'}`
- Step 3: `{action='expresses dissatisfaction', object='N/A', location='living room'}`

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
- 数量: 2
- Link 1: clip_id=`0`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`41`, relevance=`update`, similarity=`0.6032`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:39:04.624093
- `updated_at`: 2026-02-04T13:44:00.731489
- `source`: incremental_nstf
- `observation_count`: 2
- `source_clips`: [0, 41]
- `version`: 2.3.2

### Procedure 2: `living_room_12_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `trait`
- goal: Establish person_1's trait as a cleaning expert in the modern living room.
- description: person_1 explicitly states their expertise in cleaning, which person_2 acknowledges and welcomes, le...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='arranges magazines', object='magazines', location='metal rack'}`
- Step 2: `{action='asks person_2 to move away', object='N/A', location='room'}`
- Step 3: `{action='replies 'Okay'', object='N/A', location='room'}`
- Step 4: `{action='continues organizing magazines', object='magazines', location='metal rack'}`
- Step 5: `{action='expresses relief and mentions being tired from organizing', object='N/A', location='room'}`

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
- 数量: 5
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`15`, relevance=`update`, similarity=`0.6077`
- Link 3: clip_id=`42`, relevance=`update`, similarity=`0.6586`
- Link 4: clip_id=`44`, relevance=`update`, similarity=`0.7111`
- ... 还有 1 个链接

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:39:30.373411
- `updated_at`: 2026-02-04T13:47:47.802483
- `source`: incremental_nstf
- `observation_count`: 5
- `source_clips`: [1, 15, 42, 44, 60]
- `version`: 2.3.2

### Procedure 3: `living_room_12_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_1 organizes books on the white marble coffee table
- description: person_1, a woman with long dark hair, wearing a black t-shirt and blue jeans, is observed organizin...

**Steps 详情:**
- 数量: 2
- Step 1: `{action='picks up', object='a book', location='white marble coffee table'}`
- Step 2: `{action='flips through', object='a book's pages', location='N/A'}`

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
- Link 1: clip_id=`8`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T13:40:13.345124
- `updated_at`: 2026-02-04T13:40:13.345146
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [8]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (3 个)

- ⚠️ 所有 DAG 都是线性结构，无分支
- ⚠️ Episodic 覆盖率较低: 31.9%
- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱基本完整，但有 3 个警告需要关注**