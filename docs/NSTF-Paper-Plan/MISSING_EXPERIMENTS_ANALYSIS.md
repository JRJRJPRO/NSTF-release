# NSTF论文实验缺失分析与执行方案

> **分析日期**: 2026-01-31  
> **分析人**: AI Research Assistant  
> **基于**: experiment_new.tex + 论文架构规划

---

## 📊 实验完成度总览

### ✅ 已完成的实验

1. **Main Results on M3-Bench (Robot & Web)** - Section 4.2
   - Robot数据集完整结果
   - Web数据集完整结果
   - 对比M3-Agent baseline
   - 状态: ✅ **真实数据，已完成**

2. **Ablation Study** - Section 4.5
   - w/o Symbolic
   - w/o Prototype
   - Full NSTF
   - 状态: ✅ **真实数据，已完成**

### ❌ 缺失/占位符实验

根据experiment_new.tex中的`\textcolor{red}{...}`标记，以下实验是占位符：

| 实验 | 章节 | 数据状态 | 优先级 |
|------|------|----------|--------|
| **Query Type Analysis** | 4.3 | ❌ 占位符 | 🔴 **最高** |
| **Memory Prototype Comparison** | 4.4.1 | ❌ 占位符 | 🟠 高 |
| **Embedding Space Visualization** | 4.4.2 | ❌ 占位符 | 🟡 中 |
| **Efficiency Analysis** | 4.6 | ❌ 占位符 | 🟠 高 |
| **Case Study** | 4.5 | ✅ 可以基于现有数据写 | 🟢 低 |

---

## 🎯 关键缺失实验详细分析

### 实验1: Query Type Analysis ⭐⭐⭐ 最重要

#### 为什么重要？
这是论文的**核心卖点**：
- 论文架构明确提出三种问题类型：Factual、Procedural、Constrained
- Introduction 1.2节强调 "pure neural无法处理constraint satisfaction"
- 需要证明NSTF在**Constrained queries**上有显著提升（预期+14.1%）

#### 当前状态
```latex
% experiment_new.tex Line 92-94
Factual     & \textcolor{red}{71.3\%} & \textcolor{red}{72.1\%} & \textcolor{red}{+0.8\%} \\
Procedural  & \textcolor{red}{58.4\%} & \textcolor{red}{67.2\%} & \textcolor{red}{+8.8\%} \\
Constrained & \textcolor{red}{49.7\%} & \textcolor{red}{63.8\%} & \textbf{\textcolor{red}{+14.1\%}} \\
```
**全是占位符数据！**

#### 如何完成？

**方案A: 基于现有M3-Bench数据重新标注 (推荐⭐)**

1. **获取M3-Bench所有问题**
   ```bash
   cd ssh://comp5011_john/BytedanceM3Agent
   
   # 提取所有QA问题
   python -c "
   import json
   from pathlib import Path
   
   qa_files = list(Path('data').rglob('*qa*.json'))
   all_questions = []
   for f in qa_files:
       with open(f) as file:
           data = json.load(file)
           for video, info in data.items():
               for qa in info.get('qa_list', []):
                   all_questions.append({
                       'question': qa['question'],
                       'answer': qa.get('answer', ''),
                       'video': video,
                       'original_type': qa.get('type', [])
                   })
   
   with open('all_questions_for_typing.json', 'w') as f:
       json.dump(all_questions, f, indent=2, ensure_ascii=False)
   
   print(f'Total questions: {len(all_questions)}')
   "
   ```

2. **使用LLM自动分类**
   ```python
   # scripts/classify_questions.py
   
   from openai import OpenAI
   import json
   
   client = OpenAI()
   
   CLASSIFICATION_PROMPT = """
   Classify the following question into ONE category:
   
   1. Factual: Direct recall (who/what/when/where)
      Example: "What tool was used to cut vegetables?"
   
   2. Procedural: Step sequencing or process (how to/steps)
      Example: "What are the steps to make braised pork?"
   
   3. Constrained: Alternative reasoning with constraints (without/missing/no)
      Example: "How to cook rice without a rice cooker?"
   
   Question: {question}
   
   Output ONLY one word: Factual, Procedural, or Constrained
   """
   
   def classify_question(question):
       response = client.chat.completions.create(
           model="gpt-4o",
           messages=[{
               "role": "user",
               "content": CLASSIFICATION_PROMPT.format(question=question)
           }],
           temperature=0
       )
       return response.choices[0].message.content.strip()
   
   # Load questions
   with open('all_questions_for_typing.json') as f:
       questions = json.load(f)
   
   # Classify
   for q in questions:
       q['nstf_type'] = classify_question(q['question'])
   
   # Save
   with open('questions_with_types.json', 'w') as f:
       json.dump(questions, f, indent=2, ensure_ascii=False)
   
   # Statistics
   from collections import Counter
   types = Counter(q['nstf_type'] for q in questions)
   print("Question type distribution:", types)
   ```

3. **根据类型重新计算准确率**
   ```python
   # scripts/analyze_by_type.py
   
   import json
   from collections import defaultdict
   
   # Load existing results (假设你已经跑过完整实验)
   with open('results/qa_baseline.json') as f:
       baseline_results = json.load(f)
   
   with open('results/qa_full.json') as f:
       nstf_results = json.load(f)
   
   with open('questions_with_types.json') as f:
       typed_questions = {q['question']: q for q in json.load(f)}
   
   # Group by type
   type_stats = defaultdict(lambda: {'baseline_correct': 0, 'nstf_correct': 0, 'total': 0})
   
   for result in baseline_results:
       q_type = typed_questions[result['question']]['nstf_type']
       type_stats[q_type]['total'] += 1
       if result['gpt_eval']:
           type_stats[q_type]['baseline_correct'] += 1
   
   for result in nstf_results:
       q_type = typed_questions[result['question']]['nstf_type']
       if result['gpt_eval']:
           type_stats[q_type]['nstf_correct'] += 1
   
   # Calculate accuracy
   for q_type, stats in type_stats.items():
       baseline_acc = stats['baseline_correct'] / stats['total'] * 100
       nstf_acc = stats['nstf_correct'] / stats['total'] * 100
       delta = nstf_acc - baseline_acc
       
       print(f"{q_type:12} | Baseline: {baseline_acc:.1f}% | NSTF: {nstf_acc:.1f}% | Δ: {delta:+.1f}%")
   ```

**预计时间**: 2-3小时（分类 + 分析）  
**预计费用**: $5-10（GPT-4o分类成本）

---

**方案B: 人工构建精选测试集 (备选)**

如果现有数据集中constrained类问题太少，可以人工添加：

```json
// neural_symbolic_experiments/data/typed_qa_test.json
{
  "constrained_questions": [
    {
      "question": "How to organize the drawer without dividers?",
      "video": "living_room_06",
      "expected_answer": "Use small boxes or cardboard separators"
    },
    {
      "question": "How to cook rice if you don't have a rice cooker?",
      "video": "kitchen_03",
      "expected_answer": "Use a regular pot with 2:1 water ratio"
    }
    // ... 添加10-15个精心设计的constrained问题
  ],
  "procedural_questions": [...],
  "factual_questions": [...]
}
```

**优点**: 控制测试质量  
**缺点**: 样本量少，说服力不如大规模数据  
**预计时间**: 4-6小时（问题设计 + 运行 + 分析）

---

### 实验2: Memory Prototype Aggregation Strategy Comparison

#### 为什么重要？
- Memory Prototype是核心创新之一（论文贡献#2）
- 需要证明hybrid策略优于单一策略
- 体现"neural entry point to symbolic structure"的设计合理性

#### 当前状态
```latex
% experiment_new.tex Line 120-126
Goal embedding only  & \textcolor{red}{61.2\%} & ... \\
Mean pooling only    & \textcolor{red}{58.7\%} & ... \\
Hybrid (α=0.3)       & \textbf{\textcolor{red}{67.8\%}} & ... \\
```
**全是占位符！**

#### 如何完成？

**实验设置**：
```python
# scripts/test_prototype_strategies.py

strategies = {
    'goal_only': lambda goal, embeddings: embed_text(goal),
    'mean_only': lambda goal, embeddings: np.mean(embeddings, axis=0),
    'hybrid_0.3': lambda goal, embeddings: 0.3 * embed_text(goal) + 0.7 * np.mean(embeddings, axis=0),
    'hybrid_0.5': lambda goal, embeddings: 0.5 * embed_text(goal) + 0.5 * np.mean(embeddings, axis=0),
    'weighted': lambda goal, embeddings: weighted_mean(embeddings, recency_weights)
}

# 对每个ProcedureNode，生成不同策略的prototype
# 然后在所有QA任务上测试检索准确率
```

**评估指标**：
- **Recall@1**: Top-1检索命中率
- **Recall@5**: Top-5检索命中率
- **MRR**: Mean Reciprocal Rank

**实施步骤**：
1. 修改`generate_procedure_graph.py`，支持`--prototype_strategy`参数
2. 对每种策略生成一个图谱
3. 在同一QA集上测试
4. 统计检索质量

**预计时间**: 3-4小时  
**数据来源**: 现有M3-Bench QA + 已生成的procedure graphs

---

### 实验3: Efficiency Analysis (Latency Breakdown)

#### 为什么重要？
- 回应审稿人可能的质疑："符号推理会不会太慢？"
- 展示NSTF虽然增加了计算，但**减少了LLM轮数**，总体更快
- 论文明确claim: "efficiency gains come primarily from reduced LLM rounds (-34% total time)"

#### 当前状态
```latex
% experiment_new.tex Line 212-216
Retrieval (per round)    & \textcolor{red}{45ms}  & \textcolor{red}{52ms} \\
Symbolic function call   & --                     & \textcolor{red}{8ms} \\
Total (avg)              & \textcolor{red}{4.1s}  & \textcolor{red}{2.7s} \\
```
**全是占位符！**

#### 如何完成？

**实验代码**：
```python
# scripts/measure_latency.py

import time
from collections import defaultdict

class LatencyProfiler:
    def __init__(self):
        self.timings = defaultdict(list)
    
    def measure(self, component_name):
        """Context manager for timing"""
        class Timer:
            def __init__(self, profiler, name):
                self.profiler = profiler
                self.name = name
            
            def __enter__(self):
                self.start = time.time()
                return self
            
            def __exit__(self, *args):
                elapsed = (time.time() - self.start) * 1000  # ms
                self.profiler.timings[self.name].append(elapsed)
        
        return Timer(self, component_name)
    
    def report(self):
        print(f"{'Component':<30} {'Mean (ms)':<12} {'Std (ms)':<12} {'Count':<10}")
        print("-" * 70)
        for component, times in sorted(self.timings.items()):
            mean = np.mean(times)
            std = np.std(times)
            count = len(times)
            print(f"{component:<30} {mean:<12.2f} {std:<12.2f} {count:<10}")

# 在 run_qa_nstf.py 中添加计时
profiler = LatencyProfiler()

def process_question(self, question):
    with profiler.measure("total"):
        # Round 1
        with profiler.measure("retrieval_round"):
            candidates = self.retrieve(question)
        
        with profiler.measure("symbolic_function"):
            if self.use_symbolic:
                symbolic_info = self._extract_symbolic(candidates)
        
        with profiler.measure("llm_inference_round"):
            answer = self.llm_generate(question, candidates, symbolic_info)
    
    return answer

# 运行完后
profiler.report()
```

**对比基准**：
- 在**相同的QA集**上运行baseline和NSTF
- 分别记录每个组件的耗时
- 计算平均轮数和总耗时

**关键指标**：
```
Baseline (Pure Neural):
- Retrieval/round: ~45ms
- LLM inference/round: ~1200ms
- Average rounds: 3.2
- Total: 3.2 * (45 + 1200) ≈ 4000ms

NSTF:
- Retrieval/round: ~52ms (稍慢，因为要检查symbolic)
- Symbolic function: ~8ms
- LLM inference/round: ~1200ms
- Average rounds: 2.1
- Total: 2.1 * (52 + 8 + 1200) ≈ 2650ms
```

**预计时间**: 2-3小时  
**数据来源**: 跑现有实验时同步记录timing

---

### 实验4: Embedding Space Visualization (t-SNE)

#### 为什么重要？
- 直观展示Memory Prototype如何组织embedding space
- 可视化"neural entry point"的概念
- 增强论文可读性和说服力

#### 当前状态
```latex
% experiment_new.tex Line 138
\fbox{\textcolor{red}{[TBD: t-SNE visualization showing Memory Prototypes as cluster centroids]}}
```
**占位符图片！**

#### 如何完成？

**实验代码**：
```python
# scripts/visualize_embeddings.py

import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import pickle

# Load graph
with open('neural_symbolic_experiments/graphs/robot_nstf_full.pkl', 'rb') as f:
    G = pickle.load(f)

# Collect embeddings
episodic_embeddings = []
semantic_embeddings = []
procedure_prototypes = []

for node in G.nodes:
    if hasattr(node, 'type'):
        emb = node.embedding if hasattr(node, 'embedding') else None
        if emb is None:
            continue
        
        if node.type == 'episodic':
            episodic_embeddings.append(emb)
        elif node.type == 'semantic':
            semantic_embeddings.append(emb)
        elif node.type == 'procedure':
            # Memory Prototype
            if hasattr(node, 'memory_prototype'):
                procedure_prototypes.append(node.memory_prototype)

# Combine all
all_embeddings = np.vstack([
    np.array(episodic_embeddings),
    np.array(semantic_embeddings),
    np.array(procedure_prototypes)
])

labels = (['Episodic'] * len(episodic_embeddings) +
          ['Semantic'] * len(semantic_embeddings) +
          ['Procedure (Prototype)'] * len(procedure_prototypes))

# t-SNE
tsne = TSNE(n_components=2, random_state=42, perplexity=30)
embeddings_2d = tsne.fit_transform(all_embeddings)

# Plot
plt.figure(figsize=(10, 8))
colors = {'Episodic': 'lightblue', 'Semantic': 'lightgreen', 'Procedure (Prototype)': 'red'}
markers = {'Episodic': 'o', 'Semantic': 's', 'Procedure (Prototype)': '*'}

for label in set(labels):
    mask = [l == label for l in labels]
    plt.scatter(
        embeddings_2d[mask, 0],
        embeddings_2d[mask, 1],
        c=colors[label],
        marker=markers[label],
        s=100 if 'Prototype' in label else 30,
        alpha=0.7,
        label=label
    )

plt.legend()
plt.title('Embedding Space Visualization (t-SNE)')
plt.xlabel('t-SNE Dimension 1')
plt.ylabel('t-SNE Dimension 2')
plt.tight_layout()
plt.savefig('Figures/embedding_viz.pdf', dpi=300, bbox_inches='tight')
plt.show()
```

**预计时间**: 1-2小时  
**依赖**: 已生成的图谱需要保存embedding数据

---

## 🚀 执行优先级与时间规划

### Phase 1: 核心实验（必做）- 6-8小时

| 任务 | 时间 | 输出 | Deadline |
|------|------|------|----------|
| Query Type Classification | 2h | questions_with_types.json | Day 1 |
| Query Type Accuracy Analysis | 1h | Table: Accuracy by Type | Day 1 |
| Efficiency Measurement | 3h | Table: Latency Breakdown | Day 2 |

**产出**：
- ✅ 完整的Table 2: Accuracy by Query Type (真实数据)
- ✅ 完整的Table 5: Latency Breakdown (真实数据)

---

### Phase 2: 补充实验（重要）- 4-6小时

| 任务 | 时间 | 输出 | Deadline |
|------|------|------|----------|
| Prototype Strategy Comparison | 3h | Table: Retrieval Quality | Day 2-3 |
| Embedding Visualization | 2h | Figure: t-SNE plot | Day 3 |

**产出**：
- ✅ Table 4: Memory Prototype Retrieval Quality
- ✅ Figure 4: Embedding Space Visualization

---

### Phase 3: 可选增强（如有时间）- 3-4小时

| 任务 | 时间 | 输出 |
|------|------|------|
| More Baselines | 2h | VideoAgent对比 |
| Scalability Analysis | 2h | 节点数vs性能曲线 |

---

## 📋 具体执行脚本清单

### 脚本1: classify_questions.py
```python
# 见上文"方案A"
```

### 脚本2: analyze_by_type.py
```python
# 见上文"方案A"
```

### 脚本3: measure_latency.py
```python
# 见上文"Efficiency Analysis"
```

### 脚本4: test_prototype_strategies.py
```python
# 修改 generate_procedure_graph.py 添加:

def compute_memory_prototype(goal_text, related_embeddings, strategy='hybrid', alpha=0.3):
    """
    strategy: 'goal_only', 'mean_only', 'hybrid', 'weighted'
    """
    goal_emb = get_embedding(goal_text)
    
    if strategy == 'goal_only':
        return goal_emb
    elif strategy == 'mean_only':
        return np.mean(related_embeddings, axis=0)
    elif strategy == 'hybrid':
        return alpha * goal_emb + (1 - alpha) * np.mean(related_embeddings, axis=0)
    elif strategy == 'weighted':
        # 按recency加权
        weights = np.exp(-np.arange(len(related_embeddings)) * 0.1)
        weights /= weights.sum()
        return np.average(related_embeddings, axis=0, weights=weights)
```

### 脚本5: visualize_embeddings.py
```python
# 见上文"Embedding Space Visualization"
```

---

## 🎓 专家级建议

### 建议1: Query Type是核心，必须做真实数据
- 这是论文的**主要卖点**（constrained queries +14.1%）
- 占位符数据风险极高，审稿人一定会质疑
- **优先级最高**，其他可妥协，这个不能

### 建议2: Efficiency Analysis很重要
- 回应"符号推理是否低效"的质疑
- 数据收集成本低（跑实验时同步记录）
- 能展示"减少LLM轮数"的优势

### 建议3: Prototype Comparison体现设计合理性
- 证明hybrid策略不是随意选择
- 强化Memory Prototype的创新性
- 数据量不大，可以快速完成

### 建议4: Visualization是锦上添花
- 增强可读性，但不影响核心贡献
- 如果时间紧张可以先跳过
- 或者使用简化版（只画部分节点）

### 建议5: 避免过度工程化
- 不要追求完美的分类算法（LLM分类足够）
- 不要做太多baseline（2-3个足够）
- 重点在**证明核心claim**，不是炫技

### 建议6: 数据质量>数量
- 宁可在50个精选问题上做深入分析
- 也不要在500个低质量问题上跑数
- 每个实验要能讲清楚story

---

## ⚠️ 风险与应对

### 风险1: Query分类不准确
**应对**: 人工抽查10%，计算inter-annotator agreement

### 风险2: Constrained类问题太少
**应对**: 人工补充10-15个高质量问题

### 风险3: Latency测量不稳定
**应对**: 多次运行取平均，报告std

### 风险4: 时间不足
**应对**: 优先完成Query Type + Efficiency，其他用简化版

---

## 📞 下一步行动

### 立即可做（今天）：
1. ✅ 阅读本分析文档
2. 🔄 提取所有M3-Bench问题到单一文件
3. 🔄 运行LLM分类脚本

### 明天：
1. 🔄 Query Type准确率分析
2. 🔄 添加latency profiling代码
3. 🔄 重跑实验收集timing数据

### 后天：
1. 🔄 Prototype策略对比
2. 🔄 可视化embedding space
3. 🔄 更新论文tex文件

---

## 📊 预期论文完成度

完成Phase 1 + Phase 2后：

| 章节 | 完成度 | 说明 |
|------|--------|------|
| Introduction | 100% | 已完成 |
| Preliminary | 100% | 已完成 |
| Method | 100% | 已完成 |
| Experiments - Main Results | 100% | ✅ 真实数据 |
| Experiments - Ablation | 100% | ✅ 真实数据 |
| Experiments - Query Type | 100% | ✅ 待完成（高优先级） |
| Experiments - Prototype | 100% | ✅ 待完成（中优先级） |
| Experiments - Efficiency | 100% | ✅ 待完成（高优先级） |
| Experiments - Visualization | 100% | ✅ 待完成（中优先级） |
| Related Work | 100% | 已完成 |
| Conclusion | 100% | 已完成 |

**整体完成度**: 70% → 95%（完成核心实验后）

---

*文档结束*
