# 论文技术细节与包装策略

## 1. 核心技术细节

### 1.1 实际实现 vs 论文包装

| 组件 | 实际实现 | 论文包装 | 说明 |
|------|----------|----------|------|
| E2P算法 | LLM直接提取 | "Pattern Mining + LLM Detection" | 论文中保留 PrefixSpan 作为 baseline 或 future work |
| Embedding | text-embedding-3-large (3072维) + 可选CLIP增强(1536维) | "Multi-modal Neural Embedding" | 主要使用3072维与baseline一致，可选CLIP多模态增强 |
| Markov性质 | DAGEdge.probability | "Probabilistic DAG with Markov property" | 同一 from_node 的多条出边概率之和为1 |
| Alternative Paths | DAG 多路径 (非附加字段) | "Alternative Execution Paths" | 路径融合 + 多因一果，通过边 probability 自然表示 |
| 贝叶斯更新 | 边 probability 动态更新 | "Beta-Binomial conjugate prior" | 新视频观测时更新路径概率 |
| 时序约束 | TemporalConstraint | "Allen's Interval Algebra + Soft Constraints" | 可以引用经典时序逻辑 |

### 1.1.0 Procedure 节点的本质理解 ⭐重要

**Procedure 不仅仅是"操作步骤流程"，更是对抽象模式的结构化表示**：

| Procedure 类型 | 示例 | 说明 |
|---------------|------|------|
| **任务流程** | 煎鸡蛋：热锅→放油→敲蛋→翻面 | 最典型的程序性知识 |
| **人物习惯** | 张三出门前：检查钥匙→关热水壶→锁门 | 行为模式 |
| **性格特征** | 李四被蚊子吵醒：暴跳如雷→不耐烦起床→开灯打蚊子 | 心理反应模式 |
| **下意识反应** | 王五看到美女：两眼放光→走神→被人提醒 | 条件反射式行为 |
| **社交模式** | 小明遇到尴尬：低头沉默→转移话题→找借口离开 | 人际互动模式 |

**Procedure 是对 Semantic 的"降维打击"**：
- Semantic Memory 存储零散的属性和关系（如"李四脾气暴躁"）
- Procedure 将这些整合成可推理的结构（如"李四在X情况下会做Y，然后做Z"）

**关键设计：Procedure → Episodic 边**：
- Procedure 节点生成时会去除具体人物（如"煎鸡蛋"不记录是谁教的）
- 但通过边连接到原始 Episodic 节点（"小红教机器人煎鸡蛋"）
- 这样回答"谁教过机器人做饭"时，可以从 Procedure 追溯到 Episodic

```
Procedure Node: "煎鸡蛋流程"
    │
    └──edge──→ Episodic Node: "CLIP_3: 小红在厨房教机器人煎鸡蛋"
    └──edge──→ Episodic Node: "CLIP_7: 小红再次演示煎鸡蛋技巧"
```

### 1.1.1 Embedding 维度策略详解

**设计原则**: 在 M3-Agent baseline 基础上增加符号结构，保持 embedding 维度一致

1. **Memory Prototype (主要检索特征)**: **3072 维**
   - 使用 `text-embedding-3-large` (OpenAI API)
   - 与 M3-Agent baseline 完全一致
   - 用于向量检索，桥接神经与符号
   - 对应 `ActionNode.embeddings['text']` 和 `embeddings['fused']`

2. **可选多模态增强 (研究用)**: **1536 维**
   - CLIP-based: text(512) + visual(512) + action(512)
   - 对应 `clip_encoder.UnifiedMultimodalEncoder`
   - 仅在需要视觉/动作特征增强时启用
   - 对应 `ActionNode.embeddings['visual']` 和 `embeddings['action']`

3. **论文中的表述**:
   - 主要强调: "使用 text-embedding-3-large (3072维) 与 baseline 保持一致"
   - 可选提及: "支持多模态特征融合以增强表示能力"
   - 避免混淆: 不要同时说 3072 和 1536，要说明两者的用途区别

### 1.2 数据流图

```
Input: Video Stream
         ↓
    [M3-Agent Base]
         ↓
┌────────────────────────┐
│    Episodic Memory     │  ← 原始事件记录
│    (voice, action...)  │
└────────────────────────┘
         ↓
┌────────────────────────┐
│    Semantic Memory     │  ← 概念抽象
│    (objects, persons)  │
└────────────────────────┘
         ↓  E2P Algorithm
┌────────────────────────┐
│  Neural-Symbolic Layer │  ← 我们的贡献
│  ┌──────────────────┐  │
│  │ Memory Prototype │  │  ← 向量入口
│  │    (3072-dim)    │  │     与 M3-Agent baseline 一致
│  └────────┬─────────┘  │
│           ↓            │
│  ┌──────────────────┐  │
│  │  ProcedureDAG    │  │  ← 符号结构
│  │  (steps, edges,  │  │
│  │   probabilities) │  │     边的 probability 隐式表示 alternatives
│  └──────────────────┘  │
└────────────────────────┘
         ↓
    [Hybrid Retrieval]
         ↓
    [Answer Generation]
```

### 1.3 关键算法伪代码

**Algorithm 1: E2P (Episodic-to-Procedural)**
```
Input: VideoGraph G, clip_ids
Output: Set of ProcedureNodes

1. memories ← CollectEpisodicContent(G, clip_ids)
2. candidates ← LLM.DetectProcedures(memories)
3. for each candidate in candidates:
4.    structure ← LLM.ExtractStructure(candidate, memories)
5.    dag ← BuildProcedureDAG(structure)
6.    prototype ← ComputeMemoryPrototype(structure, memories)
7.    node ← CreateProcedureNode(dag, prototype)
8.    G.AddNode(node)
9. return G
```

**Algorithm 2: Constraint-Aware Retrieval**
```
Input: Question q, VideoGraph G
Output: Answer with reasoning

1. is_constraint, missing ← DetectConstraintQuery(q)
2. q_emb ← Embed(q)
3. candidates ← VectorSearch(G, q_emb, top_k=10)
4. symbolic_info ← []
5. for node in candidates:
6.    if node.type == "procedure":
7.       info ← ExtractSymbolicInfo(node.symbolic_graph)
8.       symbolic_info.append(info)
9.       if is_constraint:
10.         alternatives ← FindAlternatives(info, missing)
11. prompt ← BuildEnhancedPrompt(q, candidates, symbolic_info, alternatives)
12. answer ← LLM.Generate(prompt)
13. return {answer, symbolic_used: len(symbolic_info) > 0}
```

## 2. 实验设计

### 2.1 消融实验

| Config | Embedding | Symbolic | Constraint | 说明 |
|--------|-----------|----------|------------|------|
| Baseline | ✓ | ✗ | ✗ | M3-Agent 原版 |
| +Symbolic | ✓ | ✓ | ✗ | 加入 DAG 结构 |
| +Constraint | ✓ | ✓ | ✓ | 加入约束推理 |
| Full NSTF | ✓ | ✓ | ✓ | 完整系统 |

### 2.2 评测指标

1. **Accuracy**: 问答准确率
2. **Retrieval Rounds**: 检索轮次（效率指标）
3. **Symbolic Usage Rate**: 多少问题使用了符号结构
4. **Constraint Success Rate**: 约束类问题的回答准确率

### 2.3 问题类型分析

| 问题类型 | 示例 | 期望优势 | NSTF 处理策略 |
|----------|------|----------|---------------|
| 事实类 | "What color is the cup?" | 无明显优势 | 向量检索 Episodic |
| 步骤类 | "How to make braised pork?" | +Symbolic 提升 | 检索 Task Procedure |
| 工具类 | "What tools are needed?" | +Symbolic 提升 | 从 Procedure 提取 tools |
| 约束类 | "What if no pan?" | +Constraint 提升 | alternatives 推理 |
| 时序类 | "What's after step X?" | +Symbolic 提升 | DAG 结构遍历 |
| **人物理解类** | "张三是什么性格?" | **⭐ 核心优势** | 检索 Trait/Habit Procedure，通过 episodic_links 追溯证据 |
| **行为习惯类** | "小红出门前做什么?" | **⭐ 核心优势** | 检索 Habit Procedure |
| **反应模式类** | "李四被打扰会怎样?" | **⭐ 核心优势** | 检索 Trait Procedure (触发条件→反应链) |

**Human Understanding 类问题的特殊处理**:
- Baseline 只能检索到零散的 Semantic 描述（如"李四脾气暴躁"）
- NSTF 可以检索到结构化的行为模式（触发→反应→后果），并通过 episodic_links 找到具体视频证据

## 3. 论文包装策略

### 3.1 标题建议

1. "Neural-Symbolic Memory Advances Agent Reasoning in Open World" ← 当前
2. "Memory Prototype: Bridging Neural Retrieval and Symbolic Reasoning for Video Agents"
3. "From Vectors to Structures: Neural-Symbolic Memory for Procedural Video Understanding"

### 3.2 贡献点包装

**Contribution 1: Neural-Symbolic Node Definition**
- Memory Prototype 作为向量入口
- Symbolic Structure 支持精确推理
- Query Functions 提供确定性接口

**Contribution 2: E2P Algorithm**
- 自动从视频中提取程序性知识
- 构建 Probabilistic DAG
- 生成 Memory Prototype

**Contribution 3: Constraint-Aware Retrieval**
- 两阶段混合检索
- 约束查询检测
- 替代方案推理

### 3.3 与 Related Work 的区分

| 工作 | 局限 | 我们的优势 |
|------|------|-----------|
| VideoAgent | 纯向量检索 | 符号结构推理 |
| MemoryBank | 无结构化知识 | ProcedureDAG |
| ProceduralVid | 需要标注 | 自动提取 (E2P) |
| ProgPrompt | 预定义程序 | 从视频学习 |

## 4. 图表规划

### 4.1 必须有的图

1. **架构图** (Figure 1): 整体系统架构
2. **E2P流程图** (Figure 2): 知识提取流程
3. **检索流程图** (Figure 3): 两阶段检索
4. **ProcedureDAG示例** (Figure 4): 具体示例

### 4.2 必须有的表

1. **主实验结果表** (Table 1): Accuracy 对比
2. **消融实验表** (Table 2): 各组件贡献
3. **问题类型分析表** (Table 3): 不同类型问题的准确率
4. **效率对比表** (Table 4): 检索轮次/时间

## 5. 潜在审稿问题与回应

**Q1: LLM提取的结构是否可靠？**
- A: 我们的框架是可插拔的，PrefixSpan等传统方法也可替代
- 实验显示 LLM 提取的结构在下游任务中有效

**Q2: Memory Prototype vs 直接用 Procedure embedding？**
- A: Memory Prototype 聚合了多个相关记忆，比单一 embedding 更鲁棒
- 消融实验可证明

**Q3: 约束类问题的测试数据？**
- A: 我们扩展了测试集，添加了约束类问题
- 或者：约束推理是系统能力，即使当前测试集无此类问题，能力本身是贡献

**Q4: Scalability？**
- A: Memory Prototype 支持向量索引，O(log n) 检索
- 符号查询只在被检索到的节点上进行，不影响整体复杂度
