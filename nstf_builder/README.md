# nstf_builder 模块

**NSTF 图谱构建器** - 实现 NS-Mem 论文 SK-Gen 算法

---

## 一、概述

本模块从 Baseline Memory Graph 的 Episodic 节点中蒸馏程序性知识，生成 Logic Layer (Procedure 节点)。

### 核心流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SK-Gen 蒸馏流程                              │
│                                                                     │
│   Baseline Graph          Phase 1: Distillation           NSTF Graph│
│   ┌───────────┐    ┌───────────────────────────┐    ┌───────────┐  │
│   │ Episodic  │───►│ 1. LLM 检测程序性知识     │───►│ Procedure │  │
│   │ Nodes     │    │ 2. 提取 DAG 结构         │    │ Nodes     │  │
│   ├───────────┤    │ 3. 生成双层 Index        │    ├───────────┤  │
│   │ Semantic  │    │ 4. 建立 Episodic Links   │    │ +DAG      │  │
│   │ Nodes     │    │ 5. Procedure 融合        │    │ +Index    │  │
│   └───────────┘    └───────────────────────────┘    │ +Links    │  │
│                                                      └───────────┘  │
│                    Phase 2: Incremental Maintenance                 │
│                    ┌───────────────────────────┐                    │
│     New Obs ──────►│ Match → Gate → EMA Update │                    │
│                    └───────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 支持的知识类型

| 类型 | 说明 | 示例 |
|-----|------|------|
| `task` | 任务流程 | 把水果放进冰箱 |
| `habit` | 重复行为模式 | person_1 总是先检查物品再存放 |
| `trait` | 人物性格特征 | person_1 很有条理、乐于助人 |
| `social` | 人际互动模式 | person_1 和 person_2 一起讨论购物清单 |

---

## 二、模块结构

```
nstf_builder/
├── __init__.py              # 模块入口
├── builder.py               # 静态构建器 (NSTFBuilder)
├── incremental_builder.py   # 增量构建器 (IncrementalNSTFBuilder) ⭐ 推荐
├── extractor.py             # LLM 程序结构提取器 (ProcedureExtractor)
├── dag_fusion.py            # DAG 融合 (DAGFusion, ProcedureFusionManager)
├── episodic_linker.py       # Episodic 链接验证器 (EpisodicLinker)
├── procedure_matcher.py     # Procedure 匹配器 (ProcedureMatcher)
├── character_resolver.py    # 角色 ID 解析器 (CharacterResolver)
├── utils.py                 # 公共工具（embedding 缓存、相似度计算）
├── config/
│   └── default.json         # 默认配置
└── prompts/                 # LLM Prompt 模板目录
```

---

## 三、核心组件

### 3.1 NSTFBuilder (静态构建器)

一次性处理整个视频的所有 Episodic 内容，适用于消融实验。

**流程**:
1. 加载 Baseline Memory Graph
2. 提取所有 Episodic 内容
3. 用 CharacterResolver 解析角色 ID
4. 批量调用 LLM 检测程序性知识
5. 对每个检测到的程序提取详细结构
6. 用 EpisodicLinker 验证和发现更多链接
7. 生成双层 Index Vectors
8. 执行 Procedure 融合

### 3.2 IncrementalNSTFBuilder (增量构建器) ⭐

逐 Clip 处理，支持增量维护，适用于生产环境。

**流程**:
1. 对每个 Clip 调用 LLM 检测并提取结构
2. 用 ProcedureMatcher 匹配已有 Procedure
3. 若匹配：用 EMA 更新 embeddings、合并 DAG 边计数
4. 若不匹配：创建新 Procedure
5. 结束时执行融合和链接验证

**EMA 更新公式** (论文 Eq.9):
```
emb_new = β × emb_old + (1 - β) × emb_obs
其中 β = 0.9 (配置可调)
```

### 3.3 ProcedureExtractor (LLM 提取器)

调用 Gemini LLM 从视频内容中提取程序性知识。

**两阶段提取**:
1. `detect_procedures()`: 批量检测存在哪些程序
2. `extract_structure()`: 对每个程序提取详细 DAG 结构

**主要功能**:
- 支持 task/habit/trait/social 四种知识类型
- 生成多路径 DAG（支持分支和汇聚）
- 提取具体的 objects、locations、participants
- 增强的 JSON 解析（处理 LLM 输出格式问题）

### 3.4 DAGFusion (DAG 融合)

实现论文 Definition 3.3 (Symbolic Structure Fusion)。

**融合步骤**:
1. **Node Alignment**: 用 Hungarian Algorithm 做 step 最优二部匹配
2. **Parameter Pooling**: 贝叶斯方式合并转移概率
3. **Edge Preservation**: 保留所有观测到的替代路径

### 3.5 EpisodicLinker (链接验证器)

验证 LLM 生成的 episodic links，并自动发现额外链接。

**工作原理**:
- 计算 Procedure goal 与每个 Clip content 的 embedding 相似度
- 高于 `verify_threshold` (0.35): 验证 LLM 链接
- 高于 `discover_threshold` (0.30): 自动发现新链接

### 3.6 CharacterResolver (角色解析器)

将 Baseline 图谱中的临时 ID (`<face_0>`, `<voice_1058>`) 替换为统一的 `person_N`。

**数据来源**: Baseline 图谱的 equivalence 节点或 metadata

### 3.7 ProcedureMatcher (匹配器)

增量构建时判断新检测的程序是否应与已有 Procedure 合并。

**多信号融合**:
- goal 语义相似度 (50%)
- type 匹配 (20%)
- 关键动词重叠 (30%)

---

## 四、数据结构规范

### 4.1 NSTF 图谱顶层结构

```python
NSTFGraph = {
    'video_name': str,              # 视频名称
    'dataset': str,                 # 'web' | 'robot'
    
    'procedure_nodes': {            # 核心: Procedure 节点
        '{video}_proc_1': ProcedureNode,
        '{video}_proc_2': ProcedureNode,
        ...
    },
    
    'character_mapping': {          # 角色 ID 映射
        'face_0': 'person_1',
        'voice_1058': 'person_1',
        ...
    },
    
    'metadata': {
        'version': str,
        'created_at': str,
        'num_procedures': int,
        'processing_time': float,
    },
    
    'stats': {
        'total_procedures': int,
        'total_links': int,
        'avg_links_per_proc': float,
    }
}
```

### 4.2 Procedure 节点结构

```python
ProcedureNode = {
    # ===== 基本信息 =====
    'proc_id': str,             # 'kitchen_03_proc_1'
    'type': 'procedure',        # 固定值
    'goal': str,                # 程序目标 (具体描述)
    'description': str,         # 详细描述
    'proc_type': str,           # 'task' | 'habit' | 'trait' | 'social'
    
    # ===== 具体信息 =====
    'objects': List[str],       # 涉及物品: ['melon', 'bottle']
    'locations': List[str],     # 涉及位置: ['refrigerator', 'cabinet']
    'participants': List[str],  # 参与者: ['person_1', 'robot']
    
    # ===== 双层 Index Vectors (论文核心) =====
    'embeddings': {
        'goal_emb': np.ndarray,   # shape: (3072,), 目标向量
        'step_emb': np.ndarray,   # shape: (3072,), 步骤均值向量
        # 增量更新时还有锚定向量:
        'anchor_goal_emb': np.ndarray,
        'anchor_step_emb': np.ndarray,
    },
    
    # ===== Procedural DAG (论文核心) =====
    'dag': {
        'nodes': {
            'START': {'type': 'control'},
            'step_1': {
                'type': 'action',
                'action': str,
                'attributes': {
                    'object': str,
                    'location': str,
                    'actor': str,
                    'triggers': List[str],
                    'outcomes': List[str],
                }
            },
            ...
            'GOAL': {'type': 'control'},
        },
        'edges': [
            {
                'from': 'START',
                'to': 'step_1',
                'count': int,           # 转移计数 N_ij
                'probability': float,   # 转移概率 P(j|i)
            },
            ...
        ]
    },
    
    # ===== 兼容字段 =====
    'steps': List[Dict],        # 步骤列表
    'edges': List[Dict],        # 边列表 (与 dag.edges 相同)
    
    # ===== Episodic Links =====
    'episodic_links': [
        {
            'clip_id': int,
            'relevance': str,       # 'source' | 'update' | 'discovered'
            'similarity': float,
        },
        ...
    ],
    
    # ===== 元数据 =====
    'metadata': {
        'created_at': str,
        'updated_at': str,
        'observation_count': int,   # 观测次数
        'source_clips': List[int],
        'version': str,
    }
}
```

---

## 五、配置参数

配置文件: `config/default.json`

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| `max_procedures` | 5 | 每视频最多 Procedure 数 |
| `batch_size` | 40 | LLM 每批处理 clip 数 |
| `llm_model` | gemini-2.5-flash | LLM 模型 |
| `embedding_model` | text-embedding-3-large | Embedding 模型 (3072 维) |
| `verify_threshold` | 0.35 | 验证链接的相似度阈值 |
| `discover_threshold` | 0.30 | 发现链接的相似度阈值 |
| `max_links_per_proc` | 10 | 每 Procedure 最多链接数 |
| `enable_fusion` | true | 是否启用融合 |
| `fusion_similarity_threshold` | 0.80 | Procedure 融合阈值 |
| `ema_beta` | 0.9 | EMA 权重 β |
| `drift_threshold` | 0.7 | 漂移检测阈值 |

---

## 六、使用方式

### 6.1 命令行构建

```bash
# 工作目录: NSTF_MODEL
cd /data1/rongjiej/NSTF_MODEL

# 增量构建（推荐）
python experiments/build_nstf.py --dataset robot --mode incremental --force

# 静态构建
python experiments/build_nstf.py --dataset robot --mode static --force

# 构建指定视频
python experiments/build_nstf.py --dataset robot --videos kitchen_03 --mode incremental --force
```

### 6.2 Python API

```python
from nstf_builder import NSTFBuilder, IncrementalNSTFBuilder

# 静态构建
builder = NSTFBuilder(debug=True)
result = builder.build('kitchen_03', dataset='robot')

# 增量构建
inc_builder = IncrementalNSTFBuilder(debug=True)
result = inc_builder.build('kitchen_03', dataset='robot')

# 查看结果
print(f"生成 {result['stats']['total_procedures']} 个 Procedure")
```

### 6.3 输出位置

| 模式 | 输出路径 |
|-----|---------|
| static | `data/nstf_graphs/{dataset}/{video}_nstf.pkl` |
| incremental | `data/nstf_graphs/{dataset}/{video}_nstf.pkl` |

---

## 七、图谱分析

构建完成后，使用分析工具检查图谱质量:

```bash
python -m analysis_graph.analyze_nstf kitchen_03 --dataset robot
```

分析报告位置: `analysis_graph/reports/{video}_{dataset}_report.md`

报告内容:
- 字段填充率检查
- proc_type 分布
- DAG 结构统计（分支/线性）
- 边转移计数分析
- Episodic 覆盖率
- Goal 质量评估

---

## 八、常见问题

### Q1: 图谱为空（0 个 Procedure）

**原因**: LLM 未检测到程序性知识

**排查**:
```python
builder = NSTFBuilder(debug=True)
result = builder.build('video_name', dataset='robot')
# 查看日志中的 "检测到: N" 信息
```

### Q2: Character ID 未解析

**症状**: 内容中仍有 `<face_0>`, `<voice_1058>`

**原因**: Baseline 图谱中无 equivalence 节点

### Q3: JSON 解析失败

**症状**: `⚠️ JSON解析失败: ...`

**说明**: LLM 返回的 JSON 格式有问题。`extractor.py` 已实现增强解析（处理尾随逗号等常见问题）。若仍失败，该 clip 会被跳过，不影响整体构建。

### Q4: DAG 都是线性的

**说明**: 单个 clip 通常只能观察到线性序列。多路径 DAG 需要：
1. 多次观测同一 Procedure（增量更新）
2. 不同执行路径的合并（DAG 融合）

---

## 九、相关文档

- [NSTF_CODE_ANALYSIS_V2.md](../docs/NSTF_CODE_ANALYSIS_V2.md) - 代码分析与修复记录
- [analysis_graph/README.md](../analysis_graph/README.md) - 图谱分析工具文档
