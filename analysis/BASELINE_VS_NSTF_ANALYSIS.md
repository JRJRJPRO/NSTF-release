# Baseline vs NSTF 图谱问答系统对比分析报告

**分析时间**: 2026-02-03  
**分析视频**: study_09, kitchen_03  
**分析问题总数**: study_09 (12题) + kitchen_03 (14题) = 26题

---

## 📊 总体结果对比

### study_09 视频 (12题)

| 问题编号 | Baseline | NSTF | 问题类型 |
|---------|----------|------|---------|
| Q01 | ❌ | ❌ | Factual (书籍放置位置) |
| Q02 | ❌ | ❌ | Multi-Hop Reasoning (Eve的书放哪层) |
| Q03 | ✅ | ❌ | Human Understanding (Eve喜欢零食吗) |
| Q04 | ❌ | ❌ | Human Understanding (整理能力) |
| Q05 | ❌ | ❌ | Factual (鸭脖放回位置) |
| Q06 | ❌ | ❌ | Factual (椅子初始位置) |
| Q07 | ✅ | ✅ | Factual (奶茶放置位置) |
| Q08 | ❌ | ❌ | Cross-Modal (冰箱物品数量) |
| Q09 | ✅ | ❌ | Factual (文件是否移走) |
| Q10 | ❌ | ❌ | Multi-Detail (书包最终位置) |
| Q11 | ✅ | ✅ | Human Understanding (Ella整洁习惯) |
| Q12 | ❌ | ✅ | Multi-Detail (季节判断) |

**study_09 准确率**:
- Baseline: 4/12 = **33.3%**
- NSTF: 3/12 = **25.0%**

### kitchen_03 视频 (部分样本)

| 问题编号 | Baseline | NSTF | 问题类型 |
|---------|----------|------|---------|
| Q01 | ✅ | ✅ | Factual (菠菜存放位置) |
| Q02 | ❌ | ❌ | Multi-Detail (抹布擦拭对象) |

---

## 🔍 关键问题深度分析

### 1. NSTF 效果更差的典型案例

#### Q03: "Does Eve like snacks a lot?" 
**标准答案**: Yes

| 指标 | Baseline | NSTF |
|------|----------|------|
| **结果** | ✅ 正确 | ❌ 错误 |
| **轮数** | 5 | 4 |
| **耗时** | 56.11s | 55.85s |
| **检索次数** | 3 | 2 |

**Baseline 推理过程**:
- 搜索 "Does Eve like snacks a lot?"
- 发现 CLIP_28 提到 "bag of snacks" 在架子上
- 推断 Eve 可能喜欢零食（虽然推理较弱，但答对了）

**NSTF 推理过程**:
- 使用 NSTF Procedure (study_09_proc_3: Retrieving items from refrigerator)
- 找到 clip_33 关于取即食面的内容
- **无法将 voice_1058 映射到 Eve**
- 最终答案是 "无法确定"

**问题诊断**: 
- NSTF 过度依赖 Procedure 匹配，但匹配的 Procedure (0.311相似度) 与问题关联度低
- Character ID 映射问题导致无法追溯到 Eve 的行为
- **NSTF 的结构化知识反而限制了灵活推理**

---

#### Q09: "Have the documents been taken away from the big table?"
**标准答案**: No

| 指标 | Baseline | NSTF |
|------|----------|------|
| **结果** | ✅ 正确 | ❌ 错误 |
| **轮数** | 2 | 5 |
| **耗时** | 15.09s | 54.75s |
| **检索次数** | 1 | 4 |

**Baseline 推理过程**:
- 直接搜索 "Status of documents on the big table"
- 获取 CLIP_0 和 CLIP_14 信息
- 确认文件仍在桌上，回答正确

**NSTF 推理过程**:
- 使用 NSTF Procedure (study_09_proc_10)
- 多次搜索但匹配度低 (0.315-0.367)
- 4轮检索仍未获得有效信息
- **模型回答为空**

**问题诊断**:
- 简单的事实问题被 NSTF 复杂化
- NSTF 试图找"移除物品的程序"，而非直接查找文件位置
- **检索策略错误**：Factual 问题应优先查 Memory Bank，而非 NSTF Graphs

---

### 2. NSTF 效果更好的典型案例

#### Q12: "What season is it now?"
**标准答案**: Summer

| 指标 | Baseline | NSTF |
|------|----------|------|
| **结果** | ❌ 错误 | ✅ 正确 |
| **轮数** | 4 | 2 |
| **耗时** | 42.85s | 23.63s |
| **检索次数** | 0 | 1 |

**Baseline 推理过程**:
- 搜索 "current season and date"
- 尝试获取真实日期（无效策略）
- 回答"无法确定当前季节"

**NSTF 推理过程**:
- 搜索 CLIP 中的环境线索
- 找到 CLIP_17, CLIP_21 中的风扇和轻便服装
- 正确推断为夏季

**成功原因**:
- NSTF 系统触发了 Fallback 到 Baseline 的机制
- 此时 LLM 正确理解了问题需要从视频环境线索推理
- **不是 NSTF 知识本身的功劳，而是 Fallback 后的正确检索**

---

### 3. 两者都失败的关键案例

#### Q01: "Where should the book be placed back?"
**标准答案**: In the first layer of the bookshelf from the top (悬疑类书籍放第一层)

**标注推理**: 
> 第一层摆放悬疑类，第二层摆放专业类，第三层摆放言情类。这本书通过标签和封面可以确定是悬疑类，因此应放在书架从上数第一层。

| 指标 | Baseline | NSTF |
|------|----------|------|
| **模型回答** | "wooden shelf in the room" | "wooden shelf with decorative items..." |
| **问题** | 太泛化，没有指定层数 | 太泛化，没有指定层数 |

**失败原因分析**:
1. **缺少书籍分类规则的记忆**: 图谱中没有明确存储"悬疑类→第一层"的规则
2. **多跳推理失败**: 需要先识别书籍类型，再匹配到对应层
3. **Character ID 映射问题**: Eve 的阅读行为无法追溯

---

#### Q05: "Where should the robot put duck necks back?"
**标准答案**: In the second level of the upper part of Fridge

| 指标 | Baseline | NSTF |
|------|----------|------|
| **模型回答** | "bookshelf bottom left" | "round table" |
| **问题** | 完全错误 | 完全错误 |

**失败原因分析**:
1. **"duck necks" 拼写/术语问题**: 搜索时无法匹配到正确的视频内容
2. **NSTF 检索到的 Procedure**: "Retrieving items from refrigerator" (proc_3)
   - 相似度仅 0.315，匹配错误
3. **Memory Bank 检索失败**: 无法找到关于鸭脖的具体存储位置

---

## 🧩 NSTF 系统问题根因分析

### 问题1: Procedure 匹配精度不足

| 问题编号 | 最高匹配 Procedure | 相似度 | 实际相关性 |
|---------|-------------------|--------|-----------|
| Q03 | proc_3 (Retrieving items) | 0.311 | ❌ 不相关 |
| Q05 | proc_3 (Retrieving items) | 0.315 | ⚠️ 部分相关 |
| Q09 | proc_10 | 0.367 | ❌ 不相关 |

**诊断**: 当相似度 < 0.5 时，Procedure 匹配几乎都是错误的，但系统仍使用了这些低质量匹配。

### 问题2: 问题类型路由错误

根据 System Prompt，NSTF 系统定义了问题类型路由规则：
- **Factual questions**: 应优先使用 Memory Bank
- **Procedural questions**: 应优先使用 NSTF task procedures

**实际表现**:
| 问题 | 正确类型 | 实际路由 | 结果 |
|-----|---------|---------|------|
| Q03 (Eve喜欢零食吗) | Character Understanding | NSTF Procedure | ❌ |
| Q05 (鸭脖放哪) | Factual | NSTF Procedure | ❌ |
| Q09 (文件是否移走) | Factual | NSTF Procedure | ❌ |

**诊断**: 系统未能正确区分问题类型，将 Factual 问题路由到了 Procedure 检索。

### 问题3: Character ID 映射失败

两个系统都存在此问题，但 NSTF 更严重：
- 问题中使用人名 (Ella, Eve)
- 图谱中使用 voice_id/character_id (voice_1058, character_0)
- **映射查询经常返回空结果**

```
Q03 NSTF: 
- 搜索 "Eve's snack preferences" → 匹配 proc_3
- 搜索 "Character ID of Eve" → 空结果
- 最终无法确定 Eve 是谁
```

### 问题4: NSTF 增加了检索延迟

| 视频 | Baseline 平均耗时 | NSTF 平均耗时 | 增加 |
|-----|------------------|--------------|------|
| study_09 | ~35s | ~42s | +20% |

额外的 NSTF Procedure 匹配和多轮检索增加了响应时间，但未带来准确率提升。

---

## 📌 改进建议

### 1. Procedure 匹配阈值调整
```
建议: 当 Procedure 相似度 < 0.5 时，自动 Fallback 到 Baseline
当前问题: 低相似度匹配 (0.3-0.4) 仍被使用，导致错误答案
```

### 2. 问题类型路由优化
```
建议: 在 LLM 检索前，增加一个问题分类器
- Factual/Where/What → 优先 Memory Bank
- How to/Steps → 优先 NSTF Procedure
- Why/Character traits → 混合检索
```

### 3. Character ID 映射增强
```
建议: 在图谱中建立显式的 name → character_id 映射表
示例:
{
  "Eve": ["voice_1058", "character_0"],
  "Ella": ["voice_33", "voice_494"]
}
```

### 4. 检索策略分层
```
建议: 
第一轮: 直接 Memory Bank 检索
第二轮: 若失败，尝试 NSTF Procedure
第三轮: 若仍失败，扩大检索范围
当前问题: NSTF 先于 Memory Bank 检索，增加了错误传播
```

---

## 📈 结论

### NSTF 图谱当前问题总结

1. **准确率下降**: study_09 上 NSTF (25.0%) < Baseline (33.3%)
2. **检索效率低**: 平均检索轮数增加，但正确率下降
3. **Procedure 匹配质量差**: 低相似度匹配导致错误路由
4. **问题类型识别不准**: Factual 问题被错误地用 Procedure 处理

### NSTF 的潜在优势（未充分发挥）

1. Q12 (季节判断) 显示 NSTF 在环境推理上有潜力
2. 当正确 Fallback 到 Baseline 时，表现与 Baseline 持平
3. Procedure 结构本身可以提供步骤级推理（但当前实验未能体现）

### 下一步行动建议

1. **短期**: 调高 Procedure 匹配阈值 (0.5+)
2. **中期**: 重构问题类型路由逻辑
3. **长期**: 建立完整的 Character ID 映射和书籍分类规则
