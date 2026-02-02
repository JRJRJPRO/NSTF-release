# Neural-Symbolic Memory 论文架构图

> 此文件用于论文写作时的思路梳理，**不放入论文**
> **更新日期**: 2026-01-30 (维度统一为3072, alternatives修正为DAG路径)

## 整体架构树

```
Neural-Symbolic Memory System
│
├── 1. DEFINITION (数据结构与理论基础)
│   │
│   ├── 1.1 Neural-Symbolic Node
│   │   ├── node_id: 唯一标识
│   │   ├── contents: 自然语言描述
│   │   ├── Memory Prototype (p ∈ ℝ^d): 聚合向量表示 (神经入口)
│   │   ├── Symbolic Structure (S): DAG/规则/约束 (符号结构)
│   │   └── Query Functions (F): 确定性查询接口
│   │
│   ├── 1.2 Memory Prototype (Neural 入口)
│   │   ├── 定义: 聚合低层记忆的向量表示，使符号结构可被检索发现
│   │   ├── 作用: 神经符号层的"入口"，桥接向量检索与符号推理
│   │   ├── Embedding 维度: 3072 维 (text-embedding-3-large, 与 M3-Agent baseline 一致)
│   │   │   └── 注: CLIP 多模态编码器 (512×3=1536维) 作为可选的辅助特征
│   │   └── 聚合策略:
│   │       ├── Mean pooling: p = (1/k)Σv_i
│   │       ├── Weighted mean: p = Σw_i·v_i (按 recency/importance)
│   │       ├── Goal-centric: p = Embed(goal_description)
│   │       └── Hybrid (默认): p = α·Embed(goal) + (1-α)·Mean(v_i)
│   │
│   ├── 1.3 Symbolic Structure (以 ProcedureDAG 为例)
│   │   ├── StepNode: 步骤节点
│   │   │   ├── action: 动作描述
│   │   │   ├── required_tools: 所需工具
│   │   │   ├── required_items: 所需物品
│   │   │   ├── preconditions: 前置条件
│   │   │   ├── effects: 执行效果 (状态变化)
│   │   │   └── success_rate: 成功率 (基于观测统计)
│   │   │
│   │   ├── DAGEdge: 有向边 (⭐ Alternatives 通过边结构实现)
│   │   │   ├── from_node → to_node
│   │   │   ├── probability: 转移概率 (体现 Markov 性质)
│   │   │   │   └── ⭐ 同一 from_node 的多条出边即为 alternatives
│   │   │   │       例: A→C (p=0.6), A→D (p=0.4) 表示 C 和 D 是达成同一目标的替代路径
│   │   │   ├── edge_type: sequential/parallel/conditional
│   │   │   └── ⚠️ probability 会随新视频观测动态更新
│   │   │
│   │   ├── Alternative Paths (替代路径的正确理解):
│   │   │   ├── ⭐ 核心: DAG 结构天然支持多路径，无需额外 alternative 字段
│   │   │   ├── 表示: 通过边的 probability 自然表示，不是"附加"而是"结构本身"
│   │   │   │
│   │   │   ├── 场景1 - 路径融合 (一因多果):
│   │   │   │   ├── Procedure_1: A→B→C (传统方式)
│   │   │   │   ├── Procedure_2: A→D→C (另一种方式)
│   │   │   │   ├── 融合后: A 到 C 之间自然有 B(p=0.6) 和 D(p=0.4) 两种选择
│   │   │   │   └── 示例: 制作咖啡时，手动研磨(B) 或 机器研磨(D) 都能到达下一步
│   │   │   │
│   │   │   ├── 场景2 - 多因一果 (情绪/行为原因分析):
│   │   │   │   ├── 累了一天 ──(p=0.25)──→ 小红生气
│   │   │   │   ├── 鞋子被踩 ──(p=0.65)──→ 小红生气 (因果关系强)
│   │   │   │   ├── 香蕉被吃 ──(p=0.40)──→ 小红生气
│   │   │   │   └── 优势: 比"线性+alternative"更自然地表达多因一果
│   │   │   │
│   │   │   └── 动态更新: 每次观测到新视频，更新对应边的 probability
│   │   │
│   │   ├── ⭐ Procedure 类型扩展 (不仅是操作流程):
│   │   │   ├── 任务流程: 煎鸡蛋 (热锅→放油→敲蛋→翻面)
│   │   │   ├── 人物习惯: 张三出门前 (检查钥匙→关热水壶→锁门)
│   │   │   ├── 性格特征: 李四被打扰时 (暴跳如雷→不耐烦起床→发泄)
│   │   │   ├── 下意识反应: 王五看到美女 (两眼放光→走神→被提醒)
│   │   │   └── 社交模式: 小明遇到尴尬 (低头沉默→转移话题→找借口离开)
│   │   │
│   │   ├── ⭐ Procedure → Episodic 边 (关键设计):
│   │   │   ├── 问题: Procedure 抽象化时会丢失具体人物 (如"煎鸡蛋"不记录是谁教的)
│   │   │   ├── 解决: 每个 Procedure 节点保留 episodic_links 边，连接到源 Episodic 节点
│   │   │   ├── 作用: 回答"谁教的煎鸡蛋"时，从 Procedure 追溯到 Episodic
│   │   │   └── 示例: Procedure("煎鸡蛋") ──edge──→ Episodic("CLIP_3: 小红教机器人煎鸡蛋")
│   │   │
│   │   └── TemporalConstraint: 时序约束
│   │       ├── constraint_type: before/after/within/simultaneous/overlap
│   │       ├── source_action → target_action
│   │       ├── time_value / time_range / tolerance
│   │       └── confidence: 约束置信度
│   │
│   └── 1.4 Symbolic Query Functions (确定性接口)
│       ├── listPaths(dag): 枚举所有有效路径 (返回路径列表及各路径概率)
│       ├── getNode(id): 获取节点详细属性
│       ├── findAltPaths(dag, constraints): 满足约束的替代路径
│       │   └── 例: findAltPaths(dag, exclude_tools={'coffee_grinder'})
│       │       返回不使用 coffee_grinder 的所有路径
│       ├── checkFeasible(dag, resources): 检查资源下的可行性
│       │   └── 例: checkFeasible(dag, available_tools={'kettle', 'cup'})
│       │       返回哪些路径在当前资源下可行
│       └── recommendPath(dag, constraints): 约束下最优路径推荐
│           └── 综合 probability、success_rate、资源可用性等因素
│
├── 2. CONSTRUCTION (知识构建)
│   │
│   ├── 2.1 E2P Algorithm (Episodic-to-Procedural)
│   │   ├── Phase 1: Action Sequence Extraction
│   │   │   └── 从 Episodic 节点提取时序动作序列
│   │   ├── Phase 2: Pattern Mining (可选: PrefixSpan)
│   │   │   └── 发现重复出现的动作模式
│   │   ├── Phase 3: Knowledge Detection (LLM-based)
│   │   │   └── 判断是否为可结构化的程序性知识
│   │   ├── Phase 4: Structure Extraction (LLM-based)
│   │   │   └── 提取步骤、依赖、约束，构建 DAG
│   │   └── Phase 5: Memory Prototype Generation
│   │       └── 计算聚合向量作为神经入口
│   │
│   ├── 2.2 Parameter Estimation (统计学习)
│   │   ├── 成功率估计: success_rate = successes / observations
│   │   ├── 置信度更新: 基于观测次数加权
│   │   └── 边概率: 可选地使用贝叶斯更新 (Beta 先验)
│   │       └── 注: 边概率体现 Markov 性质，但不单独成章
│   │
│   ├── 2.3 Cross-Observation Knowledge Fusion (跨观测融合)
│   │   ├── Node Alignment: 多模态相似度匹配对齐节点
│   │   ├── Edge Merging: 合并依赖边，更新转移频率
│   │   ├── Constraint Fusion: 整合时序约束
│   │   └── Conflict Resolution: 冲突时按置信度或投票解决
│   │
│   └── 2.4 Incremental Update (增量更新)
│       ├── Neural Update: Memory Prototype 指数移动平均
│       │   └── p_{t+1} = β·p_t + (1-β)·v_new
│       ├── Symbolic Update: 新增节点/边，更新统计量
│       └── 触发条件: 新观测到达时，无需全量重建
│
└── 3. RETRIEVAL (检索与推理)
    │
    ├── 3.1 Question Type Classification (问题分类)
    │   ├── Factual: where/who/when/why → 优先 voice/episodic 节点
    │   ├── Procedural: how to/steps → 优先 procedure 节点
    │   └── Constraint: without/missing → procedure + 约束推理
    │
    ├── 3.2 Three-Level Hybrid Retrieval (三层混合检索)
    │   ├── Level 1 - Semantic: 向量相似度检索 (全图)
    │   │   └── sim(Embed(query), v_node) > θ
    │   ├── Level 2 - Structural: 按问题类型优先获取特定节点
    │   │   └── factual → episodic; procedural → procedure
    │   └── Level 3 - Constraint: 仅 constraint 类问题启用
    │       └── 搜索包含相关工具/物品的 procedure 节点
    │
    ├── 3.3 Symbolic Enhancement ⭐核心创新
    │   ├── 检测约束类问题 ("没有X怎么办")
    │   ├── 提取 ProcedureDAG 符号结构
    │   ├── 调用 Query Functions 进行确定性推理
    │   ├── Alternative Solution Generation:
    │   │   ├── 功能相似性匹配: 找相同效果的替代工具
    │   │   └── 语义相似性匹配: 找描述相似的替代步骤
    │   └── 构建增强 Prompt (结构化信息 + 内容)
    │
    └── 3.4 Answer Generation
        ├── LLM 结合符号结构推理
        └── 返回: answer + reasoning_path + symbolic_used
```

## 关键创新点

| 层次 | 现有方法 | 我们的方法 | 优势 |
|------|----------|------------|------|
| Definition | 纯向量节点 | Neural-Symbolic 节点 | 同时支持检索和推理 |
| Construction | 规则提取 / 人工标注 | LLM-based E2P + 统计学习 | 自动化、可扩展、可增量更新 |
| Retrieval | 纯向量检索 | 三层混合检索 + 符号增强 | 约束推理 + 替代方案生成 |

## 与 Baseline (M3-Agent) 的本质区别

```
M3-Agent:  Question → Embedding → Vector Search → LLM Generate Answer
                                        ↓
                              只看到 "内容" 文本
                              无法处理约束类问题

NSTF:      Question → Question Classification → Hybrid Retrieval
                              ↓                        ↓
                    factual/procedural/constraint   三层检索
                              ↓                        ↓
                    对于 constraint 类:     看到 "内容" + 看到 "结构"
                              ↓
                    约束检测 → 符号推理 → 替代方案查找
                              ↓
                    增强 Prompt (结构化 + 内容) → LLM Generate Answer
```

## 论文包装要点

1. **Memory Prototype 是桥梁**: 它让符号结构可以被向量检索发现，是 Neural-Symbolic 融合的关键
2. **确定性查询函数**: 区别于 LLM 的不确定性，提供精确、可重复的推理结果
3. **约束感知推理**: 能回答"没有X怎么办"这类纯 LLM 难以准确回答的问题
4. **三层检索策略**: 语义层 + 结构层 + 约束层，按问题类型智能分流
5. **增量更新能力**: 新观测到达时无需全量重建，支持在线学习
6. **可解释性**: 输出包含 `symbolic_used`、`alternatives_found`、`reasoning_path` 等

## 论文中关于 Markov 的处理

> **原则**: 作为点缀提及，不单独成章

在描述 DAG 边的转移概率时，可以自然地提一句：
> "Edge probabilities model the likelihood of step transitions, exhibiting Markov property where the next step depends primarily on the current state."

或者在 Parameter Estimation 部分提及贝叶斯更新时顺带说明其 Markov 假设。

## 各技术在论文中的篇幅建议

| 技术组件 | 重要性 | 篇幅 | 说明 |
|---------|--------|------|------|
| Memory Prototype | ⭐⭐⭐ 核心 | 详细 | 需要定义、公式、作用说明 |
| Symbolic Structure (DAG) | ⭐⭐⭐ 核心 | 详细 | 需要结构定义、示例 |
| Query Functions | ⭐⭐⭐ 核心 | 中等 | 列出函数及其作用 |
| E2P Algorithm | ⭐⭐⭐ 核心 | 详细 | 算法流程、伪代码 |
| Hybrid Retrieval | ⭐⭐⭐ 核心 | 详细 | 三层策略、流程 |
| Question Classification | ⭐⭐ 重要 | 中等 | 分类标准、作用 |
| Alternative Generation | ⭐⭐ 重要 | 中等 | 两种匹配策略 |
| Incremental Update | ⭐⭐ 重要 | 简述 | 公式 + 一段说明 |
| Cross-Observation Fusion | ⭐ 可选 | 简述 | 一段说明即可 |
| Markov / 贝叶斯 | 点缀 | 一句话 | 顺带提及 |
