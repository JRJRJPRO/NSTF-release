# NSTF_MODEL

神经符号任务流（Neural-Symbolic Task Flow）项目

## 快速开始

### 1. 构建 NSTF 图谱（首次使用）

```bash
cd /data1/rongjiej/NSTF_MODEL

# 构建 robot 数据集的 NSTF 图谱（增量模式，推荐）
python experiments/build_nstf.py --dataset robot --mode incremental --force

# 或构建单个视频
python experiments/build_nstf.py --dataset robot --videos kitchen_03 --mode incremental --force
```

### 2. 运行问答实验

```bash
# NSTF 增强检索（新设计，Procedure 级别）
python experiments/run_qa.py --dataset robot --ablation nstf_level

# Baseline 对比
python experiments/run_qa.py --dataset robot --ablation baseline

# 限制测试题数（调试用）
python experiments/run_qa.py --dataset robot --ablation nstf_level --limit 10
```

### 检索策略选项

| --ablation 参数 | 策略 | 说明 |
|----------------|------|------|
| `baseline` | clip_level | 原始 M3-Agent baseline |
| `nstf_level` | nstf_level | **推荐** Procedure 级别增强检索 + Symbolic 函数 |
| `nstf_node` | node_level | 节点级别检索 |
| `full_nstf` | clip_level | 旧版 NSTF (已过时) |

## 目录结构

```
NSTF_MODEL/
├── .env                              # 环境变量配置
├── env_setup.py                      # 统一环境设置模块
├── README.md                         # 本文档
│
├── configs/                          # 全局配置文件
├── models/                           # 本地模型
├── mmagent/                          # 核心依赖模块
│
├── data/
│   ├── annotations/                  # 问答数据集
│   │   ├── robot.json                # Robot 场景
│   │   └── web.json                  # Web 场景
│   ├── memory_graphs/                # Baseline 图谱
│   └── nstf_graphs/                  # NSTF 增强图谱 ⭐
│
├── qa_system/                        # 问答系统模块 ⭐
│   ├── README.md                     # 详细文档
│   ├── runner.py                     # 统一运行器
│   ├── core/
│   │   ├── retriever.py              # Clip 级别检索 (baseline)
│   │   ├── retriever_nstf.py         # NSTF 检索器 ⭐ (Procedure + Symbolic)
│   │   └── retriever_v2.py           # 节点级别检索
│   ├── config/                       # QAConfig + 消融配置
│   └── prompts/                      # Prompt 模板
│
├── nstf_builder/                     # NSTF 图谱构建模块
│   ├── README.md                     # 详细文档
│   ├── incremental_builder.py        # 增量构建器 ⭐ (推荐)
│   └── builder.py                    # 静态构建器
│
├── experiments/                      # 实验脚本
│   ├── run_qa.py                     # 问答入口 ⭐
│   └── build_nstf.py                 # 图谱构建入口
│
├── scripts/                          # 调试/分析工具
│   ├── debug/                        # 调试脚本
│   └── tuning/                       # 参数调优
│
├── results/                          # 实验结果
└── docs/                             # 设计文档
    ├── NSTF_GRAPH_CONSTRUCTION_V2.2.md  # 图谱构建设计
    └── NSTF_RETRIEVAL_DESIGN.md         # 检索系统设计 ⭐
```

## 架构说明

### NSTF 检索流程 (nstf_level)

```
Query → NSTFRetriever.search()
        │
        ├─ 1. 问题分类 (_classify_query)
        │     → temporal / character / procedure
        │
        ├─ 2. Procedure 匹配 (_search_procedures)
        │     → 多粒度相似度 (goal + steps)
        │
        ├─ 3. 选择 Symbolic 函数
        │     ├─ temporal  → query_step_sequence()
        │     ├─ character → aggregate_character_behaviors()
        │     └─ procedure → get_procedure_with_evidence()
        │
        ├─ 4. 追溯 Episodic 证据
        │     → 从 episodic_links 获取原始 clip 内容
        │
        └─ 5. 返回结构化记忆 + 元数据
```

### 关键配置参数 (QAConfig)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `nstf_threshold` | 0.30 | Procedure 匹配阈值 |
| `nstf_min_confidence` | 0.25 | 最低置信度（低于此 fallback） |
| `nstf_max_procedures` | 3 | 最大返回 Procedure 数 |
| `nstf_include_evidence` | True | 是否返回 episodic 证据 |

## 注意事项

- **统一配置**: API 密钥等从 `.env` 读取，不要硬编码
- **终端命令**: 在服务器终端 (comp5011_john) 中执行
- **路径规范**: 服务器路径以 `ssh://comp5011_john/data1/rongjiej/` 开头
