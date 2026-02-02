# NSTF_MODEL

神经符号任务流（Neural-Symbolic Task Flow）项目 

## 背景
原来的代码都在/data1/rongjiej/BytedanceM3Agent，这里面包含了baseline模型和新模型，我要用新模型做实验写论文，但由于原来的文件夹屎山代码太多，所以现在搬到了新文件夹这里，
关于baseline的源码在resource/m3-agent-master



## 目录结构
```
NSTF_MODEL/
├── .env                              # 环境变量配置（GPU、API密钥、路径等）
├── env_setup.py                      # 统一环境设置模块
├── README.md                         # 本文档
│
├── configs/                          # 全局配置文件
│   ├── api_config.json               # API配置
│   ├── memory_config.json            # 记忆配置
│   └── processing_config.json        # 处理配置
│
├── models/                           # 本地模型
│   ├── M3-Agent-Control/             # 问答LLM
│   ├── M3-Agent-Memorization/        # 记忆模型
│   ├── insightface/                  # 人脸识别
│   └── pretrained_eres2netv2.ckpt    # 声纹识别
│
├── mmagent/                          # 核心依赖模块（从BytedanceM3Agent复制）
│
├── data/
│   ├── annotations/                  # 问答数据集
│   │   ├── robot.json                # Robot场景问答
│   │   └── web.json                  # Web场景问答
│   ├── memory_graphs/                # Baseline图谱
│   │   ├── robot/                    # Robot场景图谱
│   │   └── web/                      # Web场景图谱
│   └── nstf_graphs/                  # NSTF增强图谱
│       ├── robot/                    # Robot场景NSTF图谱
│       └── web/                      # Web场景NSTF图谱
│
├── qa_system/                        # 问答系统模块
│   ├── README.md                     # 模块文档
│   ├── runner.py                     # 统一运行入口
│   ├── core/                         # 核心组件
│   │   ├── llm_client.py             # LLM调用客户端
│   │   ├── retriever.py              # 图谱检索器 (Clip级别)
│   │   ├── retriever_v2.py           # V2检索器 (策略模式)
│   │   ├── evaluator.py              # 结果评估器
│   │   └── strategies/               # 检索策略
│   │       ├── base.py               # 策略基类
│   │       ├── clip_strategy.py      # Clip级别策略
│   │       └── node_strategy.py      # 节点级别策略
│   ├── config/                       # 配置
│   │   └── default.json              # 默认配置
│   └── prompts/                      # 提示词模板
│       ├── system.txt                # Baseline系统提示
│       ├── system_nstf.txt           # NSTF系统提示
│       ├── instruction.txt           # 指令模板
│       └── evaluation.txt            # 评估提示
│
├── nstf_builder/                     # NSTF图谱构建模块
│   ├── README.md                     # 模块文档
│   ├── builder.py                    # 图谱构建器
│   ├── extractor.py                  # 知识抽取器
│   ├── config/                       # 配置
│   │   └── default.json              # 默认配置
│   └── prompts/                      # 提示词模板
│       ├── detect.txt                # 任务检测提示
│       └── structure.txt             # 结构化提示
│
├── experiments/                      # 实验脚本
│   ├── run_qa.py                     # 问答实验入口
│   ├── build_nstf.py                 # NSTF构建入口
│   ├── results/                      # 实验结果输出
│   ├── query_type/                   # Query Type实验
│   │   ├── README.md                 # 实验文档
│   │   ├── data/                     # 实验数据
│   │   └── results/                  # 实验结果
│   └── efficiency/                   # Efficiency实验（询问轮次对比）
│       ├── README.md                 # 实验文档
│       ├── data/                     # 实验数据（video_list.json）
│       ├── results/                  # 实验结果
│       └── scripts/                  # 分析脚本
│           ├── run_baseline.sh       # 运行Baseline测试
│           ├── run_nstf.sh           # 运行NSTF测试
│           ├── build_nstf_graphs.sh  # 构建NSTF图谱
│           ├── analyze_rounds.py     # 轮次分析脚本
│           └── quick_analyze.py      # 快速结果统计
│
├── scripts/                          # 通用脚本工具
│   ├── debug/                        # 调试工具
│   │   └── retrieval_debug.py        # 检索系统调试
│   └── tuning/                       # 参数调优工具
│       ├── node_threshold_analysis.py # 节点检索阈值分析
│       └── test_node_retriever.py    # 节点检索器测试
│
├── results/                          # 全局结果目录
│
└── docs/                             # 项目文档
    ├── RETRIEVAL_SYSTEM.md           # 检索系统原理文档
    ├── NODE_RETRIEVAL_DESIGN.md      # 节点级别检索设计 ⭐
    └── NSTF-Paper-Plan/              # 论文规划
```

## 注意事项

- **保持整洁**: 临时文件和调试脚本放在 scripts/debug/ 或 BytedanceM3Agent 中
- **README规范**: 不放命令行语句和具体代码；不写模块简介，各模块详情见其自身 README
- **终端使用**: 本项目通过 VS Code SSH FS 远程访问，终端命令需在已登录的服务器终端中运行
- **文档同步**: 所有目录结构和代码细节应与文档保持一致，发现过时或错误及时修改文档
- **AI助手**: 需要执行终端命令时，以文本形式给出命令，不要等待权限确认（人可能不在）
- **问题拆解**: 大任务遇到问题时，及时在下方"问题追踪"记录子问题，解决后打勾
- **统一配置**: 所有配置（GPU、API密钥等）统一从 `.env` 读取，不要在代码中硬编码

## 工具在混合工作空间的行为测试 (2026-02-01)

本项目同时打开本地 `D:\JRJ\DATA5011` 和服务器 `ssh://comp5011_john`，以下是各工具对路径的处理情况：

| 工具 | 状态 | 说明 |
|------|------|------|
| `create_file` | ✅ | 需显式指定 `ssh://` 前缀，否则默认本地 |
| `create_directory` | ✅ | 同上 |
| `read_file` | ✅ | 同上 |
| `replace_string_in_file` | ✅ | 同上 |
| `list_dir` | ✅ | 同上 |
| `grep_search` | ✅ | 能同时搜索本地和服务器，结果会标注来源路径 |
| `file_search` | ⚠️ | **只能搜索本地文件**，无法搜索服务器文件 |
| `semantic_search` | ❌ | **会一直卡着直到人工打断**，在混合工作空间中不可用 |
| `run_in_terminal` | ⚠️ | 服务器终端需密码，人不在时会空等 |

**使用规范**：
1. 搜索服务器文件时，**只用 `grep_search`**，不要用 `file_search` 或 `semantic_search`
2. 所有服务器路径必须以 `ssh://comp5011_john/data1/rongjiej/` 开头
3. 终端命令以文本形式给出，不要调用 `run_in_terminal` 等待执行



