# 实验执行计划

## 1. 当前状态检查清单

### 1.1 代码状态

| 文件 | 状态 | 说明 |
|------|------|------|
| `generate_procedure_graph.py` | ✅ 已修复 | ProcedureNode 初始化参数已修正 |
| `run_qa_nstf.py` | ✅ 已修改 | 添加消融实验支持 |
| `nstf/schemas.py` | ✅ 无需修改 | 定义正确 |
| `nstf/embeddings.py` | ✅ 无需修改 | CLIP 1536-dim |

### 1.2 待验证项

- [ ] 图生成测试 (clip 0-2) 是否成功
- [ ] 生成的 ProcedureNode 是否有正确的 `symbolic_graph`
- [ ] QA 是否能正确读取符号结构

## 2. 实验执行步骤

### Step 1: 验证图生成 (5分钟)

```bash
# 检查测试日志
tail -100 /tmp/gen_test2.log

# 如果成功，检查生成的 pkl 文件
ls -la neural_symbolic_experiments/graphs/
```

**预期输出：**
- 无 `__init__() got an unexpected keyword argument` 错误
- 生成 `robot_nstf.pkl` 文件
- 日志显示 "Created X procedure nodes"

### Step 2: 检查生成的图结构 (10分钟)

```python
# 在 Python 中检查
import pickle
with open("neural_symbolic_experiments/graphs/robot_nstf.pkl", "rb") as f:
    G = pickle.load(f)

# 检查 procedure 节点
procedure_nodes = [n for n in G.nodes if getattr(n, 'type', '') == 'procedure']
print(f"Procedure nodes: {len(procedure_nodes)}")

# 检查第一个 procedure 节点的结构
if procedure_nodes:
    p = procedure_nodes[0]
    print(f"Has symbolic_graph: {hasattr(p, 'symbolic_graph')}")
    print(f"symbolic_graph type: {type(getattr(p, 'symbolic_graph', None))}")
    if hasattr(p, 'symbolic_graph') and p.symbolic_graph:
        dag = p.symbolic_graph
        print(f"DAG steps: {len(dag.get('steps', []))}")
        print(f"DAG edges: {len(dag.get('edges', []))}")
```

### Step 3: 完整图生成 (30-60分钟)

```bash
cd BytedanceM3Agent

# 激活环境
source ../BytedanceEnv/bin/activate

# 完整生成 (跳过 CLIP 避免 SSL 错误)
nohup python scripts/generate_procedure_graph.py \
    --clip_range all \
    --no-clip \
    --output neural_symbolic_experiments/graphs/robot_nstf_full.pkl \
    > /tmp/gen_full.log 2>&1 &

# 监控进度
tail -f /tmp/gen_full.log
```

### Step 4: 运行 QA 测试 (20分钟)

```bash
# 完整版 (Full NSTF)
python scripts/run_qa_nstf.py \
    --graph neural_symbolic_experiments/graphs/robot_nstf_full.pkl \
    --questions neural_symbolic_experiments/data/qa_test.json \
    > results/qa_full.log 2>&1

# Baseline (无符号)
python scripts/run_qa_nstf.py \
    --graph neural_symbolic_experiments/graphs/robot_nstf_full.pkl \
    --questions neural_symbolic_experiments/data/qa_test.json \
    --ablation baseline \
    > results/qa_baseline.log 2>&1

# +Symbolic (有符号，无约束推理)
python scripts/run_qa_nstf.py \
    --graph neural_symbolic_experiments/graphs/robot_nstf_full.pkl \
    --questions neural_symbolic_experiments/data/qa_test.json \
    --ablation symbolic \
    > results/qa_symbolic.log 2>&1
```

### Step 5: 收集结果

```bash
# 创建结果目录
mkdir -p results/ablation

# 提取准确率
grep "Accuracy" results/qa_*.log > results/ablation/summary.txt
```

## 3. 预期结果

### 3.1 图生成

| 指标 | 预期值 |
|------|--------|
| Procedure 节点数 | 15-30 |
| 每个节点的 DAG steps | 3-8 |
| Memory Prototype 维度 | 1536 |
| 关联 clip_ids | 2-5 per node |

### 3.2 QA 准确率

| Config | 预期 Accuracy | 备注 |
|--------|--------------|------|
| Baseline | 60-70% | M3-Agent 水平 |
| +Symbolic | 70-80% | 预期提升 5-15% |
| Full NSTF | 75-85% | 约束类问题额外提升 |

## 4. 问题排查

### 4.1 如果图生成失败

**检查项：**
1. LLM API 是否正常工作
   ```bash
   python -c "from m3_agent.llm_api import generate; print(generate('test'))"
   ```

2. 视频数据是否完整
   ```bash
   ls -la data/robot/*.jsonl
   ```

3. Python 路径是否正确
   ```bash
   which python
   python --version
   ```

### 4.2 如果 QA 不使用符号结构

**检查项：**
1. 节点是否有 `symbolic_graph` 属性
2. `_extract_symbolic_info()` 函数是否被调用
3. Prompt 中是否包含 "程序性知识结构"

**调试代码：**
```python
# 在 run_qa_nstf.py 中添加调试输出
def _generate_answer_with_llm(self, ...):
    print(f"DEBUG: use_symbolic={self.use_symbolic}")
    print(f"DEBUG: symbolic_info count={len(symbolic_info)}")
    print(f"DEBUG: prompt preview: {prompt[:500]}")
```

### 4.3 如果准确率没有提升

**可能原因：**
1. 测试问题不需要程序性知识 → 需要添加新测试问题
2. DAG 结构提取质量差 → 检查 LLM prompt
3. 检索阶段没有召回 procedure 节点 → 检查 embedding 质量

## 5. 额外测试问题

为了更好地展示符号结构的优势，建议添加以下类型的测试问题：

### 5.1 步骤顺序类
```json
{
    "question": "红烧肉制作的第三步是什么？",
    "ground_truth": "煸炒五花肉",
    "type": "sequential"
}
```

### 5.2 工具查询类
```json
{
    "question": "做红烧肉需要哪些厨具？",
    "ground_truth": "炒锅、砧板、刀",
    "type": "tools"
}
```

### 5.3 约束推理类
```json
{
    "question": "如果没有炒锅，怎么做红烧肉？",
    "ground_truth": "可以用平底锅或其他深底锅代替",
    "type": "constraint"
}
```

### 5.4 依赖关系类
```json
{
    "question": "焖煮之前需要完成哪些步骤？",
    "ground_truth": "切肉块、焯水、煸炒",
    "type": "dependency"
}
```

## 6. 时间线

| 时间 | 任务 | 产出 |
|------|------|------|
| Day 1 | 验证图生成 + 修复问题 | 确认代码可运行 |
| Day 1-2 | 完整图生成 | robot_nstf_full.pkl |
| Day 2 | QA 测试 + 消融实验 | 实验数据 |
| Day 3 | 结果分析 + 补充测试 | 完整结果表 |
| Day 4-5 | 论文写作 | 初稿 |
| Day 6-7 | 画图 + 修改 | 完整论文 |

## 7. 备选方案

### 如果 LLM 提取效果不好
- 使用预定义的程序模板
- 人工标注少量示例作为 few-shot

### 如果时间紧迫
- 只使用部分视频 (clip 0-10)
- 减少消融实验组数
- 使用模拟数据展示概念

### 如果审稿要求更多 baseline
- 添加 VideoAgent 对比
- 添加纯 Embedding 检索
- 添加纯 LLM (无 Memory) 对比
