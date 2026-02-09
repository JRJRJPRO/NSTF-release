# NSTF 图谱分析: study_09

**来源**: data/nstf_graphs/robot/study_09_nstf.pkl  
**解析时间**: 2026-02-03 15:09:10  
**NSTF 版本**: 2.3.0

---

## 📊 图谱统计

| 指标 | 数值 |
|------|------|
| Procedure 数量 | 5 |
| 总步骤数 | 24 |
| 总边数 | 32 |
| Episodic 链接数 | 41 |
| 平均链接/Procedure | 8.2 |
| 融合前 Procedure 数 | 5 |

## 📝 构建元数据

| 字段 | 值 |
|------|-----|
| 视频名称 | study_09 |
| 数据集 | robot |
| 创建时间 | 2026-02-03T13:25:40.567019 |
| 处理耗时 | 129.3 秒 |
| 融合启用 | 是 |

## 👥 Character 映射

| Character ID | 名称/描述 |
|--------------|-----------|
| <face_2114> | person_1 |
| <voice_0> | person_1 |
| <voice_1118> | person_2 |
| <voice_1244> | person_2 |
| <voice_1284> | person_1 |
| <voice_1343> | person_1 |
| <voice_1421> | person_1 |
| <voice_1499> | person_1 |
| <voice_1652> | person_1 |
| <voice_1727> | person_1 |
| <voice_1811> | person_1 |
| <voice_1812> | person_1 |
| <voice_1921> | person_1 |
| <voice_1947> | person_1 |
| <voice_1> | person_1 |
| <voice_2005> | person_2 |
| <voice_2157> | person_1 |
| <voice_305> | person_1 |
| <voice_306> | person_1 |
| <voice_33> | person_1 |
| <voice_494> | person_1 |
| <voice_535> | person_1 |
| <voice_695> | person_2 |

## 🔄 Procedure 详情

### 📋 study_09_proc_1

**Goal**: Organize books on a wooden shelf

**Description**: The task involves arranging books on a wooden shelf in a neat and systematic manner, potentially including clearing, sorting, and cleaning.

| 统计 | 数值 |
|------|------|
| 步骤数 | 5 |
| 边数 | 7 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Remove all books and other items from the wooden shelf.
   - 预期结果: Shelf is empty or mostly empty, Books are in a temporary location (e.g., floor, table)
   - 时长: 60s

**step_2**: Sort books by desired criteria (e.g., genre, size, author, color).
   - 触发条件: Books are removed from the shelf
   - 预期结果: Books are categorized and ready for placement
   - 时长: 120s

**step_3**: Wipe down the wooden shelf to remove dust or debris.
   - 触发条件: Shelf is empty
   - 预期结果: Shelf is clean
   - 时长: 30s

**step_4**: Place the sorted books back onto the wooden shelf.
   - 触发条件: Books are sorted, Shelf is clean (optional)
   - 预期结果: Books are on the shelf in an initial organized manner
   - 时长: 90s

**step_5**: Make minor adjustments to the book arrangement for aesthetics and stability.
   - 触发条件: Books are placed on the shelf
   - 预期结果: Books are perfectly organized on the shelf
   - 时长: 45s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 0.50 | Shelf needs cleaning |
| ? | ? | 0.50 | Shelf does not need cleaning |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 26 | discovered | 0.632 | - |
| 3 | discovered | 0.576 | - |
| 27 | source | 0.554 | - |
| 28 | source | 0.550 | - |
| 4 | discovered | 0.525 | - |
| 25 | discovered | 0.494 | - |
| 8 | discovered | 0.490 | - |
| 30 | discovered | 0.479 | - |
| 2 | discovered | 0.475 | - |
| 17 | discovered | 0.457 | - |

---

### 📋 study_09_proc_2

**Goal**: Set and manage goals using a specific method

**Description**: This task involves selecting a specific methodology for goal setting, defining goals according to its principles, planning actions, and continuously managing progress through monitoring, review, and adjustment until the goal is achieved or concluded.

| 统计 | 数值 |
|------|------|
| 步骤数 | 7 |
| 边数 | 8 |
| Episodic 链接数 | 1 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Select and understand a specific goal-setting method.
   - 预期结果: Chosen goal-setting method understood
   - 时长: 60s

**step_2**: Define the goal clearly using the chosen method's framework.
   - 触发条件: Chosen goal-setting method understood
   - 预期结果: Clearly defined goal adhering to method's criteria
   - 时长: 120s

**step_3**: Create an actionable plan with specific tasks, resources, and timelines.
   - 触发条件: Clearly defined goal adhering to method's criteria
   - 预期结果: Detailed action plan with tasks, resources, and timelines
   - 时长: 180s

**step_4**: Execute the initial action plan.
   - 触发条件: Detailed action plan with tasks, resources, and timelines
   - 预期结果: Action plan implementation initiated
   - 时长: 300s

**step_5**: Continuously monitor progress, track metrics, and identify deviations.
   - 触发条件: Action plan implementation initiated
   - 预期结果: Progress data collected and deviations identified
   - 时长: 240s

**step_6**: Review performance, evaluate effectiveness, and make necessary adjustments to the plan or goal.
   - 触发条件: Progress data collected and deviations identified
   - 预期结果: Adjustments to plan or goal decided and applied
   - 时长: 150s

**step_7**: Achieve the goal or complete the goal management cycle.
   - 触发条件: Adjustments to plan or goal decided and applied
   - 预期结果: Goal achieved, Goal management cycle concluded
   - 时长: 90s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 37 | discovered | 0.341 | - |

---

### 📋 study_09_proc_3

**Goal**: Participate in collaborative activities at the round table

**Description**: This habit describes the process of individuals gathering at a round table to engage in shared tasks or discussions.

| 统计 | 数值 |
|------|------|
| 步骤数 | 4 |
| 边数 | 5 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Enter the room containing the round table.
   - 预期结果: person_1 is in the room with the round table
   - 时长: 10s

**step_2**: Approach and take a seat at the round table.
   - 触发条件: person_1 is in the room, round table is present
   - 预期结果: person_1 is seated at the round table
   - 时长: 15s

**step_3**: Initiate or join a collaborative discussion or shared task with others at the table.
   - 触发条件: multiple people are seated at the table
   - 预期结果: collaborative activity begins
   - 时长: 30s

**step_4**: Actively contribute to the ongoing collaborative activity.
   - 触发条件: collaborative activity is in progress
   - 预期结果: participation in the activity continues
   - 时长: 60s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 42 | discovered | 0.484 | - |
| 46 | discovered | 0.474 | - |
| 18 | discovered | 0.468 | - |
| 19 | discovered | 0.458 | - |
| 20 | discovered | 0.456 | - |
| 43 | discovered | 0.454 | - |
| 37 | discovered | 0.445 | - |
| 23 | discovered | 0.444 | - |
| 47 | discovered | 0.444 | - |
| 39 | discovered | 0.442 | - |

---

### 📋 study_09_proc_4

**Goal**: When in a group setting requiring new activity/method

**Description**: Describes a situation characterized by the presence of multiple individuals and the necessity to introduce a novel activity or approach.

| 统计 | 数值 |
|------|------|
| 步骤数 | 2 |
| 边数 | 4 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Presence of a group setting

**step_2**: Requirement for a new activity or method

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | AND step_2 is true |
| ? | ? | 1.00 | AND step_1 is true |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 42 | discovered | 0.476 | - |
| 19 | discovered | 0.423 | - |
| 43 | discovered | 0.418 | - |
| 46 | discovered | 0.414 | - |
| 8 | discovered | 0.413 | - |
| 7 | discovered | 0.413 | - |
| 39 | discovered | 0.413 | - |
| 37 | discovered | 0.410 | - |
| 23 | discovered | 0.409 | - |
| 44 | discovered | 0.403 | - |

---

### 📋 study_09_proc_5

**Goal**: Engage in collaborative activities or discussions

**Description**: A process involving multiple individuals working together or communicating to achieve a common objective or share perspectives.

| 统计 | 数值 |
|------|------|
| 步骤数 | 6 |
| 边数 | 8 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Initiate interaction or gather participants
   - 触发条件: Need for collaboration/discussion arises, A meeting is scheduled
   - 预期结果: Participants are present and ready to interact
   - 时长: 15s

**step_2**: Exchange information and ideas
   - 触发条件: Interaction has been initiated
   - 预期结果: Information is shared among participants, Different perspectives are introduced
   - 时长: 60s

**step_3**: Process and respond to shared content
   - 触发条件: Information and ideas have been exchanged
   - 预期结果: Deeper understanding is achieved, New ideas are developed, Points of agreement/disagreement are identified
   - 时长: 90s

**step_4a**: Jointly work on a shared task (for collaborative activities)
   - 触发条件: Agreement on a task requiring joint effort
   - 预期结果: Progress is made on the shared task
   - 时长: 120s

**step_4b**: Continue dialogue and explore topics (for discussions)
   - 触发条件: Unresolved points or desire for further exploration
   - 预期结果: Broader understanding is gained, Nuanced perspectives are developed
   - 时长: 120s

**step_5**: Conclude the interaction
   - 触发条件: Task completion, Time limit reached, Consensus achieved, Natural end of conversation
   - 预期结果: Resolution is reached, Plan of action is established, Cessation of interaction
   - 时长: 30s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 0.50 | If the activity involves a shared task |
| ? | ? | 0.50 | If the activity is primarily a discussion |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 42 | discovered | 0.429 | - |
| 19 | source | 0.404 | - |
| 46 | discovered | 0.396 | - |
| 18 | source | 0.395 | - |
| 43 | discovered | 0.391 | - |
| 23 | discovered | 0.390 | - |
| 37 | discovered | 0.390 | - |
| 20 | discovered | 0.375 | - |
| 47 | discovered | 0.369 | - |
| 39 | discovered | 0.366 | - |

---

## 🔍 与 Baseline 图谱的关联

NSTF 图谱基于 Baseline Memory Graph 构建，通过以下方式关联：

1. **Episodic Links**: 每个 Procedure 的 `episodic_links` 字段指向 Baseline 图谱中的 Clip ID
2. **Character Mapping**: 将 Baseline 中的 `<face_N>`, `<voice_N>` 映射为统一的 character ID
3. **时序对齐**: Procedure 的步骤顺序与原始 Episodic 事件的时序保持一致
