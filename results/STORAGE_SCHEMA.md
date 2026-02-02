# QA 结果存储方案

本文档定义了问答实验结果的统一存储规范，支持增量保存、断点续跑、多实验共享结果。

**Schema 版本**: 1.0  
**最后更新**: 2026-02-01

## 一、设计目标

1. **即时持久化**：每完成一个问题立即写入磁盘，中断不丢失
2. **增量友好**：自动跳过已完成的问题，支持强制重跑
3. **结构化存储**：按 method → dataset → video → question 层级组织
4. **多实验复用**：基础实验、Query Type 分析、Efficiency 分析共用同一份结果
5. **索引可重建**：详细文件是唯一数据源，索引只是加速缓存

## 二、目录结构

```
NSTF_MODEL/results/
├── STORAGE_SCHEMA.md                   # 本文档
├── rebuild_index.py                    # 索引重建脚本
│
├── baseline/                           # Baseline 方法
│   ├── index_robot.jsonl               # Robot 数据集索引（可重建）
│   ├── index_web.jsonl                 # Web 数据集索引（可重建）
│   ├── robot/                          # Robot 数据集详细结果
│   │   ├── study_07/
│   │   │   ├── study_07_Q1.json        # 单个问题完整结果
│   │   │   ├── study_07_Q2.json
│   │   │   └── ...
│   │   └── kitchen_14/
│   │       └── ...
│   └── web/                            # Web 数据集详细结果
│       ├── Efk3K4epEzg/
│       │   ├── Efk3K4epEzg_Q1.json
│       │   └── ...
│       └── ...
│
├── nstf/                               # NSTF 方法（完整版）
│   ├── index_robot.jsonl
│   ├── index_web.jsonl
│   ├── robot/
│   └── web/
│
├── ablation_prototype/                 # 消融实验 B（纯向量）
│   ├── index_robot.jsonl
│   ├── index_web.jsonl
│   ├── robot/
│   └── web/
│
└── ablation_structure/                 # 消融实验 C（有结构无推理）
    ├── index_robot.jsonl
    ├── index_web.jsonl
    ├── robot/
    └── web/
```

## 三、Method 命名规则

| 命令行参数 `--ablation` | method 名称 | 目录名 |
|------------------------|------------|--------|
| 不指定 或 `full_nstf` | `nstf` | `nstf/` |
| `baseline` | `baseline` | `baseline/` |
| `prototype` | `ablation_prototype` | `ablation_prototype/` |
| `structure` | `ablation_structure` | `ablation_structure/` |

## 四、数据 Schema

### 4.1 单个问题结果（详细版）

文件路径：`results/<method>/<dataset>/<video_id>/<question_id>.json`

```json
{
  // === 元信息 ===
  "schema_version": "1.0",
  "status": "success",
  "error_message": null,

  // === 基础标识 ===
  "id": "Efk3K4epEzg_Q1",
  "video_id": "Efk3K4epEzg",
  "dataset": "web",
  "method": "nstf",

  // === 问题信息 ===
  "question": "Which collection has the highest starting price among the five items shown in the video?",
  "answer": "Pirate Ship Float",

  // === 类型标注（两种分类体系）===
  "type_original": ["Multi-Detail Reasoning"],
  "type_query": "Factual",

  // === 结果 ===
  "response": "The Pirate Ship Float has the highest starting price.",
  "gpt_eval": true,

  // === 效率指标 ===
  "num_rounds": 3,
  "elapsed_time_sec": 45.2,

  // === 检索统计 ===
  "search_count": 2,
  "retrieval_trace": [
    {
      "round": 1,
      "query": "highest starting price collection",
      "num_results": 3,
      "clips": [
        {"clip_id": 5, "score": 0.82, "source": "episodic"},
        {"clip_id": 12, "score": 0.76, "source": "procedure"}
      ]
    },
    {
      "round": 2,
      "query": "Pirate Ship Float price",
      "num_results": 2,
      "clips": [
        {"clip_id": 8, "score": 0.91, "source": "episodic"}
      ]
    }
  ],

  // === Token 统计（预留，依赖 LLM client 支持）===
  "token_stats": {
    "total_input_tokens": null,
    "total_output_tokens": null
  },

  // === 图谱信息 ===
  "nstf_available": true,
  "nstf_path": "data/nstf_graphs/web/Efk3K4epEzg_nstf.pkl",
  "mem_path": "data/memory_graphs/web/Efk3K4epEzg.pkl",

  // === 运行环境 ===
  "timestamp": "2026-02-01T14:30:00.123",
  "llm_model": "gemini-2.5-flash",
  "gpt_model": "gpt-4o-mini",

  // === 完整对话历史（用于案例分析）===
  "conversations": [
    {"role": "system", "content": "You are an assistant..."},
    {"role": "user", "content": "Searched knowledge: {}"},
    {"role": "assistant", "content": "<think>...</think>\nAction: [Search]\nContent: highest starting price"},
    {"role": "user", "content": "Searched knowledge: {\"clip_5\": \"...\"}"},
    {"role": "assistant", "content": "Action: [Answer]\nContent: The Pirate Ship Float has the highest starting price."}
  ]
}
```

### 4.2 索引条目（简洁版）

文件路径：`results/<method>/index_<dataset>.jsonl`（每行一个 JSON）

索引是从详细文件生成的缓存，可随时通过 `rebuild_index.py` 重建。

```json
{
  "id": "Efk3K4epEzg_Q1",
  "video_id": "Efk3K4epEzg",
  "status": "success",
  "type_original": ["Multi-Detail Reasoning"],
  "type_query": "Factual",
  "gpt_eval": true,
  "num_rounds": 3,
  "elapsed_time_sec": 45.2,
  "search_count": 2,
  "timestamp": "2026-02-01T14:30:00.123"
}
```

### 4.3 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `schema_version` | string | ✓ | Schema 版本号，当前为 "1.0" |
| `status` | string | ✓ | 状态：`success` / `error` / `timeout` |
| `error_message` | string\|null | ✓ | 错误信息，成功时为 null |
| `id` | string | ✓ | 问题唯一标识，格式 `<video_id>_Q<n>` |
| `video_id` | string | ✓ | 视频 ID（显式存储，不从 id 解析） |
| `dataset` | string | ✓ | 数据集：`robot` 或 `web` |
| `method` | string | ✓ | 方法名称 |
| `question` | string | ✓ | 问题文本 |
| `answer` | string | ✓ | Ground Truth 答案 |
| `type_original` | array | ✓ | 原始类型标注（来自 annotations/*.json） |
| `type_query` | string\|null | ✓ | Query Type 标注，无标注时为 null |
| `response` | string | ✓ | 模型回答（错误时可为空字符串） |
| `gpt_eval` | boolean | ✓ | GPT 评估结果（错误时为 false） |
| `num_rounds` | int | ✓ | LLM 调用轮数（assistant 消息数） |
| `elapsed_time_sec` | float | ✓ | 总耗时（秒） |
| `search_count` | int | ✓ | 有效检索次数（见下方定义） |
| `retrieval_trace` | array | ✓ | 检索详情追踪（见下方定义） |
| `token_stats` | object | ✓ | Token 统计（预留字段） |
| `nstf_available` | boolean | ✓ | 是否有 NSTF 图谱 |
| `nstf_path` | string\|null | | NSTF 图谱路径 |
| `mem_path` | string | ✓ | Baseline 图谱路径 |
| `timestamp` | string | ✓ | 测试时间（ISO 格式，毫秒精度） |
| `llm_model` | string | ✓ | 推理 LLM 模型 |
| `gpt_model` | string | ✓ | 评估 GPT 模型 |
| `conversations` | array | ✓ | 完整对话历史 |

### 4.4 关键字段定义

#### `status` 状态值
| 值 | 说明 |
|----|------|
| `success` | 正常完成问答和评估 |
| `error` | 过程中发生错误（API 失败、解析错误等） |
| `timeout` | LLM 响应超时 |

#### `search_count` 有效检索次数

**定义**：LLM 输出 `Action: [Search]` 且 Content 非空，实际执行检索后返回非空结果的次数。

- LLM 输出 Search 但 Content 为空 → 不计入
- 执行检索但返回空结果 → 不计入
- 执行检索且有返回结果 → 计入

#### `retrieval_trace` 检索追踪

记录每轮检索的详细信息，用于分析 NSTF 的检索效果：

```json
{
  "round": 1,                    // 第几轮（从 1 开始）
  "query": "search query text",  // 检索 query
  "num_results": 3,              // 返回结果数
  "clips": [                     // 检索到的 clips
    {
      "clip_id": 5,              // clip ID
      "score": 0.82,             // 相似度得分
      "source": "episodic"       // 来源：episodic / procedure
    }
  ]
}
```

如果该轮没有执行检索（Content 为空或 action 为 Answer），则不记录。

## 五、增量保存逻辑

### 5.1 跳过机制

运行 `run_qa.py` 时：

1. 根据 `--ablation` 确定 method 名称
2. 扫描 `results/<method>/<dataset>/` 下所有已存在的 `.json` 文件
3. 从待测问题列表中移除已存在的问题 ID
4. 只处理剩余问题

### 5.2 保存流程（原子写入）

对于每个问题：

```
1. 检查 results/<method>/<dataset>/<video_id>/<question_id>.json 是否存在
   ├─ 存在 → 跳过（不写文件，不追加索引）
   └─ 不存在 → 继续

2. 执行问答测试

3. 原子写入详细结果：
   a. 写入临时文件 <question_id>.json.tmp
   b. 成功后 rename 为 <question_id>.json
   （确保崩溃时不会留下损坏的文件）

4. 追加索引条目到 results/<method>/index_<dataset>.jsonl
   （索引可重建，即使追加失败也不影响数据完整性）
```

### 5.3 索引重建

索引文件是从详细文件生成的缓存，可随时通过 `rebuild_index.py` 重建：

```bash
cd /data1/rongjiej/NSTF_MODEL

# 重建所有索引
python results/rebuild_index.py

# 重建指定 method 和 dataset 的索引
python results/rebuild_index.py --method baseline --dataset web
```

重建逻辑：扫描 `results/<method>/<dataset>/` 下所有 `.json` 文件，提取索引字段，写入 `index_<dataset>.jsonl`。

### 5.4 强制重跑

使用 `--force` 参数时：
- 跳过检查步骤，直接覆盖已存在的文件
- 覆盖后运行 `rebuild_index.py` 重建索引（或手动运行）

### 5.5 自定义输出路径

使用 `--output <path>` 参数时：
- 不使用结构化存储
- 所有结果写入指定的单个 JSONL 文件
- 不检测 `results/` 目录中的已有结果
- 断点续跑基于该 JSONL 文件本身

## 六、命令行使用

### 6.1 基本用法

```bash
cd /data1/rongjiej/NSTF_MODEL

# Baseline 测试（全量，自动增量）
python experiments/run_qa.py --dataset web --ablation baseline

# NSTF 测试（全量，自动增量）
python experiments/run_qa.py --dataset web

# 指定视频列表
python experiments/run_qa.py \
    --dataset web \
    --video-list experiments/query_type/data/video_list.json \
    --ablation baseline
```

### 6.2 带 Query Type 标注

```bash
# 合并 query type 标注（自动从文件读取 type_query 字段）
python experiments/run_qa.py \
    --dataset web \
    --query-type-file experiments/query_type/data/all_web_questions_typed.json
```

### 6.3 强制重跑

```bash
# 强制覆盖已有结果
python experiments/run_qa.py --dataset web --ablation baseline --force

# 重跑后重建索引
python results/rebuild_index.py --method baseline --dataset web
```

### 6.4 自定义输出（不使用结构化存储）

```bash
# 输出到指定文件（用于临时测试）
python experiments/run_qa.py \
    --dataset web \
    --ablation baseline \
    --output experiments/my_test/results.jsonl
```

### 6.5 限制题数（调试用）

```bash
python experiments/run_qa.py --dataset web --ablation baseline --limit 10
```

## 七、分析脚本适配

### 7.1 从索引快速分析

```python
import json
from pathlib import Path

def load_index(method: str, dataset: str) -> list:
    """加载索引文件（索引由 rebuild_index.py 保证无重复）"""
    index_file = Path(f'results/{method}/index_{dataset}.jsonl')
    items = []
    with open(index_file, 'r') as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line.strip()))
    return items

# 计算准确率
baseline = load_index('baseline', 'web')
accuracy = sum(1 for x in baseline if x['gpt_eval']) / len(baseline)

# 按问题类型分组
from collections import defaultdict
by_type = defaultdict(list)
for item in baseline:
    qtype = item.get('type_query') or 'Unknown'
    by_type[qtype].append(item)
```

### 7.2 读取详细结果（案例分析）

```python
def load_detail(method: str, dataset: str, video_id: str, question_id: str) -> dict:
    """加载单个问题的详细结果"""
    path = Path(f'results/{method}/{dataset}/{video_id}/{question_id}.json')
    with open(path, 'r') as f:
        return json.load(f)

# 查看对话历史
detail = load_detail('nstf', 'web', 'Efk3K4epEzg', 'Efk3K4epEzg_Q1')
for conv in detail['conversations']:
    print(f"[{conv['role']}] {conv['content'][:100]}...")

# 查看检索追踪
for trace in detail.get('retrieval_trace', []):
    print(f"Round {trace['round']}: query='{trace['query']}', results={trace['num_results']}")
```

### 7.3 批量加载详细结果

```python
def load_all_details(method: str, dataset: str) -> list:
    """加载某个 method+dataset 的所有详细结果"""
    base_dir = Path(f'results/{method}/{dataset}')
    results = []
    for video_dir in base_dir.iterdir():
        if video_dir.is_dir():
            for json_file in video_dir.glob('*.json'):
                with open(json_file, 'r') as f:
                    results.append(json.load(f))
    return results
```

## 八、错误处理

### 8.1 错误状态记录

当问答过程中发生错误时，仍会保存结果文件，但 `status` 字段标记为 `error` 或 `timeout`：

```json
{
  "schema_version": "1.0",
  "status": "error",
  "error_message": "API rate limit exceeded",
  "id": "Efk3K4epEzg_Q1",
  "video_id": "Efk3K4epEzg",
  "dataset": "web",
  "method": "baseline",
  "question": "...",
  "answer": "...",
  "response": "",
  "gpt_eval": false,
  "num_rounds": 2,
  "elapsed_time_sec": 30.5,
  "search_count": 1,
  "retrieval_trace": [...],
  ...
}
```

### 8.2 重试错误的问题

由于错误状态的问题也有结果文件，增量运行时会跳过。如需重试：

```bash
# 方式1: 删除错误的结果文件后重跑
rm results/baseline/web/Efk3K4epEzg/Efk3K4epEzg_Q1.json
python experiments/run_qa.py --dataset web --ablation baseline

# 方式2: 使用 --force 强制重跑所有
python experiments/run_qa.py --dataset web --ablation baseline --force
```

## 九、注意事项

1. **不要手动编辑** `results/` 目录下的文件，否则可能导致索引不一致
2. **索引可重建**：如果怀疑索引有问题，随时可以运行 `rebuild_index.py` 重建
3. **type_query 为 null**：如果问题没有 Query Type 标注，该字段为 null
4. **向后兼容**：使用 `--output` 参数时行为与之前完全一致
5. **video_id 显式存储**：分析时直接读取 `video_id` 字段，不要从 `id` 解析

## 十、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-02-01 | 初始版本 |
