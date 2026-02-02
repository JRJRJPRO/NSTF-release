# Prompts 目录说明

本目录存放 QA 系统使用的所有 prompt 模板。

## 目录结构

```
prompts/
├── README.md           # 本文档
├── evaluation.txt      # 评估 prompt（所有模式共用）
├── baseline/           # Baseline 模式（原始 M3-Agent）
│   ├── system.txt      # System prompt
│   └── instruction.txt # 每轮对话末尾追加的指令
├── nstf/               # 完整 NSTF 模式
│   ├── system.txt      # 增强版 system prompt（含 NSTF 图谱说明）
│   └── instruction.txt # 增强版 instruction（含 NSTF 检索策略）
└── ablation/           # 消融实验（使用 baseline prompt）
    └── README.md       # 说明文档
```

## Prompt 选择逻辑

程序根据 `ablation_mode` 和 `nstf_available` 自动选择 prompt：

| 模式 | ablation_mode | nstf_available | 使用的 Prompt |
|------|---------------|----------------|---------------|
| **Baseline** | `'baseline'` | 任意 | `baseline/` |
| **消融 B (prototype)** | `'prototype'` | 任意 | `baseline/` |
| **消融 C (structure)** | `'structure'` | 任意 | `baseline/` |
| **完整 NSTF** | `None` | `True` | `nstf/` |
| **NSTF (无图谱)** | `None` | `False` | `baseline/` |

## Prompt 文件说明

### baseline/system.txt
原始 M3-Agent 的 system prompt，简洁明了：
- 告诉模型任务是判断知识是否足够回答问题
- 指示输出 `[Answer]` 或 `[Search]`

### baseline/instruction.txt
每轮对话追加的指令，来自原始 M3-Agent：
- 指定输出格式 `Action: [Answer] or [Search]`
- 说明 character ID 和 name 的映射查询方式
- 要求答案中只使用 name 而非 ID

### nstf/system.txt
NSTF 增强版 system prompt：
- 说明两种知识来源（Memory Bank + NSTF Graphs）
- 解释 DAG 结构和概率含义
- 针对不同问题类型给出检索策略

### nstf/instruction.txt
NSTF 增强版 instruction：
- 更详细的 Search/Answer 指南
- 针对 NSTF 图谱的查询策略

### evaluation.txt
GPT 评估 prompt，用于判断模型回答是否正确，所有模式共用。

## 注意事项

1. **Baseline 复现**：运行 `--ablation baseline` 时，必须使用 `baseline/` 目录的 prompt 才能复现论文结果
2. **Instruction 格式**：`instruction.txt` 以换行符开头，会在代码中追加 `"\n\n"` 后拼接
3. **消融实验**：消融 B/C 目前使用 baseline prompt，因为消融的是检索方式而非 prompt
