# NSTF 图谱分析报告

**视频:** `living_room_23`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:35  
**NSTF 路径:** `data/nstf_graphs/robot/living_room_23_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/living_room_23_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/living_room_23.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `living_room_23`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **13**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 13/13 | 100% |
| type | ✅ | 13/13 | 100% |
| goal | ✅ | 13/13 | 100% |
| description | ✅ | 13/13 | 100% |
| proc_type | ✅ | 13/13 | 100% |
| embeddings | ✅ | 13/13 | 100% |
| dag | ✅ | 13/13 | 100% |
| steps | ✅ | 13/13 | 100% |
| episodic_links | ✅ | 13/13 | 100% |
| metadata | ✅ | 13/13 | 100% |

### proc_type 分布

- `social`: 6
- `task`: 5
- `trait`: 2

### Steps 统计

- 总数: **41**
- 范围: 1 - 5
- 平均: 3.2
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 7 (avg: 5.2)
- edges 数量: 2 - 6 (avg: 4.2)

### Episodic Links 统计

- 数量范围: 1 - 2
- 平均: 1.2
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **13/13**
- Steps/DAG 一致: **13/13**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 1
- count 均值: 1.00
- 所有 count=1 的 Procedure: 13/13
⚠️ 所有 Procedure 的 count 都未更新！

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 13/13
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 12/13
- 有分支的 DAG: **1/13**
✅ 有 1 个 DAG 包含分支结构

**分支结构示例:**
- `living_room_23_proc_3`: START→2条边

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **64**
- NSTF 引用的 clips: **15**
- 覆盖率: **23.4%**
❌ 覆盖率过低 (<30%)！大量视频内容未被程序覆盖
- 未覆盖的 clips: `[0, 3, 4, 5, 6, 7, 8, 9, 10, 11]...` (共 49 个)

## 6. Goal 质量分析

- 总 Procedure 数: **13**
- 模糊 Goal 数: 3
- 具体 Goal 数: 2

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `living_room_23_proc_4`: person_1 seeks and receives affirmation of trust from person_2 regarding person_1's ability to overcome a difficult task.
- ⚠️ `living_room_23_proc_7`: person_1 expresses and processes curiosity about an object
- ⚠️ `living_room_23_proc_13`: Organizing items on the coffee table by moving a tray and a red cloth
⚠️ 只有 2/13 个 Goal 包含具体信息

### 所有 Goals

- person_1 and person_2 are sitting together in a living room.
- To plan a Halloween party and decide on a witch costume for person_1
- Initiate a joint work session between person_1 and person_2
- person_1 seeks and receives affirmation of trust from person_2 regarding person_1's ability to overcome a difficult task.
- Clean the window
- person_1 requests person_2 to hold their head
- person_1 expresses and processes curiosity about an object
- To provide a sheet of brown paper to person_7
- Collaborate on a craft project
- Person 1 to complete a craft project using crafting materials on the coffee table
- Illustrate person_1's playful and imaginative character
- Setting up a workspace for a craft project
- Organizing items on the coffee table by moving a tray and a red cloth

## 7. Character Mapping 分析

- 映射条目数: **23**
- face_* 映射: 2
- voice_* 映射: 21
- 映射到的 person 数: 9
- Person IDs: `['person_1', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6', 'person_7', 'person_8', 'person_9']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `living_room_23_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 and person_2 are sitting together in a living room.
- description: person_1 (wearing a white t-shirt and light-colored pants) and person_2 (wearing a purple t-shirt an...

**Steps 详情:**
- 数量: 2
- Step 1: `{action='takes a seat', object='brown couch', location='living room'}`
- Step 2: `{action='sits next to', object='N/A', location='brown couch'}`

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
- `created_at`: 2026-02-04T12:26:05.231590
- `updated_at`: 2026-02-04T12:26:05.231614
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [1]
- `version`: 2.3.2

### Procedure 2: `living_room_23_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: To plan a Halloween party and decide on a witch costume for person_1
- description: person_1 and person_1 discuss inviting friends for a Halloween party. One person_1 expresses uncerta...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='suggests inviting friends over for a Halloween party', object='friends, Halloween party', location='living room'}`
- Step 2: `{action='expresses uncertainty about a costume', object='costume', location='living room'}`
- Step 3: `{action='suggests person_1 dress up as a witch and offers to help make a wizard hat', object='witch costume, wizard hat', location='living room'}`
- Step 4: `{action='agrees, saying it's a good idea', object='witch costume idea', location='living room'}`

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
- 数量: 1
- Link 1: clip_id=`2`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:26:27.493877
- `updated_at`: 2026-02-04T12:26:27.493901
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [2]
- `version`: 2.3.2

### Procedure 3: `living_room_23_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: Initiate a joint work session between person_1 and person_2
- description: person_1 and person_2 position themselves in a living room and verbally initiate a collaborative wor...

**Steps 详情:**
- 数量: 4
- Step 1: `{action='sit on a red cushion', object='red cushion', location='in front of the coffee table'}`
- Step 2: `{action='sit on the sofa', object='light-colored sofa', location='living room'}`
- Step 3: `{action='announce the start of work', object='N/A', location='living room'}`
- Step 4: `{action='acknowledge and begin to elaborate', object='N/A', location='living room'}`

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
- Edge 1: `START → step_1 (prob=1.0)`
- Edge 2: `START → step_2 (prob=1.0)`
- Edge 3: `step_1 → step_3 (prob=1.0)`
- Edge 4: `step_2 → step_3 (prob=1.0)`
- Edge 5: `step_3 → step_4 (prob=1.0)`
- Edge 6: `step_4 → GOAL (prob=1.0)`

**Episodic Links 详情:**
- 数量: 1
- Link 1: clip_id=`16`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:27:27.935441
- `updated_at`: 2026-02-04T12:27:27.935465
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [16]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (1 个)

- ❌ Episodic 覆盖率过低: 23.4%

### 警告 (2 个)

- ⚠️ 所有边的转移计数未被更新
- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱存在 1 个问题，建议修复**