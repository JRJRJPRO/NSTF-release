# 问答错误诊断报告 (初步分析)

**生成时间**: 2026-02-03  
**分析范围**: kitchen_14, living_room_06, study_07 三个视频的错误问答

---

## 一、已发现的错误案例深度分析

### 案例 1: kitchen_14_Q01 - Luna最喜欢的薯片口味

| 字段 | 内容 |
|------|------|
| **问题** | What Luna's favorite chips flavor? |
| **标准答案** | Tomato flavor |
| **模型回答** | Barbecue |
| **GPT评估** | ❌ 错误 |
| **标注推理** | Luna曾到柜子找薯片，边找边说有烧烤、蜂蜜和土豆味的薯片，最后拿了她最爱的土豆风味出来吃。 |

#### 错误根因分析

**1. 图谱信息检查**：

查看图谱 CLIP_2 的记录：
```
Node 67: "<voice_57> says, 'Barbecue.'"
Node 69: "<voice_57> says, 'And we have...'"  
Node 71: "<voice_58> says, 'Oh, we have tomatoes.'"
```

**发现**：
- 图谱中确实有 "Barbecue" 和 "tomatoes" 的记录
- 但是缺少关键信息："她最后拿了土豆风味出来吃" 
- 图谱只记录了她**找到了**这些口味，没有记录她**选择了哪个**

**2. Character 映射问题**：
- 问题中问的是 "Luna"
- 但图谱中只有 `<voice_57>` 和 `<character_0>`
- LLM 花了多轮尝试获取 Luna 对应的 character_id，但**检索返回空**
- 最终 LLM 只能猜测 character_0 = Luna

**3. LLM 推理错误**：
- 即使映射成功，LLM 看到 "Barbecue" 被先提到，就误以为那是最爱
- 实际上 "Barbecue" 只是她找到的第一个口味，不是她选择的

**诊断结论**：`GRAPH_MISSING` + `CHARACTER_MAPPING_FAILED`
- 主要原因：图谱缺少"选择/偏好"的关键信息
- 次要原因：角色名到ID的映射不可用

---

### 案例 2: kitchen_14_Q05 - Luna喜欢加胡椒的饼干吗

| 字段 | 内容 |
|------|------|
| **问题** | Does Luna like cookies with pepper? |
| **标准答案** | No |
| **模型回答** | Insufficient information to determine Luna's preference for cookies with pepper. |
| **GPT评估** | ❌ 错误 |
| **标注推理** | 两人在吃饼干时，Grace曾说她想加点胡椒粉，然后Luna很惊讶地说：胡椒粉？你确定？言下之意就是她觉得这样的搭配很奇怪。后来Grace问Luna喜不喜欢加胡椒粉，Luna犹豫了一下之后说：我觉得可以吧。没有正面回答喜不喜欢，只是说可以这么做。因此Luna应该是不喜欢往饼干里加胡椒粉的。 |

#### 错误根因分析

**1. 检索完全失败**：
- 检索 Query: "Does Luna like cookies with pepper?"
- 返回结果：只有 CLIP_1 的信息（吃水果的场景）
- 实际相关的信息应该在更后面的 Clip（第80个Clip左右）

**2. 时间戳问题**：
- 问题的 Before Clip = 80
- 这意味着相关信息在视频很后面
- 但检索只返回了最前面的 Clip

**3. 图谱信息检查**：
需要检查 CLIP_80 左右是否有 "cookies" 和 "pepper" 的记录。

**诊断结论**：`RETRIEVAL_FAILED` 或 `GRAPH_MISSING`
- 需要进一步验证图谱中是否有相关信息
- 如果有但没检索到 → RETRIEVAL_FAILED
- 如果没有 → GRAPH_MISSING

---

### 案例 3: living_room_06_Q01 - 三个人喝什么饮料

| 字段 | 内容 |
|------|------|
| **问题** | What are the drinks for the three people? |
| **标准答案** | Coffee. |
| **模型回答** | The three available drinks are coffee, milk, and orange juice... |
| **GPT评估** | ❌ 错误 |
| **标注推理** | Lily笑着说大家都没什么精神，喝点儿提神的，由此可见是喝咖啡 |

#### 错误根因分析

**1. 图谱信息检查**：
CLIP_0 的记录：
```
"<character_0>: 'Hey, robot.'"
"<character_0>: 'What drinks are available?'"
"<character_1>: 'Coffee, milk, orange juice.'"
```

**发现**：
- 图谱只记录了**可选饮料列表**
- 没有记录 Lily 说的 "大家都没什么精神，喝点儿提神的"
- 没有记录他们**最终选择了**哪种饮料

**2. 问题理解偏差**：
- 问题问的是 "drinks **for** the three people"（三个人喝的是什么）
- 但图谱只有 "drinks **available**"（有什么可选）
- LLM 正确理解了问题，但图谱信息不足

**诊断结论**：`GRAPH_MISSING`
- 图谱缺少"选择/决定"的关键信息
- 需要记录角色的选择动作，而不仅是选项列表

---

## 二、错误类型总结

基于以上深度分析，错误主要分为以下几类：

### 2.1 图谱信息缺失 (GRAPH_MISSING)

**表现**：
- 图谱记录了**事实**（什么东西在哪里），但缺少**选择/偏好**信息
- 图谱记录了**对话内容**，但缺少**言外之意**的推理

**示例**：
- 记录了"有烧烤味和番茄味薯片"，但没记录"她拿了番茄味"
- 记录了"可选饮料有咖啡、牛奶、橙汁"，但没记录"他们选了咖啡"

**根本原因**：
Baseline 的视频理解模型（M3-Agent-Memorization）倾向于描述**可观察的事实**，
但对于需要**推理**才能得出的信息（如偏好、选择、意图）记录不足。

### 2.2 角色映射失败 (CHARACTER_MAPPING_FAILED)

**表现**：
- 问题中使用人名（Luna, Grace, Lily）
- 图谱中使用 ID（character_0, voice_57）
- 检索无法建立名称到ID的映射

**示例**：
- 搜索 "What is the name of <character_0>" 返回空
- 搜索 "Luna character id" 返回空

**根本原因**：
图谱没有显式存储**角色名称到ID的映射表**，这个信息散布在对话中（如果角色自我介绍或被他人称呼），
但检索系统无法可靠地找到这些信息。

### 2.3 检索失败 (RETRIEVAL_FAILED)

**表现**：
- 相关信息确实在图谱中
- 但向量相似度检索没有找到

**可能原因**：
- Query 和图谱内容的语义表达不同
- 相关信息分散在多个节点中
- 检索只返回 Top-K 结果，相关内容排名靠后

### 2.4 LLM推理错误 (LLM_REASONING_ERROR)

**表现**：
- 相关信息已检索到并呈现给LLM
- 但LLM的推理逻辑有误

**示例**：
- 看到"Barbecue"先被提到，就认为是最爱
- 没有理解"找到"和"选择"的区别

---

## 三、改进建议

### 3.1 针对 GRAPH_MISSING

**短期方案**：
- 在视频理解阶段，增加"选择/决定/偏好"类型的信息提取
- 添加专门的 Prompt 引导模型记录"角色做出的选择"

**长期方案**：
- 引入 **Procedure 节点**（NSTF方案）记录动作序列
- 通过动作序列可以推理出"最终选择了什么"

### 3.2 针对 CHARACTER_MAPPING_FAILED

**短期方案**：
- 构建显式的**角色名称-ID映射表**
- 在图谱构建完成后，提取所有对话中的人名，建立映射

**长期方案**：
- 在 Semantic 节点中添加 `Equivalence` 关系
- 如：`character_0 = Luna = 穿白裙子的女生`

### 3.3 针对 RETRIEVAL_FAILED

**短期方案**：
- 增加检索结果数量（Top-K）
- 使用**多轮检索**，允许LLM迭代搜索

**长期方案**：
- 结合**关键词检索**和**向量检索**
- 对于名字、物品名等，使用精确匹配

### 3.4 针对 LLM_REASONING_ERROR

**短期方案**：
- 优化 System Prompt，强调"区分描述和选择"
- 添加 few-shot 示例

**长期方案**：
- 使用 Chain-of-Thought 提示
- 对关键问题类型进行专门训练

---

## 四、待执行的深度分析

以上是基于3个案例的初步分析。要获得完整的统计数据，请执行：

```bash
cd /data1/rongjiej/NSTF_MODEL
python analysis/scripts/error_diagnosis.py
```

这将：
1. 遍历所有视频的错误问答
2. 加载对应的图谱文件
3. 检查答案关键词是否在图谱中
4. 生成完整的诊断报告

---

## 五、更多错误案例分析

### 案例 4: study_07_Q03 - Lily吃了几种水果

| 字段 | 内容 |
|------|------|
| **问题** | How many kinds of fruits did Lily eat? |
| **标准答案** | 3 |
| **模型回答** | (空) |
| **GPT评估** | ❌ 错误 |
| **标注推理** | Lily曾说非常喜欢吃芒果，但因为爸爸过敏所以没能经常吃，然后吃了芒果。说过想吃葡萄，然后去洗来吃，还说过西瓜很甜，然后吃了一口。所以她吃过三种水果。 |

#### 错误根因分析

**检索过程**：
1. 第1轮: "Lily ate types of fruits" → 返回CLIP_0和CLIP_6（没有水果信息）
2. 第3轮: "What is the character id of Lily?" → 返回7条结果
3. 第4轮: "<character_1> eat fruits types" → 返回1条

**问题**：
- 水果相关信息在 CLIP_69 左右（Before Clip = 69）
- 但检索只返回了最前面的 Clip
- **时间跨度问题**：相关信息太靠后，向量检索没有命中

**诊断结论**：`RETRIEVAL_FAILED` + `GRAPH_MISSING`
- 需要验证图谱中是否有芒果/葡萄/西瓜的记录

---

### 案例 5: living_room_06_Q05 - Sophie最近是否感到疲惫

| 字段 | 内容 |
|------|------|
| **问题** | Is Sophie tired of life lately? |
| **标准答案** | Yes. |
| **模型回答** | (空) |
| **GPT评估** | ❌ 错误 |
| **标注推理** | Sophie则表示她今天压力很大，因为要给客户交付一个自己独立完成的项目设计。因此她很累。 |

#### 错误根因分析

**检索过程**：
1. 第1轮: "Sophie's recent feelings or emotions towards life" → 1条
2. 第5轮: "What is the character id of the woman wearing a pink cropped sweatshirt?" → 1条

**问题**：
- 问题问的是情感状态，需要从对话中推理
- 检索返回的信息可能没有包含"压力大"、"项目设计"等关键词
- **隐式推理**：需要从"压力大"推理出"累"

**诊断结论**：`GRAPH_MISSING` 或 `RETRIEVAL_FAILED`
- 图谱可能没有记录Sophie的情感表达
- 或者记录了但检索没有命中

---

## 六、错误模式统计（基于样本）

根据以上5个典型案例，错误模式分布如下：

| 错误类型 | 数量 | 占比 | 典型案例 |
|----------|------|------|----------|
| GRAPH_MISSING | 3 | 60% | Q01(薯片), Q01(饮料), Q05(情感) |
| CHARACTER_MAPPING_FAILED | 2 | 40% | Q01(薯片), Q03(水果) |
| RETRIEVAL_FAILED | 2 | 40% | Q03(水果), Q05(情感) |
| LLM_REASONING_ERROR | 1 | 20% | Q01(薯片-误选Barbecue) |

*注：一个案例可能有多个错误类型*

---

## 七、附录：关键发现

### 7.1 Baseline 图谱的局限性

从 kitchen_14 的图谱分析可以看到：

```
总节点数: 2391
Episodic 节点: 1168  
Semantic 节点: 1183
Voice 节点: 40
Clip 数量: 83
```

- **Episodic 节点**主要是**事实描述**（谁在哪里、做什么）
- **Semantic 节点**主要是**场景总结**（整体氛围、可能的背景）
- **缺少**：选择、偏好、意图、因果关系

### 7.2 Character Mapping 的现状

```
character_0: voice_224, voice_760, ... (+35个)
character_1: voice_625  (只有1个)
```

- character_0 对应多个 voice 节点（可能是主角）
- 但没有存储 character_0 = "Luna" 这样的映射

### 7.3 检索系统的行为

从对话历史可以看到：
- 第一次检索往往返回**最相似但不一定最相关**的内容
- 当检索角色名时经常返回空（因为图谱中没有直接的名称映射）
- LLM 需要多轮迭代才能获取足够信息

### 7.4 时间跨度问题

- 长视频(80+ Clips)中，相关信息可能在任意位置
- 向量检索的 Top-K 结果往往集中在某些区域
- 当问题涉及视频后半部分时，检索更容易失败

---

## 八、NSTF 如何解决这些问题

基于以上分析，NSTF (Neural-Symbolic Task Flow) 的改进方向：

### 8.1 Procedure 节点

**解决问题**：GRAPH_MISSING (选择/偏好信息缺失)

通过记录 **Procedure（程序/流程）** 节点：
```
Procedure: "Luna finds her favorite chips"
  - Step 1: Opens cabinet
  - Step 2: Sees barbecue flavor
  - Step 3: Sees tomato flavor  
  - Step 4: Takes tomato (final choice) ← 关键信息
```

### 8.2 Character 显式映射

**解决问题**：CHARACTER_MAPPING_FAILED

在图谱中显式存储：
```
Equivalence:
  - character_0 = "Luna" = "穿白裙子的女生"
  - character_1 = "Grace" = "穿棕色衣服的女生"
```

### 8.3 语义链接增强

**解决问题**：RETRIEVAL_FAILED

为相关节点建立语义链接：
```
Node "Luna likes mango" 
  → RELATED_TO → Node "Luna eats fruit"
  → RELATED_TO → Node "Lily's father allergic"
```

### 8.4 时序索引

**解决问题**：时间跨度问题

为问题类型添加时序提示：
```
If question about "preference" → 搜索全部 Clips
If question about "location" → 搜索最近 Clips
```
