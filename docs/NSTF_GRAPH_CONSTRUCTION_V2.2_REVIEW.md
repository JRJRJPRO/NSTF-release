# NSTF Graph Construction V2.2 方案评审报告

> **评审日期**: 2026-02-02  
> **评审者**: KG/问答系统专家  
> **基于文档**: NSTF_GRAPH_CONSTRUCTION_V2.2.md

---

## 执行摘要

V2.2 是一个**成熟可实施的方案**。采纳了合理的建议，保留了实用的功能（如 content_preview、success_rate 允许猜测）。

本次评审重点检查**系统性漏洞和潜在风险**，发现 3 个需要关注的问题和 2 个小建议。

**总体评价**: ✅ 可以开始实施，但需注意以下风险点。

---

## 1. 需要关注的风险

### 1.1 🟡 风险 #1: IncrementalBuilder 的 `detect_in_clip` 未定义

**问题**：

V2.2 中 `IncrementalBuilder.build()` 调用了 `self.extractor.detect_in_clip(clip_content)`，但这个方法与 `StaticBuilder` 中使用的 `detect_procedures(all_contents)` 不同。

```python
# IncrementalBuilder
detected = self.extractor.detect_in_clip(clip_content)  # 单个 clip

# StaticBuilder  
procedures = self.extractor.detect_procedures(all_contents)  # 全部 clips
```

**潜在问题**：
1. `detect_in_clip` 需要单独实现，与 `detect_procedures` 的 prompt 和逻辑不同
2. 单个 clip 的上下文可能不足以判断是否包含 Procedure

**建议**：

```python
class ProcedureExtractor:
    def detect_in_clip(self, clip_content: Dict) -> Optional[Dict]:
        """
        检测单个 clip 是否包含程序性知识
        
        与 detect_procedures 的区别：
        - 输入是单个 clip，不是全部
        - 返回 0 或 1 个 detected procedure
        - 需要更宽松的判断标准（因为上下文有限）
        """
        prompt = f"""Analyze this single video clip to determine if it contains procedural knowledge.

Clip content:
{clip_content['content']}

If procedural knowledge is found, return JSON:
{{"detected": true, "goal": "...", "type": "task|habit|trait|social", "confidence": 0.8}}

If not found, return:
{{"detected": false}}
"""
        # ... LLM 调用
```

**或者更简单的方案**：Phase 1 先只实现 StaticBuilder，Phase 2 再实现 IncrementalBuilder。

---

### 1.2 🟡 风险 #2: embedding 计算成本可能较高

**问题**：

`EpisodicLinker.build_verified_links()` 对**每个 episodic content** 都计算 embedding：

```python
for item in all_episodic_contents:
    content_emb = self._embed(content)  # 每次调用 API
    sim = self._cosine_similarity(proc_emb, content_emb)
```

如果一个视频有 50 个 clips，每个 Procedure 都要计算 50 次 embedding。如果检测到 5 个 Procedures，就是 250 次 API 调用。

**影响**：
- API 成本增加
- 构建时间变长
- 可能触发 rate limit

**建议**：

```python
class EpisodicLinker:
    def __init__(self, ...):
        self._content_emb_cache = {}  # 缓存 content embeddings
    
    def build_verified_links(self, procedure, all_episodic_contents, video_graph):
        # 1. 先批量计算所有 content 的 embedding（只计算一次）
        if not self._content_emb_cache:
            texts = [item['content'] for item in all_episodic_contents]
            all_embs = self._batch_embed(texts)  # 批量调用
            for item, emb in zip(all_episodic_contents, all_embs):
                self._content_emb_cache[item['clip_id']] = emb
        
        # 2. 计算 Procedure embedding
        proc_emb = self._embed(proc_text)
        
        # 3. 计算相似度（使用缓存）
        for item in all_episodic_contents:
            content_emb = self._content_emb_cache[item['clip_id']]
            sim = self._cosine_similarity(proc_emb, content_emb)
            # ...
    
    def _batch_embed(self, texts: List[str]) -> List[np.ndarray]:
        """批量获取 embeddings"""
        from mmagent.utils.chat_api import parallel_get_embedding
        embs, _ = parallel_get_embedding("text-embedding-3-large", texts)
        return [np.array(e) / (np.linalg.norm(e) + 1e-8) for e in embs]
```

**效果**：将 N_procs × N_clips 次调用减少到 N_clips + N_procs 次。

---

### 1.3 🟡 风险 #3: 检索时可能遗漏 Baseline 的 fallback 逻辑

**问题**：

V2.2 的 `NSTFRetrieverV2.retrieve_with_episodic()` 只处理了 **NSTF 命中的情况**。但如果：
1. 没有匹配到任何 Procedure
2. 匹配到的 Procedure 的 episodic_links 都为空

应该有 fallback 到 Baseline 的逻辑。

**现有代码的检索流程**（在 retriever_nstf.py 中）：

```python
if not matched_procs or matched_procs[0]['similarity'] < self.min_confidence:
    # Fallback 到 baseline
    memories, current_clips, _ = baseline_search(...)
```

**建议确认**：V2.2 的 `NSTFRetrieverV2` 是否会被集成到现有的 `NSTFRetriever.search()` 中，还是完全替代？

如果是替代，需要在 `NSTFRetrieverV2` 中添加 fallback 逻辑：

```python
class NSTFRetrieverV2:
    def search(self, query, nstf_graph, video_graph, ...) -> Dict:
        """完整的检索流程"""
        # 1. 尝试 NSTF 检索
        matched_procs = self._match_procedures(query, nstf_graph)
        
        if matched_procs and matched_procs[0]['similarity'] >= self.min_confidence:
            # NSTF 命中
            return self.retrieve_with_episodic(matched_procs, nstf_graph, video_graph)
        else:
            # Fallback 到 Baseline
            from mmagent.retrieve import search as baseline_search
            memories, _, _ = baseline_search(video_graph, query, [], ...)
            return memories
```

---

## 2. 小建议

### 2.1 建议 #1: 添加构建统计信息

在构建完成后，输出一些关键统计信息，便于快速判断图谱质量：

```python
def build(self, video_name, dataset):
    # ... 构建逻辑
    
    # 构建完成后输出统计
    stats = {
        'total_procedures': len(procedure_nodes),
        'total_links': sum(len(p['episodic_links']) for p in procedure_nodes.values()),
        'avg_links_per_proc': ...,
        'link_distribution': {
            'source': ...,
            'discovered': ...,
        },
        'character_mapping_found': bool(self.character_resolver.mapping),
    }
    
    if self.debug:
        print(f"\n=== Build Statistics ===")
        print(f"Procedures: {stats['total_procedures']}")
        print(f"Total links: {stats['total_links']}")
        print(f"Avg links/proc: {stats['avg_links_per_proc']:.1f}")
        print(f"Character mapping: {'Yes' if stats['character_mapping_found'] else 'No'}")
    
    return nstf_graph, stats  # 返回统计信息
```

### 2.2 建议 #2: ProcedureMatcher 的 decision_log 持久化

当前 `decision_log` 只在内存中，进程结束就丢失。建议在构建完成后保存：

```python
# 在 IncrementalBuilder.build() 结束时
if self.debug:
    import json
    log_path = f"logs/{video_name}_match_decisions.json"
    with open(log_path, 'w') as f:
        json.dump(self.matcher.decision_log, f, indent=2)
    print(f"Match decisions saved to {log_path}")
```

这有助于后续审核匹配决策是否合理。

---

## 3. 验证清单补充

在 V2.2 的核心链路验证清单基础上，补充几项：

```
□ 8. 验证 embedding 缓存是否正常工作（避免重复计算）
□ 9. 验证 fallback 到 Baseline 的逻辑是否正常
□ 10. 检查构建时间是否在可接受范围（<5分钟/视频）
□ 11. 检查 API 调用次数是否合理（构建时、检索时）
```

---

## 4. 总结

V2.2 方案整体完善，可以开始实施。需要注意：

| 风险 | 严重性 | 建议处理时间 |
|------|--------|------------|
| `detect_in_clip` 未定义 | 中 | Phase 1 只实现 Static，Phase 2 再实现 Incremental |
| embedding 计算成本 | 中 | Phase 1 实现缓存机制 |
| fallback 逻辑 | 低 | Phase 1 确认集成方式 |

**推荐的实施顺序**：

1. **Phase 0**：修复 bug + CharacterResolver + 手动验证
2. **Phase 1**：StaticBuilder + EpisodicLinker（带缓存）+ 阈值调参
3. **Phase 1.5**：确认检索器集成方式，添加 fallback
4. **Phase 2**：IncrementalBuilder + ProcedureMatcher

---

*评审结束*
