# NSTF 图谱分析报告

**视频:** `study_05`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:36  
**NSTF 路径:** `data/nstf_graphs/robot/study_05_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/study_05_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/study_05.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `study_05`
- 数据集: `robot`
- 版本: `2.3.2`
- Procedure 数量: **15**

## 3. Procedure 节点分析


### 字段填充率

| 字段 | 状态 | 填充数 | 比例 |
|------|------|--------|------|
| proc_id | ✅ | 15/15 | 100% |
| type | ✅ | 15/15 | 100% |
| goal | ✅ | 15/15 | 100% |
| description | ✅ | 15/15 | 100% |
| proc_type | ✅ | 15/15 | 100% |
| embeddings | ✅ | 15/15 | 100% |
| dag | ✅ | 15/15 | 100% |
| steps | ✅ | 15/15 | 100% |
| episodic_links | ✅ | 15/15 | 100% |
| metadata | ✅ | 15/15 | 100% |

### proc_type 分布

- `social`: 8
- `task`: 7

### Steps 统计

- 总数: **45**
- 范围: 1 - 7
- 平均: 3.0
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 5.0)
- edges 数量: 2 - 8 (avg: 4.0)

### Episodic Links 统计

- 数量范围: 1 - 1
- 平均: 1.0
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **15/15**
- Steps/DAG 一致: **15/15**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 1
- count 均值: 1.00
- 所有 count=1 的 Procedure: 15/15
⚠️ 所有 Procedure 的 count 都未更新！

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 15/15
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 15/15
- 有分支的 DAG: **0/15**
⚠️ 没有任何 DAG 有分支结构！

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **69**
- NSTF 引用的 clips: **15**
- 覆盖率: **21.7%**
❌ 覆盖率过低 (<30%)！大量视频内容未被程序覆盖
- 未覆盖的 clips: `[1, 2, 3, 5, 6, 7, 8, 9, 10, 11]...` (共 54 个)

## 6. Goal 质量分析

- 总 Procedure 数: **15**
- 模糊 Goal 数: 3
- 具体 Goal 数: 1

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `study_05_proc_3`: person_1 fixes something
- ⚠️ `study_05_proc_4`: person_2 successfully performs the third iteration of a hands-on task safely under person_1's guidance.
- ⚠️ `study_05_proc_15`: Interacting with items on a cluttered wooden desk
⚠️ 只有 1/15 个 Goal 包含具体信息

### 所有 Goals

- person_1 discusses homework with person_2 and understands person_2's approach
- person_1 suggests finishing craft work before dinner
- person_1 fixes something
- person_2 successfully performs the third iteration of a hands-on task safely under person_1's guidance.
- Complete a craft project
- Retrieve colorful paper from the bedside table and bring it towards the desk for the project.
- Person_1 observes person_2
- person_1 requests paint from person_2
- person_1 expresses gratitude and affection to person_2 (mom) by giving a green card.
- To decide on the use of paper shapes
- Crafting a clay apple tree
- Demonstrate the warm and supportive parent-child dynamic between person_1 and person_2 during a craft project.
- person_1 seeks confirmation from person_2 regarding a clay craft
- person_1 expresses gratitude and affection to person_2 for a handmade craft project
- Interacting with items on a cluttered wooden desk

## 7. Character Mapping 分析

- 映射条目数: **35**
- face_* 映射: 2
- voice_* 映射: 33
- 映射到的 person 数: 6
- Person IDs: `['person_1', 'person_2', 'person_3', 'person_4', 'person_5', 'person_6']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `study_05_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 discusses homework with person_2 and understands person_2's approach
- description: person_1 arrives home, walks through a hallway, and enters person_2's bedroom. person_1 initiates a ...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='walks through a hallway and enters a bedroom, then greets person_2', object='N/A', location='hallway, bedroom'}`
- Step 2: `{action='expresses tiredness and mentions having a lot of homework', object='N/A', location='bedroom'}`
- Step 3: `{action='replies that she has finished homework in school', object='N/A', location='bedroom'}`
- Step 4: `{action='asks why person_2 finished homework just in school', object='N/A', location='bedroom'}`
- Step 5: `{action='explains her reasoning for finishing homework in school', object='N/A', location='bedroom'}`

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
- `created_at`: 2026-02-04T12:33:16.455718
- `updated_at`: 2026-02-04T12:33:16.455742
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [0]
- `version`: 2.3.2

### Procedure 2: `study_05_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 suggests finishing craft work before dinner
- description: person_1 initiates a suggestion to other individuals regarding the completion of a shared activity (...

**Steps 详情:**
- 数量: 1
- Step 1: `{action='suggests finishing', object='craft work', location='at a desk'}`

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
- Link 1: clip_id=`4`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:33:37.068506
- `updated_at`: 2026-02-04T12:33:37.068530
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [4]
- `version`: 2.3.2

### Procedure 3: `study_05_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: person_1 fixes something
- description: person_1 is engaged in fixing an unspecified item and, realizing a need for adhesive, asks person_2 ...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='initiates fixing', object='something', location='N/A'}`
- Step 2: `{action='identifies need', object='glue', location='N/A'}`
- Step 3: `{action='asks', object='glue', location='N/A'}`

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
- Link 1: clip_id=`19`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T12:34:45.688300
- `updated_at`: 2026-02-04T12:34:45.688325
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [19]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (1 个)

- ❌ Episodic 覆盖率过低: 21.7%

### 警告 (3 个)

- ⚠️ 所有边的转移计数未被更新
- ⚠️ 所有 DAG 都是线性结构，无分支
- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱存在 1 个问题，建议修复**