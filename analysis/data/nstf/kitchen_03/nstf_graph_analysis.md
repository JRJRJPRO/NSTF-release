# NSTF 图谱分析: kitchen_03

**来源**: data/nstf_graphs/robot/kitchen_03_nstf.pkl  
**解析时间**: 2026-02-03 16:24:30  
**NSTF 版本**: 2.3.0

---

## 📊 图谱统计

| 指标 | 数值 |
|------|------|
| Procedure 数量 | 5 |
| 总步骤数 | 21 |
| 总边数 | 27 |
| Episodic 链接数 | 46 |
| 平均链接/Procedure | 9.2 |
| 融合前 Procedure 数 | 5 |

## 📝 构建元数据

| 字段 | 值 |
|------|-----|
| 视频名称 | kitchen_03 |
| 数据集 | robot |
| 创建时间 | 2026-02-03T13:23:29.238677 |
| 处理耗时 | 101.2 秒 |
| 融合启用 | 是 |

## 👥 Character 映射

| Character ID | 名称/描述 |
|--------------|-----------|
| <face_2> | person_1 |
| <face_3> | person_1 |
| <voice_0> | person_1 |
| <voice_1097> | person_1 |
| <voice_1301> | person_1 |
| <voice_1302> | person_1 |
| <voice_131> | person_2 |
| <voice_1348> | person_1 |
| <voice_1383> | person_1 |
| <voice_1384> | person_1 |
| <voice_1385> | person_1 |
| <voice_1427> | person_1 |
| <voice_1502> | person_1 |
| <voice_1503> | person_1 |
| <voice_1544> | person_1 |
| <voice_1545> | person_1 |
| <voice_160> | person_1 |
| <voice_1685> | person_1 |
| <voice_1720> | person_1 |
| <voice_1759> | person_1 |
| <voice_1906> | person_1 |
| <voice_197> | person_1 |
| <voice_198> | person_1 |
| <voice_1> | person_1 |
| <voice_2307> | person_1 |
| <voice_2347> | person_1 |
| <voice_2411> | person_3 |
| <voice_2412> | person_3 |
| <voice_301> | person_1 |
| <voice_302> | person_1 |
| <voice_303> | person_1 |
| <voice_304> | person_1 |
| <voice_305> | person_1 |
| <voice_348> | person_1 |
| <voice_349> | person_1 |
| <voice_383> | person_1 |
| <voice_384> | person_1 |
| <voice_430> | person_1 |
| <voice_475> | person_1 |
| <voice_476> | person_1 |
| <voice_50> | person_1 |
| <voice_514> | person_5 |
| <voice_541> | person_1 |
| <voice_542> | person_4 |
| <voice_570> | person_1 |
| <voice_571> | person_1 |
| <voice_609> | person_1 |
| <voice_610> | person_1 |
| <voice_713> | person_1 |
| <voice_750> | person_1 |
| <voice_788> | person_1 |
| <voice_789> | person_1 |
| <voice_878> | person_1 |
| <voice_879> | person_1 |
| <voice_91> | person_1 |
| <voice_92> | person_1 |
| <voice_93> | person_1 |
| <voice_989> | person_1 |
| <voice_990> | person_1 |

## 🔄 Procedure 详情

### 📋 kitchen_03_proc_1

**Goal**: Food Preparation Initiation

**Description**: The initial phase of preparing food, characterized by entering the kitchen, gathering necessary ingredients, and commencing the first physical interaction or processing of a food item.

| 统计 | 数值 |
|------|------|
| 步骤数 | 3 |
| 边数 | 4 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Enter the kitchen or designated food preparation area.
   - 预期结果: Person is present in the kitchen.
   - 时长: 5s

**step_2**: Access or retrieve ingredients for preparation.
   - 触发条件: Person is present in the kitchen.
   - 预期结果: Ingredients are available on the counter or in hand.
   - 时长: 15s

**step_3**: Begin initial handling or examination of a food ingredient.
   - 触发条件: Ingredients are available.
   - 预期结果: First ingredient is being processed or inspected.
   - 时长: 20s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 17 | discovered | 0.485 | - |
| 23 | discovered | 0.431 | - |
| 40 | discovered | 0.427 | - |
| 42 | discovered | 0.424 | - |
| 24 | discovered | 0.420 | - |
| 14 | discovered | 0.419 | - |
| 5 | discovered | 0.416 | - |
| 70 | discovered | 0.414 | - |
| 8 | discovered | 0.398 | - |
| 47 | discovered | 0.396 | - |

---

### 📋 kitchen_03_proc_2

**Goal**: Ingredient Quality Inspection

**Description**: The habit of visually examining an ingredient, often by holding and rotating it, to assess its quality before use.

| 统计 | 数值 |
|------|------|
| 步骤数 | 2 |
| 边数 | 3 |
| Episodic 链接数 | 6 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Obtain ingredient for inspection
   - 触发条件: Need to use an ingredient, Preparing to cook
   - 预期结果: Ingredient is in hand and ready for examination
   - 时长: 5s

**step_2**: Visually inspect ingredient by examining and rotating
   - 触发条件: Ingredient is obtained
   - 预期结果: Quality assessment of the ingredient is made
   - 时长: 20s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 35 | discovered | 0.356 | - |
| 24 | discovered | 0.335 | - |
| 23 | discovered | 0.331 | - |
| 17 | discovered | 0.316 | - |
| 39 | discovered | 0.313 | - |
| 70 | discovered | 0.309 | - |

---

### 📋 kitchen_03_proc_3

**Goal**: Kitchen Workspace Organization

**Description**: The process of decluttering, cleaning, and arranging items in a kitchen workspace to improve functionality and aesthetics.

| 统计 | 数值 |
|------|------|
| 步骤数 | 5 |
| 边数 | 6 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**clear_workspace**: Clear all items from the kitchen countertops and main workspace areas.
   - 预期结果: Workspace is empty of clutter
   - 时长: 60s

**clean_surfaces**: Wipe down and clean all cleared kitchen surfaces, including countertops and stovetop.
   - 触发条件: Workspace is empty of clutter
   - 预期结果: Workspace surfaces are clean
   - 时长: 45s

**sort_items**: Sort all removed items into categories (e.g., utensils, small appliances, ingredients, produce).
   - 触发条件: Workspace surfaces are clean
   - 预期结果: Items are grouped by category
   - 时长: 90s

**store_items**: Place sorted items into their designated storage locations such as cabinets, drawers, or pantry.
   - 触发条件: Items are grouped by category
   - 预期结果: Items are stored away
   - 时长: 120s

**arrange_essentials**: Arrange frequently used tools, appliances, and ingredients neatly on the workspace for easy access.
   - 触发条件: Items are stored away
   - 预期结果: Workspace is organized and functional
   - 时长: 75s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 63 | discovered | 0.464 | - |
| 65 | discovered | 0.451 | - |
| 57 | discovered | 0.443 | - |
| 62 | discovered | 0.441 | - |
| 58 | discovered | 0.438 | - |
| 64 | discovered | 0.422 | - |
| 70 | discovered | 0.418 | - |
| 61 | discovered | 0.417 | - |
| 23 | discovered | 0.414 | - |
| 6 | discovered | 0.412 | - |

---

### 📋 kitchen_03_proc_4

**Goal**: Wearing Gloves for Food Handling

**Description**: The routine practice of a person putting on and wearing protective gloves specifically for the purpose of handling or preparing food items, ensuring hygiene and safety.

| 统计 | 数值 |
|------|------|
| 步骤数 | 4 |
| 边数 | 5 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Person prepares for food handling activity
   - 时长: 10s

**step_2**: Person acquires protective gloves
   - 时长: 5s

**step_3**: Person dons gloves onto hands
   - 时长: 10s

**step_4**: Person handles food while wearing gloves
   - 时长: 30s

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
| 24 | discovered | 0.389 | - |
| 70 | discovered | 0.375 | - |
| 7 | discovered | 0.344 | - |
| 14 | discovered | 0.315 | - |
| 58 | discovered | 0.314 | - |
| 65 | discovered | 0.310 | - |
| 26 | discovered | 0.308 | - |
| 23 | discovered | 0.307 | - |
| 17 | discovered | 0.304 | - |
| 3 | discovered | 0.304 | - |

---

### 📋 kitchen_03_proc_5

**Goal**: Washing Produce

**Description**: The task of cleaning fruits and vegetables to remove dirt, pesticides, and other contaminants before consumption or further preparation.

| 统计 | 数值 |
|------|------|
| 步骤数 | 7 |
| 边数 | 9 |
| Episodic 链接数 | 10 |
| Embedding | goal_emb: 3072维, step_emb: 3072维 |

#### 📝 步骤序列

**step_1**: Retrieve produce
   - 预期结果: produce is accessible
   - 时长: 5s

**step_2**: Prepare sink area
   - 触发条件: produce is retrieved
   - 预期结果: sink is clear, colander/bowl is ready (if needed)
   - 时长: 10s

**step_3**: Turn on water
   - 触发条件: sink area is prepared
   - 预期结果: water is flowing, water temperature/flow is adjusted
   - 时长: 5s

**step_4a**: Soak produce
   - 触发条件: water is flowing
   - 预期结果: produce is submerged in water
   - 时长: 60s

**step_4b**: Directly rinse produce
   - 触发条件: water is flowing
   - 预期结果: produce is under running water
   - 时长: 15s

**step_5**: Thoroughly rinse/scrub produce
   - 触发条件: produce is soaked, produce is initially rinsed
   - 预期结果: produce is clean
   - 时长: 30s

**step_6**: Drain excess water
   - 触发条件: produce is clean
   - 预期结果: produce is free of excess water
   - 时长: 10s

#### 🔗 DAG 边（状态转移）

| 源步骤 | 目标步骤 | 概率/权重 | 条件 |
|--------|----------|-----------|------|
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 0.30 | produce requires soaking (e.g., leafy greens, berries) |
| ? | ? | 0.70 | produce can be directly rinsed (e.g., firm fruits, vegetables) |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |
| ? | ? | 1.00 | None |

#### 🎬 Episodic 链接（证据追溯）

| Clip ID | 相关性 | 相似度 | 步骤关联 |
|---------|--------|--------|----------|
| 24 | discovered | 0.462 | - |
| 70 | discovered | 0.449 | - |
| 7 | discovered | 0.375 | - |
| 3 | discovered | 0.340 | - |
| 64 | discovered | 0.337 | - |
| 6 | discovered | 0.333 | - |
| 23 | discovered | 0.332 | - |
| 63 | discovered | 0.330 | - |
| 62 | discovered | 0.327 | - |
| 65 | discovered | 0.327 | - |

---

## 🔍 与 Baseline 图谱的关联

NSTF 图谱基于 Baseline Memory Graph 构建，通过以下方式关联：

1. **Episodic Links**: 每个 Procedure 的 `episodic_links` 字段指向 Baseline 图谱中的 Clip ID
2. **Character Mapping**: 将 Baseline 中的 `<face_N>`, `<voice_N>` 映射为统一的 character ID
3. **时序对齐**: Procedure 的步骤顺序与原始 Episodic 事件的时序保持一致
