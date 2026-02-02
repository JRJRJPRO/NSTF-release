# nstf_builder 模块

NSTF 图谱构建器 V2.2 - 实现 E2P (Episodic-to-Procedural) 算法

## 核心功能

**从 Baseline Memory Graph 的 Episodic 节点中提取程序性知识，生成 Procedure 节点**

- **输入**: Baseline 图谱中的 Episodic 节点（原始事件记录）
- **输出**: 新创建的 Procedure 节点（含 episodic_links 追溯链接）

## 两种构建模式

### 1. 静态构建 (NSTFBuilder)
一次性处理所有 clips，用于消融实验。

```python
from nstf_builder import NSTFBuilder
builder = NSTFBuilder(debug=True)
result = builder.build("kitchen_03", "robot", max_procedures=5)
```

### 2. 增量构建 (IncrementalNSTFBuilder) - 推荐
逐 clip 处理，支持 **Procedure 融合**：
- 语义相似的程序合并到同一 Procedure
- 减少冗余，检索效率更高

```python
from nstf_builder import IncrementalNSTFBuilder
builder = IncrementalNSTFBuilder(debug=True)
result = builder.build("kitchen_03", "robot")
```

## 模块结构

```
nstf_builder/
├── __init__.py              # 模块入口
├── builder.py               # 静态构建器 (NSTFBuilder)
├── incremental_builder.py   # 增量构建器 (IncrementalNSTFBuilder)
├── extractor.py             # 程序结构提取 (LLM)
├── character_resolver.py    # Character ID 解析
├── episodic_linker.py       # Episodic 链接验证
├── procedure_matcher.py     # Procedure 匹配（用于融合）
├── utils.py                 # 公共工具（embedding 缓存）
├── prompts/                 # LLM Prompt 模板
└── config/
    └── default.json         # 默认配置
```

## 核心组件

### CharacterResolver
解析 `<face_N>`, `<voice_N>` 等 ID 为可读名称 (person_1, person_2...)

### EpisodicLinker
验证 LLM 提取的 episodic_links，并通过向量相似度自动发现遗漏的链接

### ProcedureMatcher
用于增量构建时判断新检测到的程序是否应该与已有 Procedure 合并

## 配置参数

| 参数 | 默认值 | 说明 |
|-----|-------|------|
| `max_procedures` | 5 | 每视频最多提取的 Procedure 数（静态模式） |
| `verify_threshold` | 0.35 | 验证 LLM 链接的相似度阈值 |
| `discover_threshold` | 0.30 | 自动发现链接的相似度阈值 |
| `max_links_per_proc` | 10 | 每个 Procedure 最大链接数 |
| `match_threshold` | 0.50 | 增量模式下 Procedure 融合阈值 |

## 命令行使用

```bash
# 增量构建（推荐）
python experiments/build_nstf.py --dataset robot --mode incremental --force

# 静态构建
python experiments/build_nstf.py --dataset robot --mode static --force

# 构建单个视频
python experiments/build_nstf.py --dataset robot --videos kitchen_03 --mode incremental --force
```

## 输出格式

构建结果保存为 pickle 文件：
- 静态模式: `data/nstf_graphs/{dataset}/{video}_nstf.pkl`
- 增量模式: `data/nstf_graphs/{dataset}/{video}_nstf_incremental.pkl`

包含：
```python
{
    'video_name': str,
    'dataset': str,
    'procedure_nodes': {
        'proc_id': {
            'goal': str,
            'steps': List[Dict],
            'episodic_links': List[Dict],  # 追溯链接
            'embeddings': {'goal_emb': ndarray},
            ...
        }
    },
    'character_mapping': Dict,
    'stats': Dict,
}
```
