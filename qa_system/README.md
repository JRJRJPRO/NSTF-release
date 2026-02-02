# qa_system 问答系统模块

## 模块结构

```
qa_system/
├── __init__.py           # 入口，导出 QARunner
├── runner.py             # 主运行器 (完整多轮对话逻辑)
├── prompts/              # Prompt 模板
│   ├── system.txt        # Baseline system prompt
│   ├── system_nstf.txt   # NSTF 增强 prompt
│   ├── instruction.txt   # 动作指令模板
│   └── evaluation.txt    # GPT 评估 prompt
├── config/
│   ├── __init__.py       # QAConfig 类 + 消融配置
│   └── default.json      # 默认参数
└── core/
    ├── retriever.py      # 原始检索器 (Clip 级别，Baseline 用)
    ├── retriever_v2.py   # V2 检索器 (策略模式，支持节点级别)
    ├── evaluator.py      # GPT 答案评估
    ├── llm_client.py     # LLM 客户端封装
    └── strategies/       # 检索策略
        ├── base.py           # 策略基类
        ├── clip_strategy.py  # Clip 级别策略 (baseline)
        └── node_strategy.py  # 节点级别策略 (NSTF 增强)
```

## 核心组件

### QARunner (runner.py)
主运行器，实现完整的多轮对话问答流程：
- 支持 5 轮迭代检索-推理
- 自动选择 NSTF/Baseline 模式
- 断点续跑、增量保存
- GPT 答案评估

### Retriever (core/retriever.py)
原始检索器（Clip 级别），支持：
- `baseline`: 原始 M3-Agent 向量检索 (threshold=0.3)
- `full_nstf`: 完整 NSTF 增强检索 (threshold=0.05)
- `prototype`: 消融 B - 纯向量
- `structure`: 消融 C - 有结构无推理

### RetrieverV2 (core/retriever_v2.py)
V2 检索器，使用策略模式支持：
- `clip_level`: Clip 级别检索（与 baseline 兼容）
- `node_level`: 节点级别检索（更精准，跨 clip 获取相关节点）

**节点级别检索特点**：
- 直接检索最相关的节点，而不是返回整个 clip 的所有内容
- 更精准，减少噪声
- 支持跨 clip 聚合信息

### Evaluator (core/evaluator.py)
答案评估器：
- 调用 GPT 判断语义正确性
- 带重试机制
- 无 API 时降级为字符串匹配

### LLMClient (core/llm_client.py)
LLM 统一接口：
- `cloud`: OpenAI 兼容 API (Gemini, GPT 等)
- `local`: vLLM 本地推理

## 配置说明

### QAConfig 主要参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `topk` | 2 | Clip 级别检索 Top-K |
| `threshold` | 0.05 | NSTF 相似度阈值 |
| `threshold_baseline` | 0.3 | Baseline 相似度阈值 |
| `total_round` | 5 | 最大对话轮数 |
| `ablation_mode` | None | 消融模式 |
| `retrieval_strategy` | "clip_level" | 检索策略 (clip_level/node_level) |
| `node_topk` | 15 | 节点级别检索 Top-K |
| `node_threshold` | 0.25 | 节点级别检索阈值 |
| `llm_source` | "cloud" | LLM 来源 |
| `llm_model` | "gemini-2.5-flash" | 模型名称 |
| `gpt_model` | "gpt-4o-mini" | 评估模型 |

### 消融模式

| 模式 | 检索策略 | 说明 |
|-----|---------|------|
| `None` / `full_nstf` | clip_level | 完整 NSTF |
| `baseline` | clip_level | 消融 A: 纯 Baseline |
| `prototype` | clip_level | 消融 B: 纯向量检索 |
| `structure` | clip_level | 消融 C: 有结构无推理 |
| `nstf_node` | node_level | 节点级别检索 (NSTF 增强) |

## Prompt 模板

位于 `prompts/` 目录，可直接编辑调整模型行为：

- `system.txt`: Baseline 模式的 system prompt
- `system_nstf.txt`: NSTF 模式的 system prompt（提示使用程序知识）
- `instruction.txt`: 动作格式指令 (Action: [Answer]/[Search])
- `evaluation.txt`: GPT 评估用 prompt

## 命令行使用

通过 `experiments/run_qa.py` 运行问答测试。**所有路径都基于 `NSTF_MODEL` 目录**。

### 存储模式

支持两种存储模式：

1. **结构化存储（默认）**：按 `results/STORAGE_SCHEMA.md` 规范存储
   - 路径: `results/<method>/<dataset>/<video_id>/<question_id>.json`
   - 自动增量：跳过已存在的结果
   - 支持 `--force` 强制覆盖

2. **自定义输出（--output）**：旧的 JSONL 模式
   - 用于临时测试
   - 支持断点续跑

### 基本用法

```bash
cd /data1/rongjiej/NSTF_MODEL

# Baseline 测试（结构化存储，自动增量）
python experiments/run_qa.py --dataset web --ablation baseline

# NSTF 测试
python experiments/run_qa.py --dataset web

# 指定视频列表
python experiments/run_qa.py \
  --dataset web \
  --video-list experiments/query_type/data/video_list.json \
  --ablation baseline

# 带 Query Type 标注
python experiments/run_qa.py \
  --dataset web \
  --query-type-file experiments/query_type/data/all_web_questions_typed.json

# 强制覆盖已有结果
python experiments/run_qa.py --dataset web --ablation baseline --force

# 自定义输出（旧模式）
python experiments/run_qa.py \
  --dataset web \
  --ablation baseline \
  --output experiments/my_test/results.jsonl

# 限制题数 (调试用)
python experiments/run_qa.py --dataset robot --ablation baseline --limit 10
```

### 参数说明

| 参数 | 说明 |
|-----|------|
| `--dataset` | 数据集类型: `robot` 或 `web` |
| `--video-list` | 视频列表 JSON 文件路径 |
| `--videos` | 直接指定视频 ID，逗号分隔 |
| `--ablation` | 消融模式: `baseline`, `prototype`, `structure`, `full_nstf` |
| `--query-type-file` | Query Type 标注文件路径（合并 `type_query` 字段） |
| `--output` | 自定义输出文件路径（指定则使用旧的 JSONL 模式） |
| `--force` | 强制覆盖已有结果（仅结构化存储模式） |
| `--limit` | 最多测试题数 |
| `--llm-source` | LLM 来源: `cloud` 或 `local` |
| `--llm-model` | LLM 模型名称 |
| `--no-resume` | 不从断点续跑（仅 --output 模式） |

### 视频列表格式

```json
{
  "description": "实验说明",
  "total_videos": 20,
  "videos": ["study_07", "kitchen_14", "living_room_19", ...]
}
```
