# Neural-Symbolic Memory System - 论文架构与内容规划 (修订版)

> **目标会议**: KDD 2025
> **论文标题**: Neural-Symbolic Memory Advances Agent Reasoning in Open World
> **页数限制**: 9页正文 + 不限页数参考文献
> **Baseline**: M3-Agent (A Multimodal Agent with Long-Term Memory)
> **实验提升**: 在 Robot 数据集上准确率提升 **6.4%**

---

## ⚠️ 写作注意事项

1. **Real World 优于 Video** - 全文使用 "real-world environments/scenarios" 而非 "video"，实操部分可偶尔提及 video
2. **先问题后方案** - 每个概念/架构提出前，必须先阐述问题和动机
3. **Neural-Symbolic Layer 为核心** - 虽然实验围绕 Procedure，但论文要讲的是 Neural-Symbolic Layer，Procedure 是其中一种实例
4. **Episodic + Semantic → Neural-Symbolic** - 要讲清楚低层记忆如何构成高层
5. **马尔科夫链包装** - 不单独章节，在边概率描述时顺带提及
6. **`<span style="color:red">`红色标记未知内容** - 不确定的数据/细节用红色标出

---

## 📌 论文整体架构

```
论文结构
├── 1. Introduction (1~1.2页)  （为什么重要，related works多加点, motivation, solution，提的太少现在的graph，定位问题，讲现在的系统，他们的问题，我的好处)
│   ├── 1.1 Real-World Agent 的挑战
│   ├── 1.2 现有记忆系统的根本局限
│   ├── 1.3 Key Insight: Neural + Symbolic    （跟上面的motivation呼应，为什么用这几个）
						（上面的客观解决方案多讲，下面的insight自然就有了，上面多一点下面少一点，使用的多个方法之间的关联，分别是用来解决什么的，文字图片要有呼应，现在太孤立了）（
│   └── 1.4 贡献总结			（到二级目录）（太多了）
│	（neural symbolic 对比图，  整个tech的图   example的图   配图要多加点icon图片）
├── 2. Preliminary (0.8~1页)
│   ├── 2.1 Memory System 框架引入 (为什么需要形式化)
│   ├── 2.2 Memory 的形式化定义 (Construction, Update, Retrieval)
│   ├── 2.3 现有方法: VideoGraph (Baseline)
│   └── 2.4 Problem Statement
│
├── 3. Method: Neural-Symbolic Memory System (2.5~3页)		（三级目录）
│   ├── 3.1 Overview (问题驱动的架构介绍)
│   ├── 3.2 Three-Layer Memory Architecture
│   │   ├── 3.2.1 Layer 1: Episodic Memory (来源)
│   │   ├── 3.2.2 Layer 2: Semantic Memory (抽象)
│   │   └── 3.2.3 Layer 3: Neural-Symbolic Layer (创新)
│   ├── 3.3 Neural-Symbolic Node Definition
│   │   ├── 3.3.1 为什么需要混合表示
│   │   ├── 3.3.2 Memory Prototype (Neural入口)
│   │   ├── 3.3.3 Symbolic Structure (确定性推理)
│   │   └── 3.3.4 Query Functions (可扩展接口)
│   ├── 3.4 Construction: E2P Algorithm	     （limitation应该放introduction多点）
│   │   └── 如何从 Episodic/Semantic 构建 Neural-Symbolic
│   └── 3.5 Retrieval: Hybrid Mechanism
│       ├── Stage 1: Neural Retrieval
│       └── Stage 2: Symbolic Enhancement
│
├── 4. Experim	ents (2~2.5页)
│   ├── 4.1 Experimental Setup
│   ├── 4.2 Main Results (对比 M3-Agent +6.4%)
│   ├── 4.3 Ablation Study
│   ├── 4.4 Analysis
│   └── 4.5 Case Study
│		（overview  4.1 prototype 画个图，  4.2construction   4.3retrieval  )
├── 5. Related Work (0.6~0.8页)
│   ├── 5.1 Memory Systems for Agents
│   ├── 5.2 Neural-Symbolic Integration
│   └── 5.3 Procedural Knowledge Learning
│
└── 6. Conclusion (0.3~0.4页)
```

---

## 📝 各章节详细内容

### 1. Introduction (约1页)

#### 1.1 Real-World Agent 的挑战 (第1段)

**要点**：

- 智能体在 **开放世界环境** 中面临的核心挑战
- 需要从连续的多模态输入中累积、管理和应用知识
- 与受控实验室环境不同，真实场景复杂多变

**写法**：

> "Intelligent agents deployed in open-world environments face a fundamental challenge: how to effectively accumulate, organize, and leverage knowledge from continuous multimodal inputs..."

**注意**: 不要说 video，说 "real-world multimodal inputs" 或 "continuous sensory streams"

#### 1.2 现有方法的根本局限 (第2段)

**先讲进步**：

- M3-Agent 等系统的贡献（VideoGraph、Episodic + Semantic Memory）
- 向量检索在语义匹配上的成功

**再讲局限（这是核心）**：

- 纯神经表示 **无法** 支持：
  1. **Constraint Satisfaction** - "没有工具X怎么办"
  2. **Path Planning** - 找最优步骤序列
  3. **Dependency Reasoning** - 理解前置条件关系

**举例说明**：

> "Consider an agent that has observed multiple cooking demonstrations. When asked 'How can I make braised pork without a wok?', pure vector retrieval can find fragments mentioning these terms, but cannot reason about which steps require a wok, what alternatives exist, or whether skipping certain steps is valid."

#### 1.3 Key Insight (第3段，核心卖点)

**一句话核心**：

> **"Effective real-world reasoning requires BOTH neural and symbolic representations working in concert—neural for efficient semantic retrieval, symbolic for precise structured reasoning."**

**展开**：

- Neural: 模糊查询、语义匹配
- Symbolic: 确定性推理、约束满足
- 两者互补，缺一不可

#### 1.4 贡献总结 (第4段)

| # | 贡献点                                        | 一句话描述                               |
| - | --------------------------------------------- | ---------------------------------------- |
| 1 | **Neural-Symbolic Memory Architecture** | 三层记忆架构，扩展现有系统               |
| 2 | **Memory Prototype**                    | 聚合向量作为符号结构的 neural 入口       |
| 3 | **E2P Algorithm**                       | 自动从低层记忆构建高层结构化知识         |
| 4 | **Symbolic Query Functions**            | 确定性、可扩展的推理接口                 |
| 5 | **Hybrid Retrieval**                    | Neural + Symbolic 两阶段检索             |
| 6 | **Empirical Validation**                | Robot 数据集上**+6.4%** 准确率提升 |

---

### 2. Preliminary (约0.8页)

#### 2.1 为什么需要形式化记忆系统

**引入文字**：

> "Before presenting our approach, we establish a formal framework for memory systems. This formalization serves two purposes: (1) it provides a unified language to describe existing methods and our extensions, and (2) it clarifies the design space and trade-offs in memory system design."

#### 2.2 Memory System 形式化定义

**Definition 1 (Memory System)**：

$$
\mathcal{M} = (\mathcal{S}, C, U, R)
$$

**逐个解释**：

- $\mathcal{S}$: State space - 记忆可能的状态集合
- $C: \mathcal{O} \rightarrow \mathcal{S}$: **Construction** - 如何从观测构建初始记忆
- $U: \mathcal{S} \times \mathcal{O} \rightarrow \mathcal{S}$: **Update** - 如何整合新信息
- $R: \mathcal{S} \times \mathcal{Q} \rightarrow \mathcal{A}$: **Retrieval** - 如何响应查询

**为什么这样定义**：

> "This framework captures the three fundamental operations any memory system must support, regardless of implementation details."

#### 2.3 现有方法: VideoGraph (Baseline)

**引入**：

> "M3-Agent introduces VideoGraph as a concrete instantiation of this framework..."

**Definition 2 (VideoGraph)**：

$$
G = (V_E, V_S, E, \phi)
$$

- $V_E$: Episodic nodes - 具体事件 (what happened, when, where)
- $V_S$: Semantic nodes - 抽象概念 (entities, attributes, relations)
- $E$: Edges - 关系连接
- $\phi: V \rightarrow \mathbb{R}^d$: Embedding function

**VideoGraph 的 C/U/R**：

- $C$: Multimodal input → LLM extraction → Graph nodes
- $U$: Add new nodes/edges, update embeddings
- $R$: Vector similarity search

**表格对比 Neural vs Symbolic**：

| Property                          | Neural (VideoGraph) | Symbolic |
| --------------------------------- | ------------------- | -------- |
| Semantic matching                 | ✓                  | ✗       |
| Fuzzy queries                     | ✓                  | ✗       |
| **Constraint satisfaction** | ✗                  | ✓       |
| **Path reasoning**          | ✗                  | ✓       |
| **Determinism**             | ✗                  | ✓       |

#### 2.4 Problem Statement

**正式问题定义**：

> Given a memory system $\mathcal{M}$ with observations $\mathcal{O}$ and a query $q$ requiring structured reasoning (constraint satisfaction, path planning, or dependency reasoning), find an answer $a$ that is both semantically relevant and logically consistent.

**Gap 总结**：

> "Existing systems excel at semantic retrieval but lack the representational power for structured reasoning—this is the gap our work addresses."

---

### 3. Method (约2.5-3页)

#### 3.1 Overview (问题驱动)

**开头（再次强调问题）**：

> "To bridge the gap between neural retrieval and symbolic reasoning, we propose the Neural-Symbolic Memory System..."

**Figure 1**: 系统架构图 (参考 drawio_sources/nstf_architecture.drawio)

- 位置: `Figures/fig_architecture.pdf`

**架构概述**：

1. 在 M3-Agent 基础上扩展
2. 添加 Neural-Symbolic Layer
3. 保持 Episodic/Semantic 不变，新增高层抽象

#### 3.2 Three-Layer Memory Architecture

**为什么需要三层**：

> "Human memory research distinguishes multiple memory systems serving different functions. We adopt a three-layer architecture that mirrors this organization..."

##### 3.2.1 Layer 1: Episodic Memory

**作用**: 记录具体事件
**内容**: 时间戳、动作描述、参与实体、多模态特征
**类比**: "What happened, when, and where"

##### 3.2.2 Layer 2: Semantic Memory

**作用**: 抽象概念知识
**内容**: 实体属性、关系、常识
**类比**: "General knowledge about the world"

##### 3.2.3 Layer 3: Neural-Symbolic Layer (Our Contribution)

**作用**: 结构化的程序性/因果知识
**关键点**:

- 不是简单添加，而是 **聚合** 低层信息
- 同时保留 neural (检索) 和 symbolic (推理) 能力

**从低层到高层的关系**：

```
Episodic nodes (具体事件) 
    ↓ 抽象
Semantic nodes (概念知识)
    ↓ 聚合 + 结构化 (E2P Algorithm)
Neural-Symbolic nodes (结构化知识 + 向量入口)
```

#### 3.3 Neural-Symbolic Node Definition

##### 3.3.1 为什么需要混合表示

**问题驱动**：

> "A key challenge is making structured knowledge discoverable through standard retrieval mechanisms. If symbolic structures are isolated from the neural retrieval pipeline, they cannot be found when relevant."

**解决方案预告**：

> "We address this by associating each symbolic structure with a Memory Prototype—an aggregated vector representation that serves as the 'entry point' for neural retrieval."

##### 3.3.2 Definition: Neural-Symbolic Node

**Definition 3**：

$$
\mathcal{N} = (id, c, \mathbf{p}, \mathcal{S}, \mathcal{F})
$$

- $id$: Unique identifier
- $c$: Natural language description (e.g., "procedure for making braised pork")
- $\mathbf{p} \in \mathbb{R}^d$: **Memory Prototype** - 聚合向量
- $\mathcal{S}$: **Symbolic Structure** - 可查询的结构
- $\mathcal{F}$: **Query Functions** - 确定性接口

##### 3.3.3 Memory Prototype (Neural 入口)

**Definition 4**：

$$
\mathbf{p} = \textsc{Aggregate}(\{\mathbf{e}_1, ..., \mathbf{e}_k\})
$$

**聚合策略**：

1. Mean pooling: $\mathbf{p} = \frac{1}{k}\sum_i \mathbf{e}_i$
2. Weighted mean: $\mathbf{p} = \sum_i w_i \mathbf{e}_i$ (权重基于 recency/importance)
3. Goal-augmented: $\mathbf{p} = \alpha \cdot \text{Embed}(c) + (1-\alpha) \cdot \text{Mean}(\mathbf{e}_i)$

**核心价值**：

> "Memory Prototypes enable Neural-Symbolic nodes to be discovered through standard vector retrieval, bridging the gap between neural and symbolic representations."

##### 3.3.4 Symbolic Structure: DAG Example

**Definition 5 (Procedural DAG)**：

$$
\mathcal{S} = (V, E, A)
$$

- $V$: Nodes (steps, including START and GOAL)
- $E$: Directed edges with transition probabilities (**Markov property**: 顺带提及)
- $A$: Attributes (action, required_tools, required_items, alternatives)

**边的概率解释** (Markov包装)：

> "Edge probabilities model the likelihood of step transitions, exhibiting Markov property where the next step depends only on the current state."

**Alternatives 表示**：

> "Different paths through the DAG represent alternative execution sequences, enabling constraint-aware path finding."

##### 3.3.5 Query Functions

**为什么需要确定性函数**：

> "Unlike LLM-based reasoning which may produce inconsistent results, query functions provide deterministic interfaces for precise reasoning."

**函数集合**：

1. `listPaths()` - 枚举所有有效路径
2. `getNode(id)` - 获取节点属性
3. `findAltPaths(C)` - 约束 C 下的替代路径
4. `checkFeasible(R)` - 资源 R 下的可行性
5. `computeCost(path)` - 路径代价
6. `recommendPath(C)` - 约束下最优路径

**Theorem 1 (Determinism)**：所有函数是确定性的

**Extensibility**：

> "The function set is designed to be extensible—new query types can be added as application needs evolve."

#### 3.4 Construction: E2P Algorithm

**Figure 2**: E2P 流程图 (参考 drawio_sources/e2p_algorithm.drawio)

- 位置: `Figures/fig_e2p.pdf`

**Algorithm 1**: E2P 伪代码

```
Input: VideoGraph G, related clip_ids
Output: Neural-Symbolic node N

1. memories ← CollectEpisodicContent(G, clip_ids)
2. detection ← LLM.DetectStructuredKnowledge(memories)
3. IF detection.is_knowledge AND confidence > τ:
4.    structure ← LLM.ExtractStructure(memories)
5.    dag ← BuildDAG(structure)  // 包含 steps, edges, alternatives
6.    prototype ← ComputePrototype(structure, memories)
7.    functions ← InstantiateQueryFunctions(dag)
8.    N ← CreateNode(dag, prototype, functions)
9.    G.AddNode(N); G.LinkToSources(N, clip_ids)
10. RETURN N
```

**Prototype 计算公式**：

$$
\mathbf{p} = \alpha \cdot \text{Embed}(goal\_description) + (1-\alpha) \cdot \frac{1}{k}\sum_{i=1}^{k} \mathbf{e}_i
$$

其中 $\alpha$ = `<span style="color:red">`[TBD: 实验确定]

#### 3.5 Retrieval: Hybrid Mechanism

**Figure 3**: Hybrid Retrieval 流程图 (参考 drawio_sources/hybrid_retrieval.drawio)

- 位置: `Figures/fig_retrieval.pdf`

**为什么两阶段**：

> "A single-stage approach cannot leverage both neural similarity and symbolic reasoning. We propose a two-stage mechanism..."

##### Stage 1: Neural Retrieval

```
q_emb ← Embed(query)
candidates ← VectorSearch(G, q_emb, top_k=10)
// candidates 包含 Episodic, Semantic, 和 Neural-Symbolic 节点
```

##### Stage 2: Symbolic Enhancement

```
IF DetectConstraintQuery(query):  // 检测约束类问题
    missing ← ExtractConstraints(query)
    FOR node in candidates:
        IF node.type == "neural-symbolic":
            dag ← node.symbolic_structure
            alternatives ← dag.findAltPaths(missing)
            structured_info ← dag.getPathDetails()
    prompt ← BuildEnhancedPrompt(query, candidates, alternatives, structured_info)
ELSE:
    prompt ← BuildStandardPrompt(query, candidates)
  
answer ← LLM.Generate(prompt)
```

**关键创新**：

> "The symbolic enhancement stage extracts structured information that pure neural retrieval cannot provide, enabling constraint-aware reasoning."

---

### 4. Experiments (约2页)

#### 4.1 Experimental Setup

**Datasets**：

- **M3-Bench-Robot**: 100 个机器人视角的真实场景 (来自 M3-Agent)
- `<span style="color:red">`[可选] COIN: 11,827 videos, 180 tasks
- `<span style="color:red">`[可选] CrossTask: 2,750 videos, 18 tasks

**Baselines**：

| Method                                        | Description                                      |
| --------------------------------------------- | ------------------------------------------------ |
| **M3-Agent**                            | VideoGraph + Episodic/Semantic Memory (Baseline) |
| RAG-only                                      | 标准检索增强生成                                 |
| `<span style="color:red">`[可选] VideoAgent | 迭代帧选择                                       |

**Metrics**：

1. **Accuracy**: 回答准确率
2. **Constraint Satisfaction Rate**: 约束类问题的正确率
3. **Retrieval Rounds**: 平均检索轮次
4. **Symbolic Usage Rate**: 使用符号结构的比例

**Implementation**：

- Embedding: text-embedding-3-large, 3072-dim (与M3-Agent baseline一致)
- LLM: `<span style="color:red">`[TBD: Qwen/GPT]
- Memory Prototype aggregation: weighted mean, α=`<span style="color:red">`[TBD]

#### 4.2 Main Results

**Table 1**: Main Results on M3-Bench-Robot

| Method         | Accuracy                                        | Constraint Sat.                              | Rounds                                      |
| -------------- | ----------------------------------------------- | -------------------------------------------- | ------------------------------------------- |
| RAG-only       | `<span style="color:red">`[TBD]%              | `<span style="color:red">`[TBD]%           | `<span style="color:red">`[TBD]           |
| M3-Agent       | `<span style="color:red">`[TBD]%              | `<span style="color:red">`[TBD]%           | `<span style="color:red">`[TBD]           |
| **Ours** | **`<span style="color:red">`[M3+6.4]%** | **`<span style="color:red">`[TBD]%** | **`<span style="color:red">`[TBD]** |

**分析要点**：

1. 整体准确率提升 **6.4%** (与 M3-Agent 论文中报告的结果对比)
2. 约束类问题显著提升
3. 检索轮次减少

#### 4.3 Ablation Study

**Table 2**: Ablation Study

| Config      | Description            | Accuracy                                     | Δ                                  |
| ----------- | ---------------------- | -------------------------------------------- | ----------------------------------- |
| Baseline    | M3-Agent (neural only) | `<span style="color:red">`[TBD]%           | -                                   |
| +Symbolic   | 加入 DAG 结构          | `<span style="color:red">`[TBD]%           | +`<span style="color:red">`[TBD]% |
| +Constraint | 加入约束推理           | `<span style="color:red">`[TBD]%           | +`<span style="color:red">`[TBD]% |
| Full (Ours) | 完整系统               | **`<span style="color:red">`[TBD]%** | +**6.4%**                     |

**按问题类型分析**：

| Question Type | Baseline                           | +Symbolic | Full  |
| ------------- | ---------------------------------- | --------- | ----- |
| Factual       | `<span style="color:red">`[TBD]% | ~same     | ~same |
| Step-based    | `<span style="color:red">`[TBD]% | ↑        | ↑    |
| Tool-based    | `<span style="color:red">`[TBD]% | ↑        | ↑    |
| Constraint    | `<span style="color:red">`[TBD]% | -         | ↑↑  |

#### 4.4 Analysis

**Memory Prototype 检索质量**：

| Strategy  | Recall@1                                     | Recall@5                                     | MRR                                         |
| --------- | -------------------------------------------- | -------------------------------------------- | ------------------------------------------- |
| Goal only | `<span style="color:red">`[TBD]%           | `<span style="color:red">`[TBD]%           | `<span style="color:red">`[TBD]           |
| Mean      | `<span style="color:red">`[TBD]%           | `<span style="color:red">`[TBD]%           | `<span style="color:red">`[TBD]           |
| Weighted  | **`<span style="color:red">`[TBD]%** | **`<span style="color:red">`[TBD]%** | **`<span style="color:red">`[TBD]** |

**Figure 4**: t-SNE 可视化 (可选)

- Memory Prototype 作为聚类中心
- 位置: `Figures/fig_tsne.pdf`

#### 4.5 Case Study

**Figure 5**: Case Study 示例

- 位置: `Figures/fig_case_study.pdf`

**示例**：

- **Question**: "没有平底锅怎么做红烧肉？"
- **M3-Agent**: 检索到相关内容，但无法识别约束和替代方案
- **Ours**:
  1. 检测到约束 (missing: 平底锅)
  2. 查找 DAG 中的替代路径
  3. 返回: "您可以用砂锅/铸铁锅代替..."

---

### 5. Related Work (约0.6页)

#### 5.1 Memory Systems for Agents

- MemGPT, MovieChat, M3-Agent
- **区分**: 我们添加 Neural-Symbolic Layer，支持结构化推理

#### 5.2 Neural-Symbolic Integration

- NeSy, DeepProbLog, Neural Theorem Provers
- **区分**: 我们 focus on memory systems for agents, not general NeSy

#### 5.3 Procedural Knowledge Learning

- ProceduralVid, ProgPrompt, ProcNets
- **区分**: 我们从观测自动学习 (E2P)，不需要预定义程序

---

### 6. Conclusion (约0.3页)

**Summary**：

- 提出 Neural-Symbolic Memory System
- Memory Prototype 桥接 neural retrieval 和 symbolic reasoning
- E2P Algorithm 自动构建结构化知识
- 在 M3-Bench-Robot 上提升 **6.4%** 准确率

**Future Work**：

- 更复杂的符号结构 (beyond DAG)
- 跨域知识迁移
- 在线学习与动态更新

---

## 🎨 图表清单

| 图号  | 内容             | DrawIO源文件                                | PDF输出位置                      | 状态                             |
| ----- | ---------------- | ------------------------------------------- | -------------------------------- | -------------------------------- |
| Fig.1 | 系统架构图       | `drawio_sources/nstf_architecture.drawio` | `Figures/fig_architecture.pdf` | ✅ 待导出                        |
| Fig.2 | E2P流程图        | `drawio_sources/e2p_algorithm.drawio`     | `Figures/fig_e2p.pdf`          | ✅ 待导出                        |
| Fig.3 | Hybrid Retrieval | `drawio_sources/hybrid_retrieval.drawio`  | `Figures/fig_retrieval.pdf`    | ✅ 待导出                        |
| Fig.4 | t-SNE可视化      | -                                           | `Figures/fig_tsne.pdf`         | `<span style="color:red">`TODO |
| Fig.5 | Case Study       | `<span style="color:red">`需新建          | `Figures/fig_case_study.pdf`   | `<span style="color:red">`TODO |

| 表号  | 内容                | 位置            |
| ----- | ------------------- | --------------- |
| Tab.1 | Main Results        | Experiments 4.2 |
| Tab.2 | Ablation Study      | Experiments 4.3 |
| Tab.3 | Prototype Retrieval | Experiments 4.4 |

---

## 📦 包装策略总结

### Story Line

```
问题: Real-world agents 需要从多模态输入中累积知识并推理
     ↓
观察: 现有 memory systems (M3-Agent) 只用 neural representation
     ↓
Gap: Neural-only 无法做 constraint reasoning, path planning
     ↓
Insight: 需要 BOTH neural AND symbolic
     ↓
方案: Neural-Symbolic Memory System
  - Memory Prototype (让符号结构可被检索)
  - E2P (自动构建)
  - Hybrid Retrieval (两阶段)
     ↓
结果: +6.4% 准确率 on Robot benchmark
```

### 关键包装点

1. **Real-World** 而非 Video
2. **Neural-Symbolic Layer** 而非只讲 Procedure
3. **问题驱动** - 每个概念前先讲为什么需要
4. **Memory Prototype 是桥梁** - 核心卖点
5. **Markov property** 顺带提及，不单独章节

### 与 M3-Agent 的关系

- **基于** M3-Agent，不是替代
- **扩展** 其记忆架构，添加第三层
- **保持** Episodic/Semantic 不变
- **提升** 6.4% 准确率

---

## 📁 文件夹结构

```
TWCS-KDD-25-/
├── main.tex
├── introduction_new.tex
├── preliminary_new.tex
├── method.tex
├── experiment_new.tex
├── related_new.tex
├── appendix_new.tex
├── ref_new.bib
└── Figures/
    ├── fig_architecture.pdf    # 系统架构图
    ├── fig_e2p.pdf             # E2P流程图
    ├── fig_retrieval.pdf       # Hybrid Retrieval
    ├── fig_tsne.pdf            # t-SNE可视化 [TODO]
    ├── fig_case_study.pdf      # Case Study [TODO]
    └── drawio_sources/         # DrawIO源文件
        ├── nstf_architecture.drawio
        ├── e2p_algorithm.drawio
        ├── hybrid_retrieval.drawio
        └── drawio_generator.py
```

---

*文档创建时间: 2026-01-23*
*修订版本: v2.0*
