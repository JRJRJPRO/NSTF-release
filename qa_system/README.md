# qa_system 问答系统模块

## 模块结构

```
qa_system/
├── __init__.py           # 入口，导出 QARunner
├── runner.py             # 主运行器 (完整多轮对话逻辑)
├── prompts/              # Prompt 模板
│   ├── baseline/         # Baseline 模式 prompt
│   │   ├── system.txt
│   │   └── instruction.txt
│   ├── nstf/             # NSTF 增强 prompt
│   │   ├── system.txt
│   │   └── instruction.txt
│   └── evaluation.txt    # GPT 评估 prompt
├── config/
│   ├── __init__.py       # QAConfig + BaselineConfig + NSTFConfig
│   └── default.json      # 默认参数
└── core/
    ├── __init__.py           # 统一导出所有核心组件
    ├── cache_manager.py      # 🆕 统一缓存管理器 (单例)
    ├── query_classifier.py   # 🆕 问题分类器 (论文 4.3.1)
    ├── name_resolver.py      # 🆕 人名解析服务
    ├── symbolic_functions.py # 🆕 Symbolic 函数封装 (论文 4.3.2)
    ├── hybrid_retriever.py   # 🆕 混合检索器 ⭐ (论文 4.3 完整实现)
    ├── retriever.py          # 原始检索器 (Baseline 兼容)
    ├── retriever_v2.py       # V2 检索器 (节点级别)
    ├── retriever_nstf.py     # NSTF 检索器 (旧版，已被 HybridRetriever 取代)
    ├── evaluator.py          # GPT 答案评估
    └── llm_client.py         # LLM 客户端封装
```

## 核心组件

### HybridRetriever (core/hybrid_retriever.py) ⭐ 推荐
**论文 4.3 Hybrid Retrieval and Reasoning 的完整实现**：

**核心流程**：
```
Query → QueryClassifier (4.3.1) → 分类为 factual/procedural/constraint/character
      ↓
      Multi-Granularity Retrieval (4.3.2)
      - 论文公式: score = α·sim(goal) + (1-α)·sim(steps), α=0.3
      ↓
      Type-Aware Re-ranking
      - 根据问题类型调整 Procedure 排序
      ↓
      Symbolic Functions (4.3.3)
      - get_procedure_with_evidence()
      - query_step_sequence() (支持 DAG 多路径)
      - aggregate_character_behaviors()
      ↓
      Episodic Evidence 追溯 + NameResolver 人名解析
```

**支持的运行模式**：
| 模式 | 描述 |
|-----|------|
| `baseline` | M3-Agent 原始检索 |
| `nstf_full` | 完整 NSTF + Logic Layer |
| `ablation_prototype` | 消融：纯向量检索 |
| `ablation_structure` | 消融：有结构无推理 |

### CacheManager (core/cache_manager.py)
**全局单例缓存管理器**，解决多处重复缓存问题：
- video_graph 缓存
- nstf_graph 缓存
- Procedure embeddings 缓存
- 人名映射缓存

### QueryClassifier (core/query_classifier.py)
**问题分类器** (论文 4.3.1 Query Classification)：
- 四种类型: `factual`, `procedural`, `constraint`, `character`
- 两阶段分类: 规则预筛选 + LLM 精细分类 (可选)

### NameResolver (core/name_resolver.py)
**人名解析服务**：
- 将 `face_X`, `voice_X`, `character_X` 映射为真实名称
- 从 equivalence 节点和 semantic 节点提取名称
- 支持批量替换和缓存

### SymbolicFunctions (core/symbolic_functions.py)
**三种 Symbolic 查询函数** (论文 4.3.2)：
1. `get_procedure_with_evidence()`: 核心检索 + episodic 证据追溯
2. `query_step_sequence()`: 时序查询 (支持 DAG 多路径)
3. `aggregate_character_behaviors()`: 人物行为模式聚合

**ProcedureDAG 类**：
- 支持分支路径枚举
- 约束过滤 (用于 "without X" 类型问题)

### QARunner (runner.py)
主运行器，实现完整的多轮对话问答流程：
- 自动选择 HybridRetriever (新) 或旧版检索器
- 断点续跑、增量保存
- GPT 答案评估

## 配置说明

### 运行模式配置 (MODE_CONFIGS)

```python
from qa_system.config import get_mode_config

# 获取预定义配置
config = get_mode_config('baseline')      # M3-Agent 原始
config = get_mode_config('nstf_full')     # 完整 NSTF
config = get_mode_config('ablation_prototype')  # 消融实验
```

### QAConfig 主要参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `mode` | "baseline" | 运行模式 |
| `nstf_threshold` | 0.30 | Procedure 匹配阈值 |
| `nstf_min_confidence` | 0.25 | 最低置信度 (低于此 fallback) |
| `nstf_max_procedures` | 3 | 最大返回 Procedure 数 |
| `nstf_use_reranking` | True | 是否使用 Type-Aware Re-ranking |
| `nstf_use_dag_paths` | True | 是否使用 DAG 多路径 |
| `threshold_baseline` | 0.3 | Baseline 相似度阈值 |
| `total_round` | 5 | 最大对话轮数 |

## 命令行使用

通过 `experiments/run_qa.py` 运行。**所有路径基于 `NSTF_MODEL` 目录**。

### 基本用法

```bash
cd /data1/rongjiej/NSTF_MODEL

# 完整 NSTF 模式 (推荐)
python experiments/run_qa.py --dataset robot --mode nstf_full

# Baseline 对比
python experiments/run_qa.py --dataset robot --mode baseline

# 消融实验
python experiments/run_qa.py --dataset robot --mode ablation_prototype

# 限制题数 (调试用)
python experiments/run_qa.py --dataset robot --mode nstf_full --limit 10
```

### 兼容旧版命令

```bash
# 使用旧的 --ablation 参数 (向后兼容)
python experiments/run_qa.py --dataset robot --ablation baseline
python experiments/run_qa.py --dataset robot --ablation nstf_level
```

## API 使用

```python
from qa_system.config import QAConfig, get_mode_config
from qa_system.runner import QARunner
from qa_system.core import HybridRetriever, create_retriever

# 方式 1: 使用预定义配置
config = get_mode_config('nstf_full')
runner = QARunner(config=config)

# 方式 2: 自定义配置
config = QAConfig(
    mode='nstf_full',
    nstf_threshold=0.25,
    nstf_use_reranking=True,
)
runner = QARunner(config=config)

# 方式 3: 直接使用 HybridRetriever
retriever = create_retriever(
    mode='nstf_full',
    threshold=0.30,
    use_reranking=True,
)
result = retriever.search(
    mem_path='path/to/memory.pkl',
    query='How to prepare for a birthday party?',
    nstf_path='path/to/nstf.pkl',
)
print(result.memories)
print(result.metadata)
```

## 版本历史

- **v2.0** (2026-02-04): 完整实现论文 4.3，新增 HybridRetriever、CacheManager、QueryClassifier、NameResolver
- **v1.0**: 初始版本，支持 baseline 和基础 NSTF 检索
