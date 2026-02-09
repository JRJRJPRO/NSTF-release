# NSTF 图谱分析报告

**视频:** `gym_03`  
**数据集:** `robot`  
**模式:** 增量模式 (incremental)  
**分析时间:** 2026-02-05 10:34:31  
**NSTF 路径:** `data/nstf_graphs/robot/gym_03_nstf.pkl`

---


## 1. 加载图谱

✅ 找到 NSTF 图谱: `data/nstf_graphs/robot/gym_03_nstf.pkl`
✅ 找到 Video Graph: `data/memory_graphs/robot/gym_03.pkl`
✅ NSTF 图谱加载成功
✅ Video Graph 加载成功

## 2. 顶层结构分析

✅ 所有预期顶层字段都存在

**基本信息:**
- 视频名称: `gym_03`
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

- `social`: 17
- `task`: 10
- `trait`: 1

### Steps 统计

- 总数: **83**
- 范围: 1 - 7
- 平均: 3.0
✅ 所有 Procedure 都有 steps

### DAG 结构统计

- nodes 数量: 3 - 9 (avg: 5.0)
- edges 数量: 2 - 8 (avg: 4.0)

### Episodic Links 统计

- 数量范围: 1 - 7
- 平均: 1.5
✅ 所有 embeddings 正常

## 4. DAG 结构详细分析

- 有效 DAG 数量: **28/28**
- Steps/DAG 一致: **28/28**
✅ 所有 Procedure 都有有效的 DAG 结构

## 4.5 边转移统计分析


### 边计数统计

- count 范围: 1 - 2
- count 均值: 1.02
- 所有 count=1 的 Procedure: 26/28
⚠️ 大部分 Procedure 的 count 未更新

### 概率分布统计

- 所有 prob=1.0 的 Procedure: 28/28
⚠️ 所有 Procedure 的概率分布无差异！

### DAG 分支结构统计

- 线性 DAG: 28/28
- 有分支的 DAG: **0/28**
⚠️ 没有任何 DAG 有分支结构！

## 5. Episodic 覆盖率分析

- Video Graph 总 clips: **68**
- NSTF 引用的 clips: **41**
- 覆盖率: **60.3%**
✅ 覆盖率 >= 50%
- 未覆盖的 clips: `[0, 3, 5, 8, 9, 11, 22, 24, 25, 32]...` (共 27 个)

## 6. Goal 质量分析

- 总 Procedure 数: **28**
- 模糊 Goal 数: 2
- 具体 Goal 数: 2

### 模糊 Goals (包含 'something/things' 等)

- ⚠️ `gym_03_proc_14`: person_1 provides objects to person_20 for person_20 to try
- ⚠️ `gym_03_proc_26`: person_1 and person_1 engage in a conversation about an item and express their states of mind.
⚠️ 只有 2/28 个 Goal 包含具体信息

### 所有 Goals

- person_1 initiating a conversation with person_3 about person_3's fitness profession
- person_1 explains a training/exercise to person_4
- Demonstrate various ways to hold and use a long, red, flexible stick
- person_1 learns to swing a wooden stick by observing person_8's practice
- Perform a post-workout routine involving stretching and cleaning
- Initiating an exercise sequence on a blue exercise mat
- person_9 provides hydration and support to person_1 during exercise
- person_1 reminds person_2 about the importance of correct posture to prevent injuries
- person_1 observes person_5
- Perform an upper body exercise using resistance bands
- To conduct a post-workout debriefing regarding muscle soreness.
- Guiding an exercise session to build muscle fullness
- Perform a flying bird arm movement
- person_1 provides objects to person_20 for person_20 to try
- Performing dumbbell exercises
- person_1 and the instructor engage in a discussion
- person_1 demonstrates a growth mindset during a strength training exercise
- person_1 offers a replacement bottle of water to person_2 after person_2's water spilled
- Provide orange juice to a person
- To coordinate the next steps of an activity between person_1 and person_2
- person_1 (wearing white t-shirt) to obtain wrist protection and back support
- person_1 and person_2 prepare for an exercise activity
- Establish the initial social interaction and positioning between person_1 and person_2
- person_1 and person_2 engage in a conversation about availability and a movie
- person_2 provides person_1 with a bottle of water.
- person_1 and person_1 engage in a conversation about an item and express their states of mind.
- person_1 advises person_2 to increase physical activity after working from home
- person_21 and person_1 coordinate to take a shower after person_21 hands person_1 a jacket

## 7. Character Mapping 分析

- 映射条目数: **65**
- face_* 映射: 2
- voice_* 映射: 63
- 映射到的 person 数: 21
- Person IDs: `['person_1', 'person_10', 'person_11', 'person_12', 'person_13', 'person_14', 'person_15', 'person_16', 'person_17', 'person_18']...`

## 8. Procedure 完整详情 (前 3 个)


### Procedure 1: `gym_03_proc_1`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 initiating a conversation with person_3 about person_3's fitness profession
- description: person_1 initiates a conversation with person_3 by asking about person_3's profession in fitness. pe...

**Steps 详情:**
- 数量: 3
- Step 1: `{action='asks a question', object='N/A', location='room'}`
- Step 2: `{action='confirms', object='N/A', location='room'}`
- Step 3: `{action='asks a follow-up question', object='N/A', location='room'}`

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
- Link 1: clip_id=`1`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:44:54.894787
- `updated_at`: 2026-02-04T14:44:54.894809
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [1]
- `version`: 2.3.2

### Procedure 2: `gym_03_proc_2`

**基本信息:**
- type: `procedure`
- proc_type: `social`
- goal: person_1 explains a training/exercise to person_4
- description: person_1 communicates instructions or information regarding a training or exercise to person_4, who ...

**Steps 详情:**
- 数量: 5
- Step 1: `{action='suggests', object='N/A', location='N/A'}`
- Step 2: `{action='stretches', object='right leg', location='N/A'}`
- Step 3: `{action='suggests', object='wooden stick', location='N/A'}`
- Step 4: `{action='demonstrates', object='wooden stick', location='N/A'}`
- Step 5: `{action='watches', object='N/A', location='N/A'}`

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
- 数量: 2
- Link 1: clip_id=`2`, relevance=`source`, similarity=`1.0`
- Link 2: clip_id=`6`, relevance=`update`, similarity=`0.6704`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_goal_emb`: shape=`(3072,)`, dtype=`float64`
- `anchor_step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:45:12.535212
- `updated_at`: 2026-02-04T14:46:09.661571
- `source`: incremental_nstf
- `observation_count`: 2
- `source_clips`: [2, 6]
- `version`: 2.3.2

### Procedure 3: `gym_03_proc_3`

**基本信息:**
- type: `procedure`
- proc_type: `task`
- goal: Demonstrate various ways to hold and use a long, red, flexible stick
- description: person_1 demonstrates multiple techniques for manipulating a long, red, flexible stick, including ra...

**Steps 详情:**
- 数量: 7
- Step 1: `{action='holds', object='long, red, flexible stick', location='N/A'}`
- Step 2: `{action='raises', object='long, red, flexible stick', location='above her head'}`
- Step 3: `{action='holds', object='long, red, flexible stick', location='N/A'}`
- Step 4: `{action='bends', object='long, red, flexible stick', location='at the waist'}`
- Step 5: `{action='places', object='long, red, flexible stick', location='on the floor'}`
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
- 数量: 1
- Link 1: clip_id=`4`, relevance=`source`, similarity=`1.0`

**Embeddings 信息:**
- `goal_emb`: shape=`(3072,)`, dtype=`float64`
- `step_emb`: shape=`(3072,)`, dtype=`float64`

**Metadata 信息:**
- `created_at`: 2026-02-04T14:45:44.450528
- `updated_at`: 2026-02-04T14:45:44.450550
- `source`: incremental_nstf
- `observation_count`: 1
- `source_clips`: [4]
- `version`: 2.3.2

## 9. 诊断总结


### 错误 (0 个)

✅ 无错误

### 警告 (2 个)

- ⚠️ 所有 DAG 都是线性结构，无分支
- ⚠️ 大部分 Goal 太抽象

### 总体评估

⚠️ **图谱基本完整，但有 2 个警告需要关注**