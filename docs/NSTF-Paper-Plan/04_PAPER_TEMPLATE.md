# 论文写作模板

## 论文元信息

**标题候选：**
1. Neural-Symbolic Memory Advances Agent Reasoning in Open World
2. Memory Prototype: Bridging Neural Retrieval and Symbolic Reasoning for Video Agents
3. From Vectors to Structures: Neural-Symbolic Memory for Procedural Video Understanding

**目标会议/期刊：** KDD 2025 / TWCS Track

**页数限制：** 9 pages + references

---

## Abstract (150-200 words)

```
[Problem & Motivation]
Understanding procedural knowledge from videos is essential for intelligent 
agents operating in the physical world. However, existing video memory systems 
rely solely on vector-based retrieval, which cannot capture the structured 
relationships inherent in procedural tasks.

[Our Approach]
We propose Neural-Symbolic Temporal Fusion (NSTF), a novel memory architecture 
that combines neural embeddings with symbolic structures. Our key innovation is 
the Memory Prototype, which serves as a vector entry point to structured 
Procedure DAGs containing steps, dependencies, and alternatives.

[Method Summary]
We introduce the E2P (Episodic-to-Procedural) algorithm that automatically 
extracts procedural knowledge from video memories, and a two-stage hybrid 
retrieval system that leverages both neural similarity and symbolic reasoning.

[Results]
Experiments on procedural video QA demonstrate that NSTF achieves XX% improvement 
over baselines. Ablation studies confirm the contribution of both symbolic 
structures and constraint-aware reasoning.

[Impact]
NSTF opens new directions for memory-augmented video understanding systems.
```

---

## 1. Introduction (1-1.5 pages)

### 1.1 Opening (动机)

```
Procedural activities - such as cooking, assembly, and repair - constitute a 
significant portion of human knowledge that intelligent agents must understand 
to assist in the physical world [cite: procedural understanding papers].

Recent advances in video understanding agents [cite: M3-Agent, VideoAgent] 
have demonstrated impressive capabilities through memory-augmented architectures. 
These systems store episodic memories (what happened) and semantic memories 
(who/what is involved) as vector embeddings, enabling efficient retrieval 
through similarity search.

However, procedural knowledge has inherent structure that pure vector 
representations fail to capture:
- Sequential dependencies: Step A must precede Step B
- Causal relationships: Failing Step A prevents Step B
- Alternative paths: Multiple valid ways to achieve a goal
- Resource constraints: What tools and ingredients are needed

[插入 Figure 1: 对比图，展示向量检索 vs 结构化检索的差异]
```

### 1.2 Key Insight

```
Our key observation is that procedural knowledge exhibits a dual nature:

(1) **Semantic similarity** to related concepts - e.g., "making braised pork" 
    is semantically similar to "cooking meat dishes"
    
(2) **Structural properties** that enable precise reasoning - e.g., the exact 
    sequence of steps, required tools, and possible variations

Neither pure neural nor pure symbolic approaches can capture both aspects. 
Vector embeddings excel at semantic similarity but lose structural information. 
Knowledge graphs preserve structure but struggle with fuzzy matching and 
generalization.
```

### 1.3 Our Approach

```
We propose Neural-Symbolic Temporal Fusion (NSTF), which integrates:

- **Memory Prototype**: A high-dimensional embedding (3072-dim, text-embedding-3-large) that serves as 
  the vector entry point to procedural knowledge
  
- **Procedure DAG**: A directed acyclic graph encoding steps, dependencies, 
  temporal constraints, and alternative paths
  
- **Query Functions**: Deterministic operations on the DAG structure

The Memory Prototype enables efficient neural retrieval (O(log n) with indexing), 
while the Procedure DAG supports precise symbolic queries.
```

### 1.4 Contributions

```
Our contributions are threefold:

1. **Neural-Symbolic Node Architecture**: We define a novel memory node that 
   combines vector prototypes with symbolic DAG structures, enabling both 
   fuzzy retrieval and precise reasoning.

2. **E2P Algorithm**: We introduce Episodic-to-Procedural conversion that 
   automatically extracts structured procedural knowledge from video memories.

3. **Constraint-Aware Retrieval**: We propose a two-stage retrieval system 
   that leverages symbolic structures for enhanced reasoning, particularly 
   for constraint satisfaction queries.

Experiments on procedural video QA demonstrate significant improvements over 
pure neural baselines, with ablation studies confirming the contribution of 
each component.
```

---

## 2. Related Work (0.5-1 page)

### 2.1 Memory-Augmented Video Understanding

```
Recent video understanding systems [M3-Agent, VideoAgent, etc.] adopt 
memory-augmented architectures that store information extracted from videos...

[讨论 episodic/semantic memory, 它们的局限性]
```

### 2.2 Procedural Video Understanding

```
Procedural video understanding has been studied from various angles...

[讨论 recipe/instruction following, 但它们大多需要标注或预定义程序]
```

### 2.3 Neural-Symbolic Integration

```
Combining neural and symbolic approaches has been explored in...

[讨论 knowledge graphs + embeddings, neuro-symbolic AI]
[指出它们在 video domain 的缺失]
```

---

## 3. Method (2-2.5 pages)

### 3.1 Preliminary: Video Memory Graph

```
Following [M3-Agent], we build upon a Video Memory Graph G = (V, E) where...

[简要描述 M3-Agent 的基础架构]
```

### 3.2 Neural-Symbolic Memory Definition

```
Definition 1 (Memory Prototype). A memory prototype π ∈ R^d is a 
high-dimensional vector that serves as the semantic entry point to 
a memory node...

Definition 2 (Procedure DAG). A procedure DAG D = (N, E, C) consists of:
- N: Set of step nodes
- E: Directed edges with transition probabilities
- C: Temporal and resource constraints

Definition 3 (ProcedureNode). A ProcedureNode P = (π, D, L, S) where:
- π: Memory prototype
- D: Procedure DAG
- L: Linked clip IDs (source evidence)
- S: Statistics (usage counts, success rates)
```

**[插入 Figure 2: ProcedureNode 结构示意图]**

### 3.3 E2P: Episodic-to-Procedural Conversion

```
Algorithm 1: E2P(G, clip_ids)
Input: VideoGraph G, clip IDs to process
Output: Set of ProcedureNodes

1. memories ← CollectEpisodicContent(G, clip_ids)
2. candidates ← DetectProcedures(memories)
3. for each candidate c in candidates:
4.    structure ← ExtractStructure(c, memories)
5.    dag ← BuildDAG(structure)
6.    prototype ← ComputePrototype(structure, memories)
7.    node ← ProcedureNode(prototype, dag, clip_ids)
8.    G.AddNode(node)
9. return G
```

**[详细解释每个步骤]**

### 3.4 Constraint-Aware Retrieval

```
Our retrieval system operates in two stages:

Stage 1: Neural Retrieval
- Encode query q into embedding e_q
- Retrieve top-k nodes by cosine similarity
- Filter to include procedure nodes

Stage 2: Symbolic Augmentation
- For each retrieved ProcedureNode:
  - Extract symbolic structure from DAG
  - If constraint query detected:
    - Find alternatives for missing resources
- Construct enhanced prompt with structural information
```

**[插入 Figure 3: 检索流程图]**

---

## 4. Experiments (2-2.5 pages)

### 4.1 Experimental Setup

```
Dataset: [描述数据集]
Baselines: [列出对比方法]
Metrics: Accuracy, Retrieval Rounds, Symbolic Usage Rate
Implementation: [简要描述]
```

### 4.2 Main Results

**[插入 Table 1: 主实验结果]**

```
Our NSTF achieves XX% accuracy, outperforming the best baseline by XX%...
```

### 4.3 Ablation Study

**[插入 Table 2: 消融实验]**

```
To understand the contribution of each component, we conduct ablation studies...

- Removing symbolic structures leads to XX% drop
- Removing constraint reasoning leads to XX% drop on constraint queries
```

### 4.4 Analysis

#### Question Type Analysis
**[插入 Table 3: 不同问题类型的准确率]**

```
We categorize questions into types and analyze performance...
- Sequential questions: NSTF shows XX% improvement
- Constraint questions: NSTF shows XX% improvement
- Factual questions: Similar performance
```

#### Qualitative Examples
```
[展示具体例子，说明符号结构如何帮助回答]
```

### 4.5 Efficiency Analysis

**[插入 Table 4 或 Figure: 效率对比]**

```
Despite additional symbolic processing, NSTF maintains efficient retrieval...
```

---

## 5. Discussion (0.5 page)

### 5.1 Limitations

```
- Reliance on LLM for structure extraction
- Limited to cooking domain evaluation
- Manual threshold selection
```

### 5.2 Future Work

```
- Extend to other procedural domains
- Integrate with more sophisticated planning algorithms
- Online learning of procedure structures
```

---

## 6. Conclusion (0.25 page)

```
We presented Neural-Symbolic Temporal Fusion (NSTF), a novel memory 
architecture that combines neural embeddings with symbolic structures 
for procedural video understanding...

[总结贡献和结果]

Our work opens new directions for memory-augmented video understanding 
systems that can reason about structured procedural knowledge.
```

---

## 核心要点检查清单

### Story Line
- [ ] 问题清晰：为什么纯向量不够？
- [ ] 方案清晰：Memory Prototype + DAG 如何解决？
- [ ] 贡献清晰：三点贡献是否独立且重要？

### 技术深度
- [ ] 定义形式化
- [ ] 算法完整
- [ ] 复杂度分析

### 实验充分
- [ ] 主实验有显著提升
- [ ] 消融实验覆盖所有组件
- [ ] 案例分析有说服力

### 写作质量
- [ ] Abstract 信息完整
- [ ] Introduction 有好的 hook
- [ ] 图表清晰专业
- [ ] Related work 定位准确
