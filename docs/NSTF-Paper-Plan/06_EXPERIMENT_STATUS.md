# 实验状态与数据格式文档

## 1. 数据格式规范

### 1.1 control.py 期望的数据格式（字典格式）

```json
{
  "video_name": {
    "video_path": "data/videos/robot/video_name.mp4",
    "mem_path": "data/memory_graphs/robot/video_name.pkl",
    "qa_list": [
      {
        "question": "问题内容",
        "answer": "答案内容",
        "question_id": "video_name_Q01",
        "reasoning": "推理说明（可选）",
        "timestamp": "00:18",
        "type": ["Factual Recall"],
        "before_clip": 0
      }
    ]
  }
}
```

### 1.2 关键字段说明

| 字段            | 类型   | 必需 | 说明                |
| --------------- | ------ | ---- | ------------------- |
| `video_name`  | string | ✅   | 顶层键，视频名称    |
| `video_path`  | string | ❌   | 视频文件路径        |
| `mem_path`    | string | ✅   | memory graph路径    |
| `qa_list`     | array  | ✅   | 问答列表            |
| `question`    | string | ✅   | 问题内容            |
| `answer`      | string | ✅   | 标准答案            |
| `question_id` | string | ✅   | 唯一问题ID          |
| `before_clip` | int    | ❌   | 截止clip索引，默认0 |
| `type`        | array  | ❌   | 问题类型列表        |

### 1.3 NSTF图谱格式

```python
# neural_symbolic_experiments/data/nstf_graphs/{video_name}_nstf.pkl
{
    "video_name": "living_room_06",
    "original_graph_path": "...",
    "procedure_nodes": {
        "living_room_06_proc_1": {
            "proc_id": "living_room_06_proc_1",
            "type": "procedure",
            "goal": "Setting up for Yoga",
            "description": "...",
            "steps": ["step1", "step2", ...],
            "temporal_constraints": [...],
            "embeddings": [(text, vector), ...],
            "metadata": {...}
        }
    },
    "metadata": {...}
}
```

### 1.4 结果文件格式 (JSONL)

```json
{
  "id": "question_id",
  "mem_path": "...",
  "question": "...",
  "answer": "标准答案",
  "response": "模型回答",
  "gpt_eval": true/false,
  "conversations": [...],
  "nstf_available": true/false
}
```

---

## 2. 实验进度

### 2.1 已完成实验

| 实验    | 数据集                | 问题数 | Baseline | NSTF | 提升 | 状态    |
| ------- | --------------------- | ------ | -------- | ---- | ---- | ------- |
| 5问验证 | test_questions_5.json | 5      | 60%      | 80%  | +20% | ✅ 完成 |

### 2.2 待运行实验

| 实验       | 数据集             | 问题数 | 预计时间 | 状态      |
| ---------- | ------------------ | ------ | -------- | --------- |
| 小批量验证 | living_room_06_5q  | 5      | ~5分钟   | 🔄 准备中 |
| 中等规模   | living_room_06_16q | 16     | ~15分钟  | 📋 待运行 |
| 大批量     | robot_nstf_subset  | 44     | ~45分钟  | 📋 待运行 |

---

## 3. 可用资源

### 3.1 NSTF图谱

| 视频           | 文件大小 | Procedures数 | 状态          |
| -------------- | -------- | ------------ | ------------- |
| living_room_06 | 115KB    | 4            | ✅ 完整       |
| bedroom_01     | 262B     | 0?           | ⚠️ 可能为空 |
| kitchen_01     | 262B     | 0?           | ⚠️ 可能为空 |

### 3.2 Memory Graphs

路径: `data/memory_graphs/robot/`

---

## 4. 时间与费用估算

### 4.1 时间估算

- 每问题约 1-2 分钟（含推理+搜索+评估）
- 16问: ~15-30 分钟
- 44问: ~45-90 分钟

### 4.2 API费用估算

- GPT-4o 评估: ~$0.01/问题
- 16问: ~$0.16
- 44问: ~$0.44

---

## 5. 故障排查

### 5.1 常见错误

1. **`AttributeError: 'list' object has no attribute 'values'`**

   - 原因: 数据格式错误，使用了列表而非字典
   - 解决: 转换为字典格式（见1.1节）
2. **`ModuleNotFoundError: No module named 'xxx'`**

   - 原因: Python路径未正确设置
   - 解决: 确保 `project_root` 在 `sys.path` 中
3. **`ValueError: setting an array element with a sequence`**

   - 原因: embedding格式不一致
   - 解决: 检查 `get_embedding()` 返回值类型

---

*最后更新: 2026-01-29*
