# nstf_builder 模块

NSTF 图谱构建器 - 实现 E2P (Episodic-to-Procedural) 算法

## 核心功能

**从 Baseline Memory Graph 的 Episodic 节点中提取程序性知识，生成 Procedure 节点**

- **输入**: Baseline 图谱中的 Episodic 节点（原始事件记录）
- **输出**: 新创建的 Procedure 节点（含 ProcedureDAG 符号结构）

## 模块结构

```
nstf_builder/
├── __init__.py
├── builder.py        # 主构建器
├── extractor.py      # 程序结构提取
├── prompts/          # LLM Prompt 模板
│   ├── detect.txt    # 程序检测
│   └── structure.txt # 结构提取
└── config/
    └── default.json  # 默认配置
```

## 核心流程 (E2P Algorithm)

```
Episodic 节点 (输入)      →      Procedure 节点 (输出)
    │                                    ↑
    │  1. 加载 Baseline 图谱             │
    │  2. 收集 Episodic 节点内容         │
    │  3. LLM 检测程序性知识             │
    │  4. LLM 提取程序结构 (DAG)         │
    │  5. 生成 Memory Prototype          │
    │  6. 创建并保存 Procedure 节点      │
    └────────────────────────────────────┘
```

## 配置参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `max_procedures` | 5 | 每视频最多提取的 Procedure 节点数 |
| `batch_size` | 40 | Episodic 内容批处理大小 |
| `max_content_chars` | 150 | 内容截断长度 |
