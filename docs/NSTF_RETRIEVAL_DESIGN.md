# NSTF Retrieval 系统设计文档

> **文档状态**: 最终版  
> **创建日期**: 2026-02-02  
> **核心思想**: 从"假想的约束推理"转向"episodic_links证据追溯 + 三种Symbolic查询函数"

---

## 目录
1. [问题诊断](#1-问题诊断)
2. [设计方案](#2-设计方案)
3. [三种Symbolic函数](#3-三种symbolic函数)
4. [实现细节](#4-实现细节)
5. [与Baseline的对比](#5-与baseline的对比)

---

## 1. 问题诊断

### 1.1 原设计的问题

原设计构想了6个复杂的Query Functions：

| 函数 | 设计目的 | 实际问题 |
|------|----------|----------|
| `listPaths(dag)` | 枚举DAG所有路径 | ⚠️ 输出复杂，LLM难以利用 |
| `getNode(dag, id)` | 获取节点属性 | ⚠️ 太底层，不应暴露给检索层 |
| `findAltPaths(dag, constraints)` | 约束下替代路径 | ❌ 需要 required_tools/items 字段，数据中不存在 |
| `checkFeasible(dag, resources)` | 资源可行性 | ❌ 同上 |
| `recommendPath(dag, constraints)` | 最优路径推荐 | ❌ 同上 |
| `find_alternatives()` | 缺失资源替代 | ❌ 数据集中约束类问题极少（<2%） |

### 1.2 M3-Agent数据集问题类型分析

| 问题类型 | 频率 | 示例 | Procedure价值 |
|----------|------|------|--------------|
| 事实查询 | 40% | "What color is the cup?" | 低 - Episodic足够 |
| 人物身份 | 15% | "Who is character_0?" | 低 - Semantic足够 |
| **人物理解** | 15% | "Is Bob familiar with cooking?" | **高** - 行为模式聚合 |
| **时序查询** | 10% | "What did X do after Y?" | **高** - DAG结构查询 |
| **步骤查询** | 10% | "How many steps?" | **高** - steps字段 |
| 工具/物品 | 5% | "What tools were used?" | 中 - 从steps提取 |
| 约束推理 | <2% | "What if no pan?" | 低 - 数据极少 |

**结论**: 应聚焦于**人物理解、时序查询、步骤查询**三类高价值问题。

---

## 2. 设计方案

### 2.1 核心理念

```
旧设计: Query → 向量检索Procedure → 复杂符号函数推理 → 返回推理结果
新设计: Query → 向量检索Procedure → 三种Symbolic函数 → 返回结构+证据
```

### 2.2 三层检索架构

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: Evidence Retrieval (通过 episodic_links 追溯原始证据)   │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Symbolic Query (三种函数：时序/步骤/人物聚合)            │
├─────────────────────────────────────────────────────────────────┤
│ Layer 1: Neural Retrieval (多粒度向量检索：goal + steps)         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 检索流程

```python
def search(query, nstf_graph, video_graph):
    # 1. 多粒度向量检索 Procedure
    matched_procs = neural_search(query, nstf_graph)
    
    if not matched_procs or max_similarity < threshold:
        return fallback_to_baseline()
    
    # 2. 根据问题类型选择 Symbolic 函数
    query_type = classify_query(query)
    
    if query_type == 'temporal':
        result = query_step_sequence(matched_procs[0], query)
    elif query_type == 'character':
        result = aggregate_character_behaviors(query, nstf_graph)
    else:
        result = get_procedure_with_evidence(matched_procs, video_graph)
    
    return result
```

---

## 3. 三种Symbolic函数

### 3.1 函数1: `get_procedure_with_evidence()`

**用途**: 检索Procedure结构 + 追溯episodic证据（核心函数）

**输入**:
- `matched_procs`: 匹配到的Procedure列表
- `nstf_graph`: NSTF图谱
- `video_graph`: 视频图谱

**输出**:
```python
{
    'NSTF_Procedures': """
        --- Procedure 1 (Relevance: 0.45, matched by goal) ---
        Goal: Preparing for a birthday party
        Step 1: Arrange childcare
        Step 2: Tidy the party area
        Step 3: Prepare food and drinks
    """,
    'clip_26': "character_0 enters carrying groceries...",
    'clip_27': "character_0 places bag on counter...",
}
```

**实现要点**:
- 通过 `episodic_links` 追溯原始clip内容
- 返回带序号的有序步骤，方便LLM理解时序

---

### 3.2 函数2: `query_step_sequence()`

**用途**: 回答时序相关问题（"之后做了什么？"、"有几个步骤？"）

**输入**:
- `procedure`: 匹配到的Procedure
- `query_type`: 'count' | 'first' | 'last' | 'after' | 'before'
- `reference_action`: 参考动作（可选）

**输出**:
```python
{
    'query_type': 'after',
    'reference': 'Enter room',
    'result': 'Place grocery bag on counter',
    'total_steps': 3,
    'full_sequence': ['Enter room', 'Place bag', 'Place item'],
}
```

**支持的查询类型**:
| 类型 | 问题示例 | 实现方式 |
|------|---------|---------|
| count | "有多少步？" | `len(steps)` |
| first | "第一步是什么？" | `steps[0]` |
| last | "最后做了什么？" | `steps[-1]` |
| after | "X之后做了什么？" | 找到X的索引，返回下一步 |
| before | "X之前做了什么？" | 找到X的索引，返回上一步 |

---

### 3.3 函数3: `aggregate_character_behaviors()`

**用途**: 回答人物理解问题（"Bob熟悉做饭吗？"）

**输入**:
- `character_id`: 人物ID（如 "character_0"）
- `nstf_graph`: NSTF图谱
- `video_graph`: 视频图谱

**输出**:
```python
{
    'character': 'character_0',
    'involved_procedures': [
        {'goal': 'Cooking pasta', 'proc_type': 'task', 'role': 'performer'},
        {'goal': 'Teaching cooking', 'proc_type': 'habit', 'role': 'instructor'}
    ],
    'behavior_summary': 'character_0 is involved in 2 cooking-related procedures, suggesting familiarity with cooking.',
    'evidence_clips': [26, 27, 35, 41],
}
```

**实现要点**:
- 遍历所有Procedure，通过 `episodic_links` 找到涉及该人物的Procedure
- 聚合行为模式，生成summary

---

## 4. 实现细节

### 4.1 文件结构

```
qa_system/core/
├── retriever_nstf.py        # NSTF检索器（已实现基础版）
│   ├── search()             # 主入口
│   ├── _search_procedures() # 多粒度向量检索
│   ├── get_procedure_with_evidence()      # Symbolic函数1
│   ├── query_step_sequence()              # Symbolic函数2
│   └── aggregate_character_behaviors()    # Symbolic函数3
└── ...
```

### 4.2 问题类型分类

```python
def classify_query(query: str) -> str:
    """简单规则分类问题类型"""
    query_lower = query.lower()
    
    # 时序问题
    if any(kw in query_lower for kw in ['after', 'before', 'then', 'next', 'first', 'last', 
                                         'how many steps', '之后', '之前', '第一步', '最后']):
        return 'temporal'
    
    # 人物理解问题
    if any(kw in query_lower for kw in ['familiar', 'usually', 'habit', 'often', 'good at',
                                         '熟悉', '习惯', '擅长', '经常']):
        return 'character'
    
    # 默认：返回Procedure + 证据
    return 'procedure'
```

### 4.3 返回格式

**Procedure信息格式**:
```
--- Procedure 1 (Relevance: 0.45, matched by goal) ---
Goal: Unpacking groceries
Steps:
  1. Enter room carrying groceries
  2. Place grocery bag on counter
  3. Place additional item on counter
Evidence Clips: 26, 27, 28
```

**时序查询格式**:
```
[Step Sequence Query]
Total Steps: 3
Question: What did character_0 do after entering?
Answer: Place grocery bag on counter (Step 2 of 3)
Full Sequence: Enter room → Place bag → Place item
```

**人物聚合格式**:
```
[Character Behavior Analysis]
Character: character_0
Involved in 2 procedures:
  - Unpacking groceries (task)
  - Organizing kitchen (habit)
Behavior Pattern: Frequently involved in kitchen-related activities
```

---

## 5. 与Baseline的对比

| 维度 | Baseline (Clip级别) | NSTF (本设计) |
|------|---------------------|--------------|
| 检索单位 | 30秒视频片段 | 事件模式 + 精准证据 |
| 时序理解 | 需LLM从零推理 | `query_step_sequence()` 直接查询 |
| 人物理解 | 零散描述 | `aggregate_character_behaviors()` 聚合 |
| 噪声水平 | 高 (无关信息多) | 低 (精准定位) |
| 可解释性 | 低 | 高 (结构化输出) |

---

## 6. 验证指标

| 指标 | 目标 | 说明 |
|------|------|------|
| Procedure命中率 | >30% | 多粒度匹配应提高命中率 |
| 时序问题准确率 | > Baseline 5%+ | `query_step_sequence()` 的价值 |
| 人物问题准确率 | > Baseline 5%+ | `aggregate_character_behaviors()` 的价值 |
| 整体准确率 | >= Baseline | 不能比baseline差 |
| 回退触发率 | <50% | NSTF应该有实际贡献 |

---

## 附录: Procedure节点数据结构

```python
{
    'proc_id': 'kitchen_03_proc_1',
    'goal': 'Unpacking groceries',
    'proc_type': 'task',
    'steps': [
        {'step_id': 'step_1', 'action': 'Enter room carrying groceries'},
        {'step_id': 'step_2', 'action': 'Place grocery bag on counter'},
        {'step_id': 'step_3', 'action': 'Place additional item on counter'},
    ],
    'episodic_links': [
        {'clip_id': 26, 'relevance': 'source'},
        {'clip_id': 27, 'relevance': 'source'},
        {'clip_id': 28, 'relevance': 'discovered'},
    ],
    'embeddings': {
        'goal_emb': [3072维向量],
    },
    'metadata': {
        'source_clips': [26, 27, 28],
        'observation_count': 1,
    }
}
```
