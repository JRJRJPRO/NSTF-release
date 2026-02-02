# NSTF 图谱构建方案 V2

> **文档状态**: 待评审  
> **更新日期**: 2026-02-02  
> **作者**: AI Assistant (基于现有代码和技术文档分析)

---

## 1. 问题诊断：当前实现与设计的差距

### 1.1 设计意图 vs 实际实现

通过对比 `docs/NSTF-Paper-Plan/` 中的技术文档和实际代码，发现以下**设计但未完全实现**的功能：

| 设计意图 | 文档描述 | 实际实现 | 差距分析 |
|---------|---------|---------|---------|
| **episodic_links 追溯** | Procedure → Episodic 边，用于回答"谁教的"等问题 | 代码中有 `episodic_links` 字段，但**获取 clip 内容失败** | `video_graph.contents` 属性不存在；使用了错误的 API |
| **Procedure 增量更新** | 新 clip 到来时更新已有 Procedure（边概率、步骤等） | **完全未实现**，每次全量重建 | 缺少 `ProcedureUpdater` 模块 |
| **跨观测知识融合** | Node Alignment + Edge Merging | **未实现** | 缺少融合逻辑 |
| **DAG 结构** | steps + edges 构成有向无环图 | 有 `edges` 字段但**很少被填充**，多为空 | LLM 提取时 edge 信息丢失 |
| **丰富的步骤属性** | triggers, outcomes, duration_seconds, success_rate | 提取器 prompt 中有要求，但**返回结果通常缺失** | LLM 输出不稳定 |
| **Memory Prototype 聚合** | Hybrid: α·Embed(goal) + (1-α)·Mean(v_i) | 只用了 `Embed(goal+steps)` | 缺少 episodic 向量聚合 |

### 1.2 导致准确率低的直接原因

通过分析 `results/nstf/robot/kitchen_03/` 的测试结果：

```
问题: "What are wiped by the dishcloth?"
答案: "The countertop, the refrigerator, and the window."

实际表现:
- search_count: 0
- retrieval_trace: []
- gpt_eval: false

原因分析:
1. NSTF 图谱中没有与 "dishcloth" 相关的 Procedure
2. Procedure 检索阈值 (0.30) 未达到 → fallback 到 baseline
3. Baseline 也未找到相关内容 → 返回空
```

**根本原因**: 图谱内容过于稀疏、抽象，与问题的具体细节不匹配。

---

## 2. 核心问题深度分析

### 2.1 episodic_links 为什么失效？

检索器 `retriever_nstf.py` 中的 `_extract_episodic_evidence()`:

```python
# 尝试从 video_graph.contents 获取
if hasattr(video_graph, 'contents'):
    contents = video_graph.contents
    for clip_id in clip_ids:
        if clip_id in contents:
            evidence[clip_id] = contents[clip_id]
```

**问题**: `VideoGraph` 对象**没有 `contents` 属性**！

正确的获取方式应该是：
```python
# 通过 text_nodes_by_clip 获取 clip 内容
if clip_id in video_graph.text_nodes_by_clip:
    node_ids = video_graph.text_nodes_by_clip[clip_id]
    for node_id in node_ids:
        node = video_graph.nodes[node_id]
        contents = node.metadata.get('contents', [])
```

### 2.2 Procedure 内容为什么太抽象？

当前的提取器 (`extractor.py`) 流程：

```
全部 episodic 内容 → LLM 检测 Procedure → LLM 提取结构 → 保存
```

问题：
1. **输入内容截断过早**: `max_content_chars=150`，丢失关键细节
2. **LLM 倾向于泛化**: 将具体动作（如"用抹布擦窗户"）抽象为"清洁"
3. **缺少质量验证**: 提取结果无 ground truth 校验

### 2.3 Procedure 更新机制缺失

文档设计了**增量更新**，但代码中完全是**全量重建**：

```python
# builder.py 中的 build() 方法
def build(self, video_name, dataset, max_procedures):
    # 1. 加载 baseline 图谱
    # 2. 提取 episodic 内容
    # 3. 检测 procedures (全量)
    # 4. 提取结构 (全量)
    # 5. 保存
```

这意味着：
- 每次运行都是独立的，不会利用之前的 Procedure
- 无法进行"观测到新 clip 后更新边概率"的设计

---

## 3. 改进方案设计

### 3.1 方案概述

为支持**消融实验**，设计两种图谱构建模式：

| 模式 | 名称 | 特点 | 适用场景 |
|------|------|------|---------|
| **Mode A** | `static` | 一次性构建，不更新 | 消融对照组，验证基础 E2P 效果 |
| **Mode B** | `incremental` | 逐 clip 构建，支持 Procedure 更新 | 主实验，验证增量学习效果 |

### 3.2 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    NSTFGraphBuilder V2                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐       ┌──────────────────────────────┐   │
│  │  Mode Selector   │       │    ProcedureExtractor        │   │
│  │  - static        │──────>│    - detect_procedures()     │   │
│  │  - incremental   │       │    - extract_structure()     │   │
│  └──────────────────┘       │    - extract_detailed_facts()│   │ <- 新增
│                             └──────────────────────────────┘   │
│                                       │                         │
│           ┌───────────────────────────┼───────────────────────┐ │
│           │                           │                       │ │
│           ▼                           ▼                       │ │
│  ┌─────────────────┐       ┌─────────────────────────────┐   │ │
│  │ Static Builder  │       │   Incremental Builder       │   │ │
│  │ - build_all()   │       │   - build_clip()            │   │ │
│  │ - no update     │       │   - match_existing()        │   │ │
│  └─────────────────┘       │   - update_or_create()      │   │ │
│                             │   - update_probabilities()  │   │ │
│                             └─────────────────────────────┘   │ │
│                                       │                       │ │
│                                       ▼                       │ │
│                            ┌─────────────────────┐            │ │
│                            │  EpisodicLinker     │            │ │
│                            │  - link_to_clips()  │            │ │
│                            │  - verify_links()   │            │ │
│                            └─────────────────────┘            │ │
│                                                               │ │
└───────────────────────────────────────────────────────────────┘ │
```

---

## 4. 详细技术设计

### 4.1 数据结构改进

#### 4.1.1 ProcedureNode 完整定义

```python
@dataclass
class ProcedureNode:
    """改进后的 Procedure 节点"""
    
    # === 基础标识 ===
    proc_id: str                    # 唯一标识
    goal: str                       # 目标/触发条件
    proc_type: str                  # task | habit | trait | social
    description: str                # 简要描述
    
    # === DAG 结构 ===
    steps: List[StepNode]           # 步骤节点列表
    edges: List[DAGEdge]            # 有向边列表
    
    # === Episodic 链接（核心改进）===
    episodic_links: List[EpisodicLink]  # 关联的原始 clip
    
    # === Neural 入口 ===
    embeddings: Dict[str, np.ndarray]   # 多种 embedding
        # 'goal_emb': goal 文本 embedding (3072)
        # 'steps_emb': steps 聚合 embedding (3072)
        # 'prototype': 混合 prototype (3072)
    
    # === 元数据 ===
    metadata: Dict
        # 'created_at': 创建时间
        # 'updated_at': 最后更新时间
        # 'observation_count': 被观测到的次数
        # 'source_clips': 原始来源 clip 列表
        # 'confidence': 整体置信度


@dataclass
class StepNode:
    """步骤节点"""
    step_id: str
    action: str                     # 动作描述
    
    # 丰富属性（LLM 提取，允许缺失）
    triggers: List[str] = None      # 触发条件
    outcomes: List[str] = None      # 执行结果/状态变化
    required_tools: List[str] = None
    required_items: List[str] = None
    duration_seconds: int = None
    success_rate: float = 0.95


@dataclass  
class DAGEdge:
    """DAG 边"""
    from_step: str
    to_step: str
    probability: float = 1.0        # 转移概率，支持 alternatives
    condition: str = None           # 可选条件
    edge_type: str = 'sequential'   # sequential | parallel | conditional


@dataclass
class EpisodicLink:
    """Episodic 链接 - 核心改进"""
    clip_id: int                    # 关联的 clip ID
    relevance: str                  # source | evidence | update
    step_idx: int = None            # 关联的步骤索引
    timestamp: str = None           # 时间戳
    content_preview: str = None     # 内容预览（前100字）
```

#### 4.1.2 NSTF 图谱完整结构

```python
NSTFGraph = {
    'video_name': str,
    'dataset': str,
    'procedure_nodes': Dict[str, ProcedureNode],
    
    # 新增：事实性知识索引（解决抽象问题）
    'fact_index': Dict[str, List[FactItem]],
    # 例: {'dishcloth': [FactItem(clip_id=5, content="用抹布擦窗户", ...)]}
    
    'metadata': {
        'version': '2.0',
        'build_mode': 'static' | 'incremental',
        'created_at': str,
        'updated_at': str,
        'total_clips_processed': int,
        'total_procedures': int,
    }
}
```

### 4.2 Mode A: Static Builder (静态构建)

用于消融实验对照组，一次性处理所有 clips。

```python
class StaticNSTFBuilder:
    """静态 NSTF 构建器"""
    
    def build(self, video_name: str, dataset: str) -> NSTFGraph:
        """
        一次性构建完整 NSTF 图谱
        
        流程:
        1. 加载 baseline memory graph
        2. 提取所有 episodic 内容
        3. 检测 procedures (全量)
        4. 提取结构 + 建立 episodic_links
        5. 构建事实索引
        6. 生成 embeddings
        7. 保存
        """
        # 加载
        mem_graph = self.load_memory_graph(video_name, dataset)
        all_contents = self.extract_all_episodic(mem_graph)
        
        # 检测
        procedures = self.extractor.detect_procedures(
            all_contents,
            max_procedures=self.config['max_procedures']
        )
        
        # 提取结构 + 链接
        procedure_nodes = {}
        for proc in procedures:
            structure = self.extractor.extract_structure(all_contents, proc)
            node = self.create_procedure_node(structure, all_contents)
            
            # 核心改进：建立真实的 episodic_links
            node.episodic_links = self.build_episodic_links(
                structure, all_contents, mem_graph
            )
            
            procedure_nodes[node.proc_id] = node
        
        # 新增：构建事实索引
        fact_index = self.build_fact_index(all_contents)
        
        return NSTFGraph(
            video_name=video_name,
            dataset=dataset,
            procedure_nodes=procedure_nodes,
            fact_index=fact_index,
            metadata={'build_mode': 'static', ...}
        )
```

### 4.3 Mode B: Incremental Builder (增量构建)

主实验方案，支持 Procedure 更新。

```python
class IncrementalNSTFBuilder:
    """增量 NSTF 构建器"""
    
    def build(self, video_name: str, dataset: str) -> NSTFGraph:
        """
        逐 clip 增量构建 NSTF 图谱
        
        关键差异：每个 clip 到来时，先尝试匹配已有 Procedure，
        匹配成功则更新，不成功才创建新的。
        """
        mem_graph = self.load_memory_graph(video_name, dataset)
        clips = self.get_sorted_clips(mem_graph)
        
        nstf_graph = NSTFGraph(
            video_name=video_name,
            build_mode='incremental'
        )
        
        for clip_id in clips:
            clip_content = self.get_clip_content(mem_graph, clip_id)
            
            # 步骤 1: 检测当前 clip 是否包含程序性知识
            detected = self.extractor.detect_in_clip(clip_content)
            
            if not detected:
                # 仅更新事实索引
                self.update_fact_index(nstf_graph, clip_id, clip_content)
                continue
            
            # 步骤 2: 尝试匹配已有 Procedure
            matched_proc = self.match_existing_procedure(
                nstf_graph, detected
            )
            
            if matched_proc:
                # 步骤 3a: 更新已有 Procedure
                self.update_procedure(
                    matched_proc, 
                    clip_id, 
                    clip_content,
                    detected
                )
            else:
                # 步骤 3b: 创建新 Procedure
                new_proc = self.create_procedure(
                    detected,
                    clip_id,
                    clip_content
                )
                nstf_graph.procedure_nodes[new_proc.proc_id] = new_proc
        
        return nstf_graph
    
    def match_existing_procedure(
        self, 
        nstf_graph: NSTFGraph, 
        detected: Dict
    ) -> Optional[ProcedureNode]:
        """
        匹配已有 Procedure
        
        策略:
        1. 计算 detected.goal 与所有现有 Procedure 的相似度
        2. 如果最高相似度 > threshold (0.75)，认为是同一个 Procedure
        """
        if not nstf_graph.procedure_nodes:
            return None
        
        detected_emb = self.embed(detected['goal'])
        
        best_match = None
        best_sim = 0
        
        for proc in nstf_graph.procedure_nodes.values():
            sim = cosine_similarity(detected_emb, proc.embeddings['goal_emb'])
            if sim > best_sim:
                best_sim = sim
                best_match = proc
        
        if best_sim >= self.config['match_threshold']:  # 默认 0.75
            return best_match
        return None
    
    def update_procedure(
        self,
        proc: ProcedureNode,
        clip_id: int,
        clip_content: Dict,
        detected: Dict
    ):
        """
        更新已有 Procedure
        
        更新内容:
        1. 添加新的 episodic_link
        2. 更新 observation_count
        3. 可选: 更新 steps（如果发现新步骤）
        4. 可选: 更新 edge probabilities（如果发现新路径）
        """
        # 添加 episodic_link
        new_link = EpisodicLink(
            clip_id=clip_id,
            relevance='update',
            content_preview=clip_content.get('content', '')[:100]
        )
        proc.episodic_links.append(new_link)
        
        # 更新元数据
        proc.metadata['observation_count'] += 1
        proc.metadata['updated_at'] = datetime.now().isoformat()
        proc.metadata['source_clips'].append(clip_id)
        
        # 可选: 检测新步骤
        new_steps = self.detect_new_steps(proc, detected, clip_content)
        if new_steps:
            self.merge_steps(proc, new_steps)
        
        # 可选: 更新边概率
        self.update_edge_probabilities(proc, detected)
        
        # 更新 prototype embedding
        self.update_prototype(proc, clip_content)
```

### 4.4 Episodic Links 修复

```python
class EpisodicLinker:
    """修复 episodic_links 获取问题"""
    
    def build_links(
        self,
        structure: Dict,
        all_contents: List[Dict],
        mem_graph
    ) -> List[EpisodicLink]:
        """
        建立 Procedure 与 Episodic 的链接
        """
        links = []
        
        # 从 structure 中获取 source_clips
        source_clips = structure.get('source_clips', [])
        
        for clip_id in source_clips:
            # 获取该 clip 的实际内容
            content = self.get_clip_content(mem_graph, clip_id)
            
            link = EpisodicLink(
                clip_id=clip_id,
                relevance='source',
                content_preview=content[:100] if content else None
            )
            links.append(link)
        
        return links
    
    def get_clip_content(self, mem_graph, clip_id: int) -> str:
        """
        正确获取 clip 内容（修复原有 bug）
        """
        if clip_id not in mem_graph.text_nodes_by_clip:
            return None
        
        node_ids = mem_graph.text_nodes_by_clip[clip_id]
        contents = []
        
        for node_id in node_ids:
            node = mem_graph.nodes.get(node_id)
            if node and hasattr(node, 'metadata'):
                node_contents = node.metadata.get('contents', [])
                contents.extend(node_contents)
        
        return ' '.join(contents)
```

### 4.5 事实索引 (Fact Index) - 解决抽象问题

```python
class FactIndexBuilder:
    """
    构建事实索引，解决 Procedure 过于抽象的问题
    
    思路: 除了抽象的 Procedure，还维护一个具体事实的倒排索引
    """
    
    def build_index(self, all_contents: List[Dict]) -> Dict[str, List[FactItem]]:
        """
        构建关键词到事实的索引
        
        例如:
        {
            'dishcloth': [
                FactItem(clip_id=5, content="用抹布擦窗户", entities=['窗户'])
            ],
            'spinach': [
                FactItem(clip_id=3, content="把菠菜放进冰箱抽屉", entities=['冰箱抽屉'])
            ]
        }
        """
        index = defaultdict(list)
        
        for item in all_contents:
            clip_id = item['clip_id']
            content = item['content']
            
            # 提取关键词和实体
            keywords = self.extract_keywords(content)
            
            for keyword in keywords:
                fact_item = FactItem(
                    clip_id=clip_id,
                    content=content,
                    entities=self.extract_entities(content)
                )
                index[keyword.lower()].append(fact_item)
        
        return dict(index)
    
    def extract_keywords(self, content: str) -> List[str]:
        """提取关键词（名词、动词）"""
        # 可用 spaCy 或简单的规则
        # 保留: 物品名、动作、人名
        pass
```

### 4.6 改进的检索器

```python
class NSTFRetrieverV2:
    """
    改进的 NSTF 检索器
    
    三层检索策略:
    1. Fact Index 精确查找（针对具体问题）
    2. Procedure 向量检索（针对程序性问题）
    3. Episodic Links 追溯（获取原始证据）
    """
    
    def search(self, query: str, nstf_graph, mem_graph) -> Dict:
        memories = {}
        
        # Layer 1: Fact Index 查找
        keywords = self.extract_query_keywords(query)
        fact_matches = []
        for keyword in keywords:
            if keyword in nstf_graph.fact_index:
                fact_matches.extend(nstf_graph.fact_index[keyword])
        
        if fact_matches:
            for fact in fact_matches[:5]:
                clip_content = self.get_clip_content(mem_graph, fact.clip_id)
                memories[f'CLIP_{fact.clip_id}'] = clip_content
        
        # Layer 2: Procedure 检索
        matched_procs = self.match_procedures(query, nstf_graph)
        
        if matched_procs:
            # 格式化 Procedure 信息
            proc_info = self.format_procedures(matched_procs)
            memories['NSTF_Procedures'] = proc_info
            
            # Layer 3: Episodic Links 追溯
            for proc in matched_procs:
                for link in proc.episodic_links:
                    if link.clip_id not in [f.clip_id for f in fact_matches]:
                        clip_content = self.get_clip_content(mem_graph, link.clip_id)
                        if clip_content:
                            memories[f'CLIP_{link.clip_id}'] = clip_content
        
        return memories
```

---

## 5. 实施计划

### 5.1 阶段划分

| 阶段 | 任务 | 预计时间 | 输出 |
|------|------|---------|------|
| Phase 1 | 修复 episodic_links 获取 bug | 1天 | 修复后的 retriever_nstf.py |
| Phase 2 | 实现 Fact Index | 2天 | FactIndexBuilder 类 |
| Phase 3 | 改进 Extractor（更详细的提取） | 2天 | 新的 prompt + 后处理 |
| Phase 4 | 实现 Static Builder V2 | 2天 | StaticNSTFBuilder 类 |
| Phase 5 | 实现 Incremental Builder | 3天 | IncrementalNSTFBuilder 类 |
| Phase 6 | 改进 Retriever | 2天 | NSTFRetrieverV2 类 |
| Phase 7 | 测试与调优 | 2天 | 实验报告 |

### 5.2 文件结构变更

```
nstf_builder/
├── __init__.py
├── builder.py              # 原有，保留兼容
├── builder_v2.py           # 新增：V2 构建器入口
├── static_builder.py       # 新增：静态构建器
├── incremental_builder.py  # 新增：增量构建器
├── extractor.py            # 改进：更详细的提取
├── fact_index.py           # 新增：事实索引构建
├── episodic_linker.py      # 新增：episodic 链接器
├── procedure_matcher.py    # 新增：Procedure 匹配器（用于增量更新）
├── config/
│   ├── default.json
│   └── incremental.json    # 新增：增量构建配置
└── prompts/
    ├── detect.txt
    ├── structure.txt
    └── detailed_facts.txt  # 新增：详细事实提取 prompt

qa_system/core/
├── retriever_nstf.py       # 修复 bug
├── retriever_nstf_v2.py    # 新增：V2 检索器
└── ...
```

---

## 6. 风险评估与缓解

### 6.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| LLM 提取不稳定 | 步骤/边信息缺失 | 高 | 多次重试 + 后处理补全 |
| Procedure 匹配误差 | 错误更新/重复创建 | 中 | 调高匹配阈值 (0.75→0.80) |
| 增量构建顺序敏感 | 不同顺序产生不同图谱 | 中 | 对于对照实验使用固定顺序 |
| Fact Index 膨胀 | 内存占用过大 | 低 | 限制每个关键词最多保留 N 条 |
| Embedding API 成本 | 费用增加 | 中 | 缓存 + 批量调用 |

### 6.2 实验设计风险

| 风险 | 缓解措施 |
|------|---------|
| Static vs Incremental 对比不公平 | 控制相同的输入内容，只改变构建方式 |
| Fact Index 是否算作"NSTF 特性" | 可以设计单独的消融：+FactIndex vs 不加 |
| 如何证明 Procedure 更新有效 | 设计跨视频场景：同一任务在多个视频中出现 |

---

## 7. 消融实验设计

### 7.1 实验组别

| 组别 | 构建模式 | Fact Index | Procedure 更新 | 预期效果 |
|------|---------|------------|---------------|---------|
| **Baseline** | - | - | - | 原始 M3-Agent |
| **NSTF-Static** | static | ✗ | ✗ | 验证基础 E2P |
| **NSTF-Static+FI** | static | ✓ | ✗ | 验证 Fact Index 价值 |
| **NSTF-Incr** | incremental | ✗ | ✓ | 验证增量更新价值 |
| **NSTF-Full** | incremental | ✓ | ✓ | 完整系统 |

### 7.2 评估指标

1. **Overall Accuracy**: 整体问答准确率
2. **Procedural Accuracy**: 步骤类问题准确率
3. **Factual Accuracy**: 事实类问题准确率
4. **Retrieval Precision**: 检索到相关内容的比例
5. **Empty Search Rate**: 空搜索结果的比例
6. **Procedure Utilization**: Procedure 被使用的比例

---

## 8. 附录：关键代码片段

### 8.1 修复 episodic_links 获取

```python
# 修改 qa_system/core/retriever_nstf.py

def _extract_episodic_evidence(
    self,
    matched_procs: List[Dict],
    nstf_graph: Dict,
    video_graph
) -> Dict[int, List[str]]:
    """修复后的版本"""
    proc_nodes = nstf_graph.get('procedure_nodes', {})
    clip_ids = set()
    
    for match in matched_procs:
        proc = proc_nodes.get(match['proc_id'], {})
        for link in proc.get('episodic_links', []):
            clip_id = link.get('clip_id')
            if clip_id is not None:
                clip_ids.add(clip_id)
    
    evidence = {}
    
    # 修复：使用正确的 API 获取 clip 内容
    for clip_id in clip_ids:
        if clip_id in video_graph.text_nodes_by_clip:
            node_ids = video_graph.text_nodes_by_clip[clip_id]
            contents = []
            for node_id in node_ids:
                node = video_graph.nodes.get(node_id)
                if node and hasattr(node, 'metadata'):
                    node_contents = node.metadata.get('contents', [])
                    contents.extend(node_contents)
            if contents:
                evidence[clip_id] = contents
    
    return evidence
```

### 8.2 Procedure 匹配（用于增量更新）

```python
def match_existing_procedure(
    self,
    nstf_graph: NSTFGraph,
    detected_goal: str,
    match_threshold: float = 0.75
) -> Optional[ProcedureNode]:
    """
    判断检测到的程序是否与已有程序匹配
    """
    from mmagent.utils.chat_api import parallel_get_embedding
    import numpy as np
    
    if not nstf_graph.procedure_nodes:
        return None
    
    # 计算检测到的 goal 的 embedding
    embs, _ = parallel_get_embedding("text-embedding-3-large", [detected_goal])
    detected_emb = np.array(embs[0])
    detected_emb = detected_emb / (np.linalg.norm(detected_emb) + 1e-8)
    
    best_match = None
    best_sim = 0
    
    for proc in nstf_graph.procedure_nodes.values():
        if 'goal_emb' in proc.embeddings:
            proc_emb = proc.embeddings['goal_emb']
            sim = float(np.dot(detected_emb, proc_emb))
            if sim > best_sim:
                best_sim = sim
                best_match = proc
    
    if best_sim >= match_threshold:
        return best_match
    return None
```

---

## 9. 下一步行动

1. **评审本文档**：确认技术方案无重大漏洞
2. **Phase 1 快速修复**：先修复 episodic_links bug，验证现有图谱能否正常工作
3. **重新测试**：用修复后的检索器重跑 kitchen_03 测试
4. **评估是否需要重建图谱**：如果修复后效果仍差，则需要按 V2 方案重建

---

**文档结束**
