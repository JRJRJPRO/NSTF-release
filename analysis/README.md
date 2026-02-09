# 图谱与问答分析模块 (Analysis Module)

本模块用于**拆解和分析** Baseline 图谱、NSTF 图谱与问答结果，帮助理解模型行为并发现改进方向。


---

## 一、设计目标

1. **人可读格式**：将 pickle 格式的图谱转换为 Markdown/JSON，方便人工阅读和分析
2. **完整不截断**：所有文本内容完整保留，不做省略（embedding 除外，只显示维度）
3. **自动化执行**：给定视频列表文件，一条命令完成所有解析
4. **增量处理**：已解析的视频自动跳过，避免重复工作
5. **统一组织**：所有视频的解析结果统一存放，不区分 robot/web
6. **支持 NSTF**：完整解析 NSTF 图谱的 Procedure 节点、步骤、边、episodic 链接等

---

## 二、目录结构

```
NSTF_MODEL/analysis/
├── README.md                         # 本文档
├── config.json                       # 配置文件
├── run.py                            # 统一入口脚本
├── parsers/                          # 解析器模块
│   ├── __init__.py
│   ├── graph_parser.py               # Baseline 图谱解析器
│   ├── nstf_graph_parser.py          # NSTF 图谱解析器 ⭐
│   └── qa_parser.py                  # 问答结果解析器
├── templates/                        # Markdown 模板
│   ├── graph_template.md             # 图谱解析模板
│   └── qa_template.md                # 问答分析模板
└── data/                             # 解析输出目录
    ├── baseline/                     # Baseline 方法的分析结果
    │   ├── study_07/                 # 视频名作为文件夹
    │   │   ├── graph_analysis.md     # Baseline 图谱解析文档
    │   │   └── qa_results/           # 问答结果目录
    │   │       ├── Q01_analysis.md   # 第1个问题的分析
    │   │       ├── Q02_analysis.md
    │   │       └── ...
    │   └── ...
    ├── nstf/                         # NSTF 方法的分析结果
    │   ├── study_07/
    │   │   ├── graph_analysis.md     # Baseline 图谱解析
    │   │   ├── nstf_graph_analysis.md # NSTF 图谱解析 ⭐
    │   │   └── qa_results/
    │   │       └── ...
    │   └── ...
    └── nstf_level/                   # NSTF Level 方法（别名，同 nstf）
        └── ...
```

**说明**: 
- 输出按 `data/{method}/{video_id}/` 组织
- 同一视频在不同方法下的结果分开存放，便于对比分析
- Baseline 图谱解析对所有方法相同（因为图谱是共享的），问答结果按方法区分
- **NSTF 方法会同时输出 Baseline 和 NSTF 图谱分析**

---

## 三、核心 Schema

### 3.1 原始图谱结构（Baseline VideoGraph）

Baseline 模型生成的图谱是 pickle 序列化的 Python 对象，核心结构如下：

```python
class VideoGraph:
    """
    视频记忆图谱（从 pkl 文件反序列化）
    """
    
    # 节点存储
    nodes: Dict[int, Node]  # node_id -> Node 对象
    
    # 边存储  
    edges: List[Tuple[int, int, float]]  # (source_id, target_id, weight)
    
    # 人物映射（跨 Clip 追踪）
    character_mappings: Dict[str, List[int]]
    # 例: {"character_0": [10, 25, 42], "character_1": [11, 26]}
    # 表示 character_0 对应 node_id 10, 25, 42（可能是 face/voice 节点）
    
    # Clip 信息
    clip_ids: List[str]  # ["CLIP_0", "CLIP_1", ...]
    
class Node:
    """
    图谱节点
    """
    id: int
    type: str  # "episodic" | "semantic" | "img" | "voice"
    embeddings: List[List[float]]  # 向量列表（可能有多个）
    metadata: Dict[str, Any]  # 包含 contents, timestamp 等
```

### 3.2 NSTF 图谱结构 ⭐

NSTF 图谱是基于 Baseline 图谱提取的程序性知识，以 Procedure 为中心：

```python
{
    'video_name': str,
    'dataset': str,
    'procedure_nodes': {
        'proc_id': {
            'proc_id': str,
            'type': 'procedure',
            'goal': str,                    # 程序目标
            'description': str,             # 程序描述
            'steps': List[Dict],            # 步骤列表
            'edges': List[Dict],            # DAG 边（状态转移）
            'episodic_links': List[Dict],   # 追溯链接
            'embeddings': {'goal_emb': ndarray},
            'metadata': Dict,
            'fusion_info': Dict,            # 融合统计（如有）
        }
    },
    'character_mapping': Dict,
    'metadata': Dict,
    'stats': Dict,
}
```

**步骤结构 (steps)**:
```python
{
    'step_id': 'step_1',
    'action': str,                  # 动作描述
    'triggers': List[str],          # 触发条件
    'outcomes': List[str],          # 预期结果
    'duration_seconds': int,        # 预估时长
    'success_rate': float,          # 成功率
}
```

**Episodic 链接 (episodic_links)**:
```python
{
    'clip_id': int,                 # 关联的 Clip ID
    'relevance': str,               # 相关性类型 (source/evidence/etc.)
    'similarity': float,            # 相似度得分
    'step_id': str,                 # 关联的步骤 ID
}
```

### 3.3 节点类型详解

| 类型 | 说明 | Embedding 维度 | metadata.contents |
|------|------|----------------|-------------------|
| `episodic` | 情节记忆（具体事件） | 3072 (OpenAI) | 文本描述，含 `<face_X>`/`<voice_X>` |
| `semantic` | 语义记忆（归纳总结） | 3072 (OpenAI) | 概括性文本描述 |
| `img` | 人脸节点 | 512 (InsightFace) | Base64 编码的人脸图像 |
| `voice` | 语音节点 | 192 (SpeechBrain) | Base64 编码的音频 + ASR 文本 |

### 3.3 问答结果结构（来自 results/baseline/）

单个问题结果文件（JSON）的核心字段：

```json
{
  "schema_version": "1.0",
  "status": "success",
  "id": "study_07_Q01",
  "video_id": "study_07",
  "dataset": "robot",
  "method": "baseline",
  
  "question": "Where can the robot get the water?",
  "answer": "It's on the white cabinet that is near the bookshelf.",
  "type_original": ["Cross-Modal Reasoning", "General Knowledge Extraction"],
  "type_query": "Factual",
  
  "response": "The robot can get the water from the white cabinet in the room.",
  "gpt_eval": true,
  
  "num_rounds": 2,
  "elapsed_time_sec": 14.19,
  "search_count": 1,
  
  "retrieval_trace": [
    {
      "round": 1,
      "query": "Where is the water source located?",
      "num_results": 1,
      "clips": []
    }
  ],
  
  "conversations": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "Searched knowledge: {}"},
    {"role": "assistant", "content": "<think>...</think>\nAction: [Search]\nContent: ..."},
    {"role": "user", "content": "Searched knowledge: {...}"},
    {"role": "assistant", "content": "Action: [Answer]\nContent: ..."}
  ]
}
```

---

## 四、解析输出格式

### 4.1 图谱解析文档 (graph_analysis.md)

```markdown
# 视频图谱分析: study_07

**来源**: data/memory_graphs/robot/study_07.pkl  
**解析时间**: 2026-02-03 14:30:00

## 📊 图谱统计

| 指标 | 数值 |
|------|------|
| 总节点数 | 156 |
| Episodic 节点 | 82 |
| Semantic 节点 | 15 |
| Img 节点 | 35 |
| Voice 节点 | 24 |
| 总边数 | 210 |
| Clip 数量 | 10 |
| Character 数量 | 3 |

## 👥 人物映射 (Character Mappings)

| Character | 关联节点 ID | 类型分布 |
|-----------|------------|----------|
| character_0 | 10, 25, 42, 68 | img×2, voice×2 |
| character_1 | 11, 26, 43 | img×2, voice×1 |
| character_2 | 12, 44 | img×1, voice×1 |

## 📹 Clip 详情

### CLIP_0 (00:00:00 - 00:00:30)

#### Episodic 记忆 (8 条)

1. **Node 101** [episodic, 3072维]
   > The video takes place in a small, well-lit room with light-colored walls and a gray floor.

2. **Node 102** [episodic, 3072维]
   > The room contains a round table with a mosaic-style tabletop and a black base, two red chairs, a white cabinet, a wooden shelf, a floor lamp with a white conical shade, a standing fan, and several potted plants.

3. **Node 103** [episodic, 3072维]
   > A person wearing a yellow shirt and gray pants sits on a striped couch, holding a tablet.

4. **Node 104** [episodic, 3072维]
   > <character_0>: 'Lily, I have poured a glass of water for you. Remember to drink it.'

5. **Node 105** [episodic, 3072维]
   > <character_1>: 'Okay, thank you. I will drink it later.'

... (完整列出所有 episodic 节点)

#### Semantic 记忆 (1 条)

1. **Node 150** [semantic, 3072维]
   > The scene depicts a quiet moment of personal care and consideration within a domestic setting.

#### Img 节点 (4 个)

| Node ID | Quality Score | Bbox |
|---------|--------------|------|
| 10 | 25.3 | [120, 80, 280, 300] |
| 11 | 28.1 | [350, 90, 500, 310] |
| ... | ... | ... |

#### Voice 节点 (3 个)

| Node ID | ASR 文本 | 时长 |
|---------|---------|------|
| 20 | "Lily, I have poured a glass of water for you. Remember to drink it." | 3.2s |
| 21 | "Okay, thank you. I will drink it later." | 2.1s |
| ... | ... | ... |

### CLIP_1 (00:00:30 - 00:01:00)
... (同样格式)

## 🔗 边连接分析

| 边类型 | 数量 | 示例 |
|--------|------|------|
| episodic → img | 45 | Node 103 → Node 10 (weight: 1.0) |
| episodic → voice | 38 | Node 104 → Node 20 (weight: 1.0) |
| episodic → semantic | 15 | Node 101 → Node 150 (weight: 0.8) |
| ... | ... | ... |

```

### 4.2 问答分析文档 (Q01_analysis.md)

```markdown
# 问答分析: study_07_Q01

**视频**: study_07  
**数据集**: robot  
**方法**: baseline  
**解析时间**: 2026-02-03 14:35:00

---

## 📋 问题信息

| 字段 | 值 |
|------|-----|
| **问题** | Where can the robot get the water? |
| **标准答案** | It's on the white cabinet that is near the bookshelf. |
| **问题类型** | Cross-Modal Reasoning, General Knowledge Extraction |
| **Query Type** | Factual |
| **时间戳** | 00:43 |
| **Before Clip** | 0 |

---

## 🎯 结果摘要

| 指标 | 值 |
|------|-----|
| **模型回答** | The robot can get the water from the white cabinet in the room. |
| **GPT 评估** | ✅ 正确 |
| **LLM 轮数** | 2 |
| **耗时** | 14.19 秒 |
| **检索次数** | 1 |

---

## 🔍 检索过程追踪

### Round 1: 初始状态

**输入知识**: (空)

**LLM 思考**:
> Okay, the user is asking where the robot can get the water. Let me check the provided knowledge. Oh, the searched knowledge is empty, which means there's no information given here. Since there's no data about the robot's environment or available resources, I can't determine where the water is. I need to ask for more information. The previous search queries were about character IDs and names, but that's not relevant here. So I should generate a new search query related to the robot's location or water sources. Maybe something like "Where is the water source located?" or "What are the available water sources for the robot?". That should help retrieve the necessary details.

**LLM 行动**: `[Search] Where is the water source located?`

**检索结果**: 1 条

---

### Round 2: 获取信息后

**输入知识**:
```json
{
  "CLIP_0": [
    "The video takes place in a small, well-lit room with light-colored walls and a gray floor.",
    "The room contains a round table with a mosaic-style tabletop and a black base, two red chairs, a white cabinet, a wooden shelf, a floor lamp with a white conical shade, a standing fan, and several potted plants.",
    "A person wearing a yellow shirt and gray pants sits on a striped couch, holding a tablet.",
    "A black handbag rests on the round table.",
    "Another person, wearing a white shirt and gray pants, enters the room and walks towards the white cabinet.",
    "<character_0>: 'Lily, I have poured a glass of water for you. Remember to drink it.'",
    "<character_1>: 'Okay, thank you. I will drink it later.'",
    "The person in the white shirt places a glass of water on the round table and then sits down at the table.",
    "..."
  ]
}
```

**LLM 思考**:
> Okay, let's see. The user is asking where the robot can get the water. From the provided knowledge, there's a description of a room with a round table, a white cabinet, and other items. The characters in the scene are placing a glass of water on the table.
>
> First, I need to figure out if there's a specific location mentioned where water is stored or accessed. The knowledge mentions a white cabinet, which might be where the water is kept. Also, the person in the white shirt pours a glass of water, so maybe the cabinet has a water source or bottles. Alternatively, there's a floor lamp and a standing fan, but those don't relate directly to water storage.
>
> The key points are that the water is placed on the round table, but the source might be the cabinet. Since the cabinet is white and mentioned as storage, it's possible that the water comes from there. The robot would need to check the cabinet to get the water. There's no mention of a kitchen or other areas, so within the described room, the cabinet is the most likely source.

**LLM 行动**: `[Answer] The robot can get the water from the white cabinet in the room.`

---

## 💬 完整对话历史

### System Prompt

```
You are given a question and some relevant knowledge. Your task is to reason about whether the provided knowledge is sufficient to answer the question. If it is sufficient, output [Answer] followed by the answer. If it is not sufficient, output [Search] and generate a query that will be encoded into embeddings for a vector similarity search. The query will help retrieve additional information from a memory bank.

Question: Where can the robot get the water?
```

### Turn 1

**User**:
```
Searched knowledge: {}
```

**Assistant**:
```
<think>
Okay, the user is asking where the robot can get the water. Let me check the provided knowledge. Oh, the searched knowledge is empty, which means there's no information given here. Since there's no data about the robot's environment or available resources, I can't determine where the water is. I need to ask for more information. The previous search queries were about character IDs and names, but that's not relevant here. So I should generate a new search query related to the robot's location or water sources. Maybe something like "Where is the water source located?" or "What are the available water sources for the robot?". That should help retrieve the necessary details.
</think>

Action: [Search]
Content: Where is the water source located?
```

### Turn 2

**User**:
```
Searched knowledge: {"CLIP_0": ["The video takes place in a small, well-lit room with light-colored walls and a gray floor.", "The room contains a round table with a mosaic-style tabletop and a black base, two red chairs, a white cabinet, a wooden shelf, a floor lamp with a white conical shade, a standing fan, and several potted plants.", "A person wearing a yellow shirt and gray pants sits on a striped couch, holding a tablet.", "A black handbag rests on the round table.", "Another person, wearing a white shirt and gray pants, enters the room and walks towards the white cabinet.", "<character_0>: 'Lily, I have poured a glass of water for you. Remember to drink it.'", "<character_1>: 'Okay, thank you. I will drink it later.'", "The person in the white shirt places a glass of water on the round table and then sits down at the table.", "The person in the white shirt opens the black handbag on the table.", "<character_0> is considerate and attentive to <character_1>.", "<character_1> is polite and appreciative of <character_0>'s gesture.", "<character_0> and <character_1> likely have a close relationship, possibly familial or friendly.", "The interaction between <character_0> and <character_1> suggests a comfortable and familiar dynamic.", "The scene depicts a quiet moment of personal care and consideration within a domestic setting.", "The narrative unfolds with a simple act of service, creating a gentle interruption to the otherwise tranquil atmosphere.", "The scene's tone is relaxed and intimate, suggesting a close relationship between the individuals involved.", "The act of providing water prompts a polite acknowledgment and a future intention to consume it, indicating a shared understanding of routine or care.", "The room appears to be a combined living and dining area, possibly in a small apartment or studio.", "The room's decor suggests a preference for a minimalist or vintage aesthetic.", "The presence of a standing fan suggests the room is designed for natural ventilation or cooling.", "The placement of the potted plants suggests an effort to bring nature indoors and enhance the room's ambiance.", "The white cabinet likely serves as storage for household items or personal belongings.", "The wooden shelf appears to be used for organizing and displaying books or decorative items.", "The round table with a mosaic-style tabletop serves as a multifunctional piece for dining, casual activities, or conversations.", "The red chairs likely complement the table and contribute to the room's overall color scheme and aesthetic.", "The floor lamp with a white conical shade provides focused lighting and adds a touch of vintage charm to the room.", "The black handbag placed on the table suggests a temporary arrangement, indicating the person's presence and activity in the room.", "The provision of water by <character_0> to <character_1> reflects a common social norm of offering refreshments to guests or those in need."]}
```

**Assistant**:
```
<think>
Okay, let's see. The user is asking where the robot can get the water. From the provided knowledge, there's a description of a room with a round table, a white cabinet, and other items. The characters in the scene are placing a glass of water on the table.

First, I need to figure out if there's a specific location mentioned where water is stored or accessed. The knowledge mentions a white cabinet, which might be where the water is kept. Also, the person in the white shirt pours a glass of water, so maybe the cabinet has a water source or bottles. Alternatively, there's a floor lamp and a standing fan, but those don't relate directly to water storage.

The key points are that the water is placed on the round table, but the source might be the cabinet. Since the cabinet is white and mentioned as storage, it's possible that the water comes from there. The robot would need to check the cabinet to get the water. There's no mention of a kitchen or other areas, so within the described room, the cabinet is the most likely source.
</think>

Action: [Answer]
Content: The robot can get the water from the white cabinet in the room.
```

---

## 📈 分析总结

### 正确性分析
- **答案匹配度**: 高（模型正确识别了 white cabinet）
- **推理过程**: 合理（通过场景描述和对话推断水源位置）

### 检索效率
- **检索轮数**: 1 次
- **检索精度**: 第一次检索即获得相关信息

### 改进建议
- (可手动添加分析笔记)

```

---

## 五、使用方法

### 5.1 配置文件 (config.json)

```json
{
  "graph_paths": {
    "robot": "data/memory_graphs/robot",
    "web": "data/memory_graphs/web"
  },
  "nstf_graph_paths": {
    "robot": "data/nstf_graphs/robot",
    "web": "data/nstf_graphs/web"
  },
  "result_paths": {
    "baseline": {
      "robot": "results/baseline/robot",
      "web": "results/baseline/web"
    },
    "nstf": {
      "robot": "results/nstf/robot",
      "web": "results/nstf/web"
    },
    "nstf_level": {
      "robot": "results/nstf/robot",
      "web": "results/nstf/web"
    }
  },
  "output_path": "analysis/data",
  "skip_existing": true
}
```

### 5.2 运行命令

```bash
cd /data1/rongjiej/NSTF_MODEL

# ====== Baseline 分析 ======

# 解析指定视频列表 (默认 baseline)
python analysis/run.py --video-list analysis/video_list.json

# 解析单个视频 (默认 baseline)
python analysis/run.py --video study_07

# 只解析图谱
python analysis/run.py --video study_07 --graph-only

# 只解析问答结果
python analysis/run.py --video study_07 --qa-only

# 强制重新解析（覆盖已有）
python analysis/run.py --video study_07 --force

# ====== NSTF 分析 ======

# 解析 NSTF 方法的结果（同时输出 Baseline + NSTF 图谱分析）
python analysis/run.py --video study_09 --method nstf

# 解析 nstf_level（同 nstf，只是别名）
python analysis/run.py --video study_09 --method nstf_level

# 批量解析 NSTF
python analysis/run.py --video-list analysis/video_list.json --method nstf

# ====== 对比分析 ======

# 同一视频的两种方法对比
python analysis/run.py --video study_09 --method baseline
python analysis/run.py --video study_09 --method nstf
# 结果分别在:
#   - analysis/data/baseline/study_09/
#   - analysis/data/nstf/study_09/
```

### 5.3 输出文件说明

**Baseline 方法输出**:
```
analysis/data/baseline/{video_id}/
├── graph_analysis.md       # Baseline 图谱分析
└── qa_results/
    ├── Q01_analysis.md
    └── ...
```

**NSTF 方法输出**:
```
analysis/data/nstf/{video_id}/
├── graph_analysis.md       # Baseline 图谱分析（作为基础）
├── nstf_graph_analysis.md  # NSTF 图谱分析（Procedure 详情）⭐
└── qa_results/
    ├── Q01_analysis.md     # 包含 NSTF 检索决策和匹配 Procedure
    └── ...
```

### 5.4 视频列表文件格式 (video_list.json)

```json
{
  "videos": [
    "study_07",
    "study_09",
    "kitchen_03",
    "kitchen_14",
    "living_room_06",
    "Efk3K4epEzg"
  ]
}
```

---

## 六、实现说明

### 6.1 图谱解析器 (graph_parser.py)

主要功能：
1. 加载 pkl 文件，反序列化为 VideoGraph 对象
2. 遍历所有节点，按 Clip 分组
3. 对于每个节点：
   - 记录类型、ID
   - 提取 contents（完整文本，不截断）
   - embedding 只记录维度，不输出具体数值
4. 提取人物映射关系
5. 统计边连接情况
6. 生成 Markdown 文档

### 6.2 问答解析器 (qa_parser.py)

主要功能：
1. 扫描 results/{method}/{dataset}/{video_id}/ 目录
2. 读取每个 JSON 文件
3. 提取并格式化：
   - 问题和答案信息
   - 结果摘要
   - 检索追踪（每轮的 query 和返回内容）
   - 完整对话历史（不截断）
4. 生成 Markdown 文档

### 6.3 增量处理逻辑

```python
def should_skip(video_id, output_path, method, skip_existing):
    """判断是否跳过该视频的解析"""
    if not skip_existing:
        return False
    
    # 输出路径: output_path/{method}/{video_id}
    video_dir = os.path.join(output_path, method, video_id)
    graph_file = os.path.join(video_dir, "graph_analysis.md")
    qa_dir = os.path.join(video_dir, "qa_results")
    
    # 图谱文件存在且问答目录存在（且非空）则跳过
    if os.path.exists(graph_file) and os.path.exists(qa_dir):
        if len(os.listdir(qa_dir)) > 0:
            return True
    return False
```

---

## 七、依赖

- Python 3.9+
- 无额外包依赖（只用标准库 pickle, json, os, datetime）

---

## 八、注意事项

1. **embedding 处理**: 不输出具体数值，只显示维度（如 "3072维"）
2. **Base64 内容**: img/voice 节点的 contents 是 Base64 编码，解析时只标注类型，不输出原始字符串
3. **路径兼容**: 图谱和结果可能在 robot 或 web 子目录，解析器自动检测
4. **编码问题**: 所有文件使用 UTF-8 编码
5. **大文件处理**: 对于超长对话历史，完整保留，不做截断

---

## 九、迁移指南

**如果之前已生成的结果在旧路径 `data/{video_id}/`，需要迁移到新路径 `data/{method}/{video_id}/`**

```bash
cd /data1/rongjiej/NSTF_MODEL/analysis

# 创建 baseline 目录
mkdir -p data/baseline

# 迁移现有结果到 baseline
mv data/study_07 data/baseline/
mv data/kitchen_14 data/baseline/
mv data/living_room_06 data/baseline/

# 或者使用通配符（小心不要移动 baseline/nstf 目录本身）
# for dir in data/*/; do
#   if [[ "$dir" != "data/baseline/" && "$dir" != "data/nstf/" ]]; then
#     mv "$dir" data/baseline/
#   fi
# done
```
