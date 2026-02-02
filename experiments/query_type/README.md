# Query Type 实验

按问题类型（Factual / Procedural / Constrained）分析 NSTF 对不同类型问题的效果。

## 目录结构

```
query_type/
├── README.md                         # 本文档
├── merge_query_type.py               # Query Type 标注合并脚本
├── analyze_comprehensive.py          # 综合分析脚本
├── data/
│   ├── video_list.json               # 测试视频列表
│   └── all_web_questions_typed.json  # 带类型标注的问题（部分标注）
└── results/
    ├── nstf_new.json                 # NSTF 结果 (JSONL格式)
    └── baseline_new.json             # Baseline 结果 (JSONL格式)
```

## 数据准备

### 合并 Query Type 标注到原始 annotation

`all_web_questions_typed.json` 中有部分问题已标注 Query Type，需要合并到 `data/annotations/web.json`：

```bash
cd /data1/rongjiej/NSTF_MODEL

# 预览合并结果（不实际修改）
python experiments/query_type/merge_query_type.py --dry-run

# 执行合并（会自动备份原文件）
python experiments/query_type/merge_query_type.py

# 合并到新文件（不修改原文件）
python experiments/query_type/merge_query_type.py --output data/annotations/web_with_query_type.json
```

合并后的 annotation 格式：
```json
{
  "<video_id>": {
    "qa_list": [
      {
        "question": "...",
        "answer": "...",
        "question_id": "<video_id>_Q1",
        "type": ["Multi-Detail Reasoning"],  // 原始类型（数组）
        "type_query": "Factual",             // Query Type（字符串，无标注时为 null）
        "reasoning": "..."
      }
    ]
  }
}
```

## 数据 Schema

### video_list.json
```json
{
  "description": "...",
  "statistics": { "total_videos": 10, "total_questions": 50, ... },
  "videos": ["KuRs5aoKT4g", "XtRd7qitotM", ...]
}
```

### all_web_questions_typed.json（标注源）
```json
{
  "<video_id>": {
    "qa_list": [
      {
        "question": "...",
        "question_id": "<video_id>_Q1",
        "type": "Factual"           // Query Type（字符串格式）
      }
    ]
  }
}
```

## 问题类型定义

| 类型 | 说明 | 示例 |
|-----|------|------|
| **Factual** | 事实性问题 (who/what/where/when) | "What color is the car?" |
| **Procedural** | 程序性问题 (how to/steps) | "How to make a burger?" |
| **Constrained** | 约束/条件性问题 | "What if missing X?" / "What happened after Y?" |

## 运行实验

### 方式 1：使用结构化存储（推荐）

```bash
cd /data1/rongjiej/NSTF_MODEL

# 先合并 Query Type 标注
python experiments/query_type/merge_query_type.py

# 运行 Baseline（结果存储到 results/baseline/web/）
python experiments/run_qa.py \
    --dataset web \
    --video-list experiments/query_type/data/video_list.json \
    --ablation baseline

# 运行 NSTF（结果存储到 results/nstf/web/）
python experiments/run_qa.py \
    --dataset web \
    --video-list experiments/query_type/data/video_list.json
```

### 方式 2：使用自定义输出（旧方式）

```bash
cd /data1/rongjiej/NSTF_MODEL

# 运行 Baseline
python experiments/run_qa.py \
    --dataset web \
    --video-list experiments/query_type/data/video_list.json \
    --data-file experiments/query_type/data/all_web_questions_typed.json \
    --ablation baseline \
    --output experiments/query_type/results/baseline_new.json

# 运行 NSTF
python experiments/run_qa.py \
    --dataset web \
    --video-list experiments/query_type/data/video_list.json \
    --data-file experiments/query_type/data/all_web_questions_typed.json \
    --output experiments/query_type/results/nstf_new.json
```

## 分析结果

```bash
cd /data1/rongjiej/NSTF_MODEL/experiments/query_type
python analyze_comprehensive.py
```

## 实验目标

验证 NSTF 对 Procedural 和 Constrained 类型问题的提升效果。
