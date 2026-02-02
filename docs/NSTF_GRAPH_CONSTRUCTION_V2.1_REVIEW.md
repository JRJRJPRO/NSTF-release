# NSTF Graph Construction V2.1 方案评审报告

> **评审日期**: 2026-02-02  
> **评审者**: KG/问答系统专家  
> **基于文档**: NSTF_GRAPH_CONSTRUCTION_V2.1.md

---

## 执行摘要

V2.1 已采纳大部分评审建议，整体方案合理。本次评审聚焦于：
1. **属性定义的最终确认** — 明确哪些必须、哪些可选
2. **属性验证实验设计** — 快速实验确定属性价值
3. **消融实验精简** — 移除 NoLinks 组
4. **剩余风险和建议**

---

## 1. 节点与边属性最终定义

### 1.1 Procedure 节点属性

| 属性 | 类型 | 必要性 | 说明 | 验证方式 |
|------|------|--------|------|---------|
| `proc_id` | str | **必须** | 唯一标识 | - |
| `goal` | str | **必须** | 触发条件/目标 | - |
| `proc_type` | str | **必须** | task/habit/trait/social | 检查分布是否合理 |
| `steps` | List[Step] | **必须** | 步骤列表 | - |
| `episodic_links` | List[Link] | **必须** | 追溯链接 | 检查 precision/recall |
| `embeddings.goal_emb` | ndarray | **必须** | 检索匹配用 | - |
| `description` | str | 可选 | 简要描述 | 实验验证是否提升准确率 |
| `edges` | List[Edge] | 可选 | DAG 边 | 实验验证 |
| `embeddings.steps_emb` | ndarray | 可选 | steps 聚合 embedding | 实验验证是否比 goal_emb 更好 |
| `metadata.observation_count` | int | 增量时必须 | 被观测次数 | - |
| `metadata.source_clips` | List[int] | 推荐 | 来源 clips | 调试用 |

### 1.2 Step 节点属性

| 属性 | 类型 | 必要性 | 说明 | 验证方式 |
|------|------|--------|------|---------|
| `step_id` | str | **必须** | 步骤标识 | - |
| `action` | str | **必须** | 动作描述 | - |
| `triggers` | List[str] | 待验证 | 触发条件 | 检查 LLM 提取成功率 |
| `outcomes` | List[str] | 待验证 | 执行结果 | 检查 LLM 提取成功率 |
| `required_tools` | List[str] | 待验证 | 所需工具 | 检查是否对工具类问题有帮助 |
| `required_items` | List[str] | 待验证 | 所需物品 | 同上 |
| `duration_seconds` | int | 不建议 | 持续时间 | LLM 难以准确估计 |
| `success_rate` | float | 不建议 | 成功率 | 无数据支撑 |

### 1.3 EpisodicLink 属性

| 属性 | 类型 | 必要性 | 说明 | 验证方式 |
|------|------|--------|------|---------|
| `clip_id` | int | **必须** | 关联的 clip ID | - |
| `relevance` | str | **必须** | source/discovered/update | 检查分布 |
| `node_id` | str | 推荐 | 具体节点 ID（更细粒度） | 实验验证是否比 clip_id 更精确 |
| `similarity` | float | 推荐 | 与 Procedure 相似度 | 用于排序和调试 |
| `verified` | bool | 可选 | 是否经过验证 | 调试用 |
| `content_preview` | str | 不建议 | 内容预览 | 增加存储，检索时动态获取即可 |

### 1.4 Edge 属性（DAG 边）

| 属性 | 类型 | 必要性 | 说明 | 验证方式 |
|------|------|--------|------|---------|
| `from_step` | str | 有 edge 时必须 | 起始步骤 ID | - |
| `to_step` | str | 有 edge 时必须 | 目标步骤 ID | - |
| `probability` | float | 可选 | 转移概率 | LLM 难以准确估计，默认 1.0 |
| `condition` | str | 可选 | 转移条件 | 检查 LLM 提取成功率 |
| `edge_type` | str | 可选 | sequential/parallel/conditional | 大多数是 sequential |

**关于 Edge 的建议**：

目前实验结果显示 `edges` 字段经常为空。建议：
1. **Phase 1 不实现 edge**，仅保留 steps 作为有序列表
2. 如果后续需要 DAG 结构，再添加 edge
3. 论文中可以说"支持 DAG 结构"，但不作为主要贡献点

---

## 2. 属性验证实验设计

### 2.1 快速验证实验（不写进论文，用于指导开发）

```python
# 实验 1: steps_emb 是否有用
def exp_steps_emb():
    """
    比较检索时使用 goal_emb vs goal_emb + steps_emb
    
    方法: 
    - 对同一组问题，分别只用 goal_emb 和 goal+steps 双 embedding 检索
    - 比较 top-3 命中率
    """
    pass

# 实验 2: node_id 粒度是否比 clip_id 更好
def exp_node_id_granularity():
    """
    比较追溯时使用 clip_id vs node_id
    
    方法:
    - 选 10 个问题，人工标注 ground truth episodic 节点
    - 比较两种粒度下返回内容的相关性
    """
    pass

# 实验 3: Step 扩展属性的提取成功率
def exp_step_attributes():
    """
    检查 LLM 能否稳定提取 triggers, outcomes, required_tools
    
    方法:
    - 对 20 个 Procedure 提取，统计各属性的非空率
    - 非空率 < 30% 的属性建议移除
    """
    pass

# 实验 4: description 是否提升准确率
def exp_description_value():
    """
    比较有 description vs 无 description
    
    方法:
    - 构建两版图谱
    - 比较 5 个问题的回答质量（人工评估）
    """
    pass
```

### 2.2 建议的验证流程

```
Phase 0: 先用 minimal 属性集跑通整个链路
         → 确认基础机制 work

Phase 1: 测试 steps_emb 和 node_id
         → 如果有提升，保留
         
Phase 2: 测试 Step 扩展属性
         → 提取成功率 > 50% 的保留
         
Phase 3: 决定最终属性集
```

---

## 3. 消融实验精简（采纳用户建议）

### 3.1 修订后的消融组

| 组别 | Procedure | episodic_links | 增量更新 | 说明 |
|------|-----------|----------------|----------|------|
| **Baseline** | ✗ | ✗ | ✗ | M3-Agent 原版 |
| **NSTF-Static** | ✓ | ✓ | ✗ | 静态构建 + 追溯 |
| **NSTF-Incr** | ✓ | ✓ | ✓ | 增量更新 |

**移除 NSTF-NoLinks 的理由**：
1. 根据核心假设，追溯是核心机制，没有 links 的 Procedure 本身意义不大
2. 减少实验工作量
3. 如果 NSTF-Static 比 Baseline 好，就已经证明了整体方案有效

### 3.2 关键对比

| 对比 | 验证目标 |
|------|---------|
| NSTF-Static vs Baseline | 证明 NSTF 整体方案有效 |
| NSTF-Incr vs NSTF-Static | 证明增量更新的价值 |

---

## 4. 剩余风险与建议

### 4.1 🟡 风险 #1: verify_threshold 和 discover_threshold 的设置

**问题**：
V2.1 设置 `verify_threshold=0.25`, `discover_threshold=0.40`，但这些值是拍脑袋的。

**建议**：
```python
# 快速调参实验
thresholds_to_test = [
    {'verify': 0.20, 'discover': 0.35},
    {'verify': 0.25, 'discover': 0.40},  # 当前值
    {'verify': 0.30, 'discover': 0.45},
]

for t in thresholds_to_test:
    linker = EpisodicLinker(verify_threshold=t['verify'], discover_threshold=t['discover'])
    # 对 5 个视频构建，统计：
    # - 平均每个 Procedure 有多少 links
    # - links 中 source vs discovered 的比例
    # - 人工抽查 10 个 link 的准确率
```

**合理范围**：
- 每个 Procedure 应有 2-8 个 links
- source 链接应占 30-50%
- 抽查准确率应 > 70%

### 4.2 🟡 风险 #2: ProcedureMatcher 的 verb_overlap 可能过于简单

**问题**：
当前实现只匹配固定的动词列表，可能遗漏领域特定动词。

**建议**：
```python
# 方案 A: 扩展动词列表
DOMAIN_VERBS = {
    'kitchen': ['chop', 'stir', 'fry', 'boil', 'bake', 'pour', 'mix', 'season'],
    'cleaning': ['wipe', 'scrub', 'sweep', 'mop', 'dust', 'vacuum'],
    'general': ['make', 'cook', 'prepare', 'clean', 'wash', 'put', 'place', 'store', ...]
}

# 方案 B: 使用 lemmatization
import spacy
nlp = spacy.load('en_core_web_sm')
def extract_verbs(text):
    doc = nlp(text)
    return {token.lemma_ for token in doc if token.pos_ == 'VERB'}
```

对于 Phase 1，方案 A 足够，如果发现问题再升级到方案 B。

### 4.3 🟡 风险 #3: Character 映射可能不完整

**问题**：
`CharacterResolver._extract_from_semantic()` 假设 video_graph 中有 `semantic_type='character'` 的节点，但这可能不存在。

**建议**：
```python
def _extract_from_semantic(self, video_graph) -> Dict[str, str]:
    """从 semantic 节点提取 character 映射"""
    mapping = {}
    
    # 尝试方法 1: 从 metadata
    if 'character_mapping' in video_graph.metadata:
        return video_graph.metadata['character_mapping']
    
    # 尝试方法 2: 从 semantic 节点
    for node_id, node in video_graph.nodes.items():
        # ... 原有逻辑
    
    # 尝试方法 3: 从 episodic 内容中推断（更复杂）
    if not mapping:
        mapping = self._infer_from_episodic(video_graph)
    
    # 如果都失败，记录警告
    if not mapping:
        print("⚠️ No character mapping found, character-related questions may fail")
    
    return mapping
```

### 4.4 建议: 添加调试模式

```python
class NSTFBuilder:
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def build(self, ...):
        if self.debug:
            # 输出每个 Procedure 的 episodic_links 数量
            # 输出 Character 映射
            # 输出任何被 reject 的链接
            pass
```

这有助于快速定位问题。

---

## 5. 最终属性推荐（Minimal Viable Set）

基于以上分析，建议 **Phase 1 使用以下最小属性集**：

### 5.1 Procedure

```python
{
    'proc_id': str,           # 必须
    'goal': str,              # 必须
    'proc_type': str,         # 必须 (task/habit/trait/social)
    'steps': [                # 必须
        {'step_id': str, 'action': str}  # 最小 step
    ],
    'episodic_links': [       # 必须
        {'clip_id': int, 'relevance': str, 'similarity': float}
    ],
    'embeddings': {
        'goal_emb': ndarray   # 必须
    },
    'metadata': {
        'source_clips': List[int],      # 推荐（调试用）
        'observation_count': int        # 增量时必须
    }
}
```

### 5.2 暂不实现

| 属性 | 暂不实现原因 | 何时考虑 |
|------|-------------|---------|
| `edges` | 当前 LLM 提取成功率低 | 需要 DAG 推理时 |
| `steps_emb` | 先验证 goal_emb 够不够 | Phase 1 实验后 |
| `step.triggers/outcomes` | 先验证提取成功率 | Phase 2 |
| `step.required_tools/items` | 同上 | Phase 2 |
| `link.node_id` | 先用 clip_id 验证链路 | Phase 1 后期 |
| `link.content_preview` | 增加存储，动态获取即可 | 不需要 |

---

## 6. 行动建议

### 6.1 Phase 0（1-2 天）

1. ✅ 修复 episodic_links bug
2. ✅ 实现 CharacterResolver
3. ✅ 用 minimal 属性集重建 kitchen_03 图谱
4. ✅ 手动验证核心链路

### 6.2 Phase 1（3-5 天）

1. 实现 EpisodicLinker（verify + discover）
2. 快速调参实验（threshold）
3. 测试 steps_emb 是否有用
4. 运行 NSTF-Static vs Baseline

### 6.3 Phase 2（5-7 天）

1. 实现 ProcedureMatcher + IncrementalBuilder
2. 测试 Step 扩展属性提取成功率
3. 运行 NSTF-Incr vs NSTF-Static
4. 确定最终属性集

---

## 7. 总结

V2.1 方案整体合理，建议：

1. **属性采用最小可行集**：先跑通核心链路，再逐步添加
2. **移除 NoLinks 消融组**：减少工作量，聚焦核心对比
3. **快速属性验证实验**：用数据驱动决策，不凭直觉
4. **添加调试模式**：便于快速定位问题

**下一步**：Phase 0 开始实施，先修复 bug + 用 minimal 属性集重建图谱。

---

*文档结束*
