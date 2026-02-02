# Efficiency 实验

**核心目标**: 测量 NSTF 相比 Baseline 需要更少的检索轮次即可找到正确答案

## 核心指标

| 指标 | 说明 |
|------|------|
| `avg_rounds` | 平均检索轮次（达到正确答案所需轮数） |
| `avg_time_sec` | 平均单题耗时（秒） |
| `accuracy` | 准确率 |

**关键假设**: NSTF 通过程序性知识结构化，能让模型更快定位相关信息，减少无效检索

## 目录结构

```
efficiency/
├── README.md                     # 本文档
├── run_experiment.sh             # 一键运行整个实验
├── data/
│   └── video_list.json           # 20 个随机 robot 视频
├── results/
│   ├── baseline_results.jsonl    # Baseline 测试结果
│   ├── nstf_results.jsonl        # NSTF 测试结果
│   └── analysis_report.json      # 对比分析报告
└── scripts/
    ├── build_nstf_graphs.sh      # 生成 NSTF 图谱
    ├── run_baseline.sh           # 运行 Baseline 测试
    ├── run_nstf.sh               # 运行 NSTF 测试
    └── analyze_rounds.py         # 轮次分析脚本
```

## 快速开始

```bash
cd /data1/rongjiej/NSTF_MODEL

# 方式1: 完整流程（生成图谱 + 测试 + 分析）
bash experiments/efficiency/run_experiment.sh

# 方式2: 分步执行
# Step 1: 生成 NSTF 图谱
bash experiments/efficiency/scripts/build_nstf_graphs.sh

# Step 2: 运行测试
bash experiments/efficiency/scripts/run_baseline.sh
bash experiments/efficiency/scripts/run_nstf.sh

# Step 3: 分析结果
python experiments/efficiency/scripts/analyze_rounds.py
```

## 实验数据

- **数据集**: robot
- **视频数量**: 20 个（按场景类型分层随机抽样）
- **视频分布**: kitchen(4), living_room(5), bedroom(2), study(5), meeting_room(2), office(1), gym(1)

## 预期结果

- NSTF 平均轮次 < Baseline 平均轮次
- NSTF 准确率 ≥ Baseline 准确率
- 单题耗时差异不大（主要取决于 LLM 响应时间）

## 轮次分析原理

分析脚本 `analyze_rounds.py` 从结果文件中提取轮次信息：
1. **num_rounds**: 直接记录在结果中的轮次数（LLM 调用次数）
2. **conversations**: 通过统计 assistant 角色的消息数来计算

轮次越少说明模型越快找到答案，NSTF 的结构化知识应该帮助减少无效检索。
- 推理开销：延迟增加 < 10%
