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
    ├── retriever_v2.py   # V2 检索器 (策略模式，节点级别)
    ├── retriever_nstf.py # NSTF 检索器 ⭐ (Procedure + Symbolic 函数)
    ├── evaluator.py      # GPT 答案评估
    ├── llm_client.py     # LLM 客户端封装
    └── strategies/       # 检索策略
        ├── base.py           # 策略基类
        ├── clip_strategy.py  # Clip 级别策略
        └── node_strategy.py  # 节点级别策略
```

## 核心组件

### QARunner (runner.py)
主运行器，实现完整的多轮对话问答流程：
- 支持 5 轮迭代检索-推理
- 根据 `retrieval_strategy` 自动选择检索器
- 断点续跑、增量保存
- GPT 答案评估

### NSTFRetriever (core/retriever_nstf.py) ⭐ 推荐
**新设计的 NSTF 检索器**，基于 Procedure 级别增强：

**三种 Symbolic 函数**：
1. `get_procedure_with_evidence()`: 核心检索，返回 Procedure 结构 + episodic 证据
2. `query_step_sequence()`: 时序查询（"第一步是什么？" "X 之后做了什么？"）
3. `aggregate_character_behaviors()`: 人物行为聚合（"Bob 擅长什么？"）

**检索流程**：
```
Query → _classify_query() → 选择 Symbolic 函数
      ↓
      Procedure 匹配 (goal + steps 多粒度相似度)
      ↓
      命中 → 返回结构化知识 + episodic 证据
      未命中 → fallback 到 baseline
```

### Retriever (core/retriever.py)
原始检索器（Clip 级别），用于 baseline 对比。

### RetrieverV2 (core/retriever_v2.py)
节点级别检索器，直接检索最相关的节点。

## 配置说明

### 消融配置 (ABLATION_CONFIGS)

| --ablation 参数 | 检索策略 | 说明 |
|----------------|----------|------|
| `baseline` | clip_level | 原始 M3-Agent baseline |
| `nstf_level` | nstf_level | **推荐** Procedure 级别 + Symbolic 函数 |
| `nstf_node` | node_level | 节点级别检索 |
| `full_nstf` | clip_level | 旧版 NSTF (已过时) |

### QAConfig 主要参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `retrieval_strategy` | "clip_level" | 检索策略 |
| `nstf_threshold` | 0.30 | Procedure 匹配阈值 |
| `nstf_min_confidence` | 0.25 | 最低置信度（低于此 fallback） |
| `nstf_max_procedures` | 3 | 最大返回 Procedure 数 |
| `nstf_include_evidence` | True | 是否返回 episodic 证据 |
| `threshold_baseline` | 0.3 | Baseline 相似度阈值 |
| `total_round` | 5 | 最大对话轮数 |
| `llm_source` | "cloud" | LLM 来源 |
| `llm_model` | "gemini-2.5-flash" | 模型名称 |

## 命令行使用

通过 `experiments/run_qa.py` 运行。**所有路径基于 `NSTF_MODEL` 目录**。

### 基本用法

```bash
cd /data1/rongjiej/NSTF_MODEL

# NSTF 增强检索（推荐）
python experiments/run_qa.py --dataset robot --ablation nstf_level

# Baseline 对比
python experiments/run_qa.py --dataset robot --ablation baseline

# 限制题数（调试用）
python experiments/run_qa.py --dataset robot --ablation nstf_level --limit 10

# 强制覆盖已有结果
python experiments/run_qa.py --dataset robot --ablation nstf_level --force
```

### 参数说明

| 参数 | 说明 |
|-----|------|
| `--dataset` | 数据集: `robot` 或 `web` |
| `--ablation` | 检索策略: `baseline`, `nstf_level`, `nstf_node` |
| `--video-list` | 视频列表 JSON 文件 |
| `--videos` | 指定视频 ID，逗号分隔 |
| `--limit` | 最多测试题数 |
| `--force` | 强制覆盖已有结果 |
| `--llm-source` | LLM 来源: `cloud` 或 `local` |
| `--llm-model` | LLM 模型名称 |
