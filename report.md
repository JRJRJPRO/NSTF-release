================================================================================
NSTF 图谱详细分析报告
视频: kitchen_03 | 数据集: robot
生成时间: 2026-02-03 18:30:52
================================================================================

============================================================
## 1. 图谱顶层结构
============================================================

顶层 Keys: ['video_name', 'dataset', 'procedure_nodes', 'character_mapping', 'metadata', 'stats']
  video_name: str = kitchen_03
  dataset: str = robot
  procedure_nodes: dict (5 items)
  character_mapping: dict (59 items)
  metadata: dict (5 items)
  stats: dict (6 items)

Metadata:
  version: 2.3.0
  created_at: 2026-02-03T18:27:23.051913
  num_procedures: 5
  processing_time: 171.40207600593567
  fusion_enabled: True

构建统计:
  total_procedures: 5
  total_links: 50
  avg_links_per_proc: 10.0
  character_mapping_found: True
  fusion_performed: 0
  procedures_before_fusion: 5

============================================================
## 2. Procedure Nodes 概览
============================================================

总共 5 个 Procedure

字段出现次数:
  ✅ proc_id: 5/5 (100%)
  ✅ type: 5/5 (100%)
  ✅ goal: 5/5 (100%)
  ✅ description: 5/5 (100%)
  ✅ proc_type: 5/5 (100%)
  ✅ steps: 5/5 (100%)
  ✅ dag: 5/5 (100%)
  ✅ edges: 5/5 (100%)
  ✅ objects: 5/5 (100%)
  ✅ locations: 5/5 (100%)
  ✅ participants: 5/5 (100%)
  ✅ episodic_links: 5/5 (100%)
  ✅ embeddings: 5/5 (100%)
  ✅ metadata: 5/5 (100%)

新格式必要字段检查:
  ✅ proc_id: 5/5
  ✅ goal: 5/5
  ✅ steps: 5/5
  ✅ objects: 5/5
  ✅ locations: 5/5
  ✅ edges: 5/5

============================================================
## 3. Steps 详细分析
============================================================

步骤数量统计:
  有步骤的 Procedure: 3/5 (60%)
  步骤数分布: min=0, max=6, avg=2.8

步骤字段填充率 (共 14 个步骤):
  有 action: 14/14 (100%)
  有 object: 14/14 (100%)
  有 location: 14/14 (100%)

步骤示例 (前3个有步骤的 Procedure):

  [kitchen_03_proc_1] Goal: Unpack all groceries from their bags and place them onto the white kitchen countertops, including initial handling of items like broccoli.
    Step 1: Bring grocery bags | obj: grocery bags | loc: white kitchen countertop
    Step 2: Take a grocery item | obj: grocery item | loc: grocery bag
    Step 3: Place the grocery item | obj: grocery item | loc: white kitchen countertop
    Step 4: Hold a head of broccoli | obj: head of broccoli | loc: white kitchen countertop
    Step 5: Examine and rotate the head of broccoli | obj: head of broccoli | loc: white kitchen countertop
    ... (1 more steps)

  [kitchen_03_proc_2] Goal: Peel outer leaves from a head of broccoli
    Step 1: Hold a head of broccoli | obj: head of broccoli | loc: white countertop
    Step 2: Examine the broccoli by rotating it to show the white stem and green florets | obj: broccoli | loc: white countertop
    Step 3: Peel off some of the outer leaves | obj: outer leaves | loc: white countertop

  [kitchen_03_proc_5] Goal: Retrieve milk, eggs, and yogurt from the refrigerator and then close the refrigerator door.
    Step 1: Open | obj: refrigerator door | loc: refrigerator
    Step 2: Retrieve | obj: milk | loc: refrigerator
    Step 3: Retrieve | obj: eggs | loc: refrigerator
    Step 4: Retrieve | obj: yogurt | loc: refrigerator
    Step 5: Close | obj: refrigerator door | loc: refrigerator

============================================================
## 4. Objects & Locations 分析
============================================================

有 objects 的 Procedure: 5/5
有 locations 的 Procedure: 5/5

所有 Objects (共 67 种):
  groceries: 5次
  head of broccoli: 5次
  purple trash bin: 5次
  black chair: 5次
  black gloves: 4次
  red cabinets: 4次
  white countertops: 4次
  patterned cushion: 4次
  blue apron: 4次
  outer leaves: 3次
  refrigerator: 3次
  cabinet door: 3次
  red basketball hoop: 3次
  wooden t: 3次
  round decorative sticker with Chinese characters: 3次
  white jacket: 3次
  glasses: 3次
  blue stripes: 2次
  black pants: 2次
  beige jacket: 2次
  ... 还有 47 种

所有 Locations (共 26 种):
  red cabinets: 5次
  door: 5次
  room: 4次
  floor: 4次
  refrigerator: 4次
  white countertops: 4次
  counter: 4次
  modern kitchen: 3次
  striped walls: 3次
  light-colored tiled floors: 3次
  kitchen: 2次
  beneath the counter: 2次
  light gray floor: 2次
  striped wallpaper: 2次
  white kitchen countertop: 1次
  purple trash bin: 1次
  gray walls: 1次
  kitchen area: 1次
  white cabinets: 1次
  backgroun: 1次
  ... 还有 6 种

============================================================
## 5. DAG 边结构分析
============================================================

有 edges 的 Procedure: 4/5
总边数: 18
边数分布: min=0, max=7, avg=3.6

DAG 边示例:

  [kitchen_03_proc_1]
    START -> step_1 (count: 1)
    step_1 -> step_2 (count: 1)
    step_2 -> step_3 (count: 1)
    step_3 -> step_4 (count: 1)
    step_4 -> step_5 (count: 1)
    ... (2 more edges)

  [kitchen_03_proc_2]
    START -> step_1 (count: 1)
    step_1 -> step_2 (count: 1)
    step_2 -> step_3 (count: 1)
    step_3 -> GOAL (count: 1)

============================================================
## 6. Episodic Links 分析
============================================================

有 episodic_links 的 Procedure: 5/5
引用的不同 clip 数: 27
链接数分布: min=10, max=10, avg=10.0
相似度分布: min=0.38, max=0.73, avg=0.55

引用的 Clip IDs: [1, 2, 3, 4, 5, 6, 7, 13, 14, 15, 17, 18, 20, 21, 23, 24, 27, 28, 29, 37]...

============================================================
## 7. 视频覆盖率分析
============================================================

Video Graph 总 clip 数: 74
NSTF 引用的 clip 数: 27
覆盖率: 36.5%

未被引用的 clip (47 个):
  [0, 8, 9, 10, 11, 12, 16, 19, 22, 25, 26, 30, 31, 32, 33, 34, 35, 36, 39, 40]...

============================================================
## 8. 图谱质量总结
============================================================

优点:
  ✅ 所有 Procedure 都有 objects
  ✅ 所有 Procedure 都有 locations
  ✅ 所有 Procedure 都有 episodic_links

问题:
  ⚠️  只有 3/5 个 Procedure 有 steps
  ⚠️  只有 4/5 个 Procedure 有 edges

总体评分: 60% - B (良好)