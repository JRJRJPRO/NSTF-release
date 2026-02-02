# -*- coding: utf-8 -*-
"""
配置模块
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

CONFIG_DIR = Path(__file__).parent


@dataclass
class QAConfig:
    """问答系统配置"""
    
    # === 检索配置 ===
    topk: int = 2                       # 检索Top-K (与baseline一致)
    threshold: float = 0.05             # 相似度阈值（NSTF模式）
    threshold_baseline: float = 0.3     # Baseline相似度阈值（分析后建议=0.3）
    total_round: int = 5                # 最大对话轮数
    batch_size: int = 4                 # 批处理大小
    
    # === 消融模式 ===
    # None: 完整NSTF
    # 'baseline': 消融A - 纯Baseline，不使用NSTF
    # 'prototype': 消融B - 纯向量检索
    # 'structure': 消融C - 有结构无推理
    ablation_mode: Optional[str] = None
    
    # === 检索策略配置 (V2) ===
    retrieval_strategy: str = 'clip_level'  # 'clip_level', 'node_level', 或 'nstf_level'
    
    # 节点级别策略参数 (基于 parameter_tuning.py 分析结果)
    node_topk: int = 20                     # 节点检索的 topk（分析推荐：15-20 平衡质量与召回）
    node_threshold: float = 0.20            # 节点检索的阈值（分析推荐：0.20 保证 0% 空结果率）
    include_timestamp: bool = True          # 是否返回时间戳
    group_by_clip: bool = True              # 是否按 clip 分组（默认 True 保持兼容）
    include_semantic: bool = False          # 是否包含 semantic 节点
    preserve_clip_order: bool = True        # group 后是否恢复时间顺序
    
    # === NSTF级别策略参数 (基于 Stage 1/2 实验验证) ===
    nstf_threshold: float = 0.30            # Procedure匹配阈值 (从0.40降低，提高命中率)
    nstf_min_confidence: float = 0.25       # 最低置信度（低于此值触发fallback）
    nstf_max_procedures: int = 3            # 最大返回Procedure数
    nstf_include_evidence: bool = True      # 是否返回episodic证据
    
    # === LLM配置 ===
    # 默认值从 .env 读取，.env 未设置时使用 "local"
    llm_source: str = field(default_factory=lambda: os.environ.get('CONTROL_LLM_SOURCE', 'local'))
    llm_model: str = field(default_factory=lambda: os.environ.get('CONTROL_LLM_MODEL', 'M3-Agent-Control'))
    temperature: float = 0.6
    top_p: float = 0.95
    max_tokens: int = 1024              # 与原始代码一致
    
    # === 评估配置 ===
    gpt_model: str = field(default_factory=lambda: os.environ.get('GPT_MODEL', 'gpt-4o-mini'))
    eval_timeout: int = 30              # 评估超时秒数
    
    # === 路径配置 ===
    # 这些会在运行时根据NSTF_MODEL目录设置
    data_dir: Optional[str] = None
    output_dir: Optional[str] = None
    
    @classmethod
    def from_json(cls, path: str) -> 'QAConfig':
        """从JSON文件加载配置，未指定的字段使用 .env 或默认值"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 如果 JSON 中没有指定 llm_source/llm_model，从 .env 读取
        if 'llm_source' not in data or data.get('llm_source') is None:
            data['llm_source'] = os.environ.get('CONTROL_LLM_SOURCE', 'local')
        if 'llm_model' not in data or data.get('llm_model') is None:
            data['llm_model'] = os.environ.get('CONTROL_LLM_MODEL', 'M3-Agent-Control')
        if 'gpt_model' not in data or data.get('gpt_model') is None:
            data['gpt_model'] = os.environ.get('GPT_MODEL', 'gpt-4o-mini')
            
        return cls(**data)
    
    @classmethod
    def load_default(cls) -> 'QAConfig':
        """加载默认配置"""
        default_path = CONFIG_DIR / "default.json"
        if default_path.exists():
            return cls.from_json(str(default_path))
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return {
            'topk': self.topk,
            'threshold': self.threshold,
            'threshold_baseline': self.threshold_baseline,
            'total_round': self.total_round,
            'batch_size': self.batch_size,
            'ablation_mode': self.ablation_mode,
            'llm_source': self.llm_source,
            'llm_model': self.llm_model,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'max_tokens': self.max_tokens,
            'gpt_model': self.gpt_model,
            'eval_timeout': self.eval_timeout,
            # V2 检索策略配置
            'retrieval_strategy': self.retrieval_strategy,
            'node_topk': self.node_topk,
            'node_threshold': self.node_threshold,
            'include_timestamp': self.include_timestamp,
            'group_by_clip': self.group_by_clip,
            'include_semantic': self.include_semantic,
            'preserve_clip_order': self.preserve_clip_order,
            # NSTF级别策略配置
            'nstf_threshold': self.nstf_threshold,
            'nstf_min_confidence': self.nstf_min_confidence,
            'nstf_max_procedures': self.nstf_max_procedures,
            'nstf_include_evidence': self.nstf_include_evidence,
        }
    
    def save(self, path: str):
        """保存配置到JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


# 预定义的消融实验配置
ABLATION_CONFIGS = {
    'baseline': QAConfig(
        ablation_mode='baseline',
        retrieval_strategy='clip_level',  # baseline 使用 clip 级别检索
        threshold=0.3,      # 分析后建议 threshold=0.3
        threshold_baseline=0.3,  # baseline 模式使用 threshold=0.3
    ),
    'prototype': QAConfig(
        ablation_mode='prototype',
        retrieval_strategy='clip_level',
        threshold=0.05,
    ),
    'structure': QAConfig(
        ablation_mode='structure',
        retrieval_strategy='clip_level',
        threshold=0.05,
    ),
    'full_nstf': QAConfig(
        ablation_mode=None,
        retrieval_strategy='clip_level',
        threshold=0.05,
    ),
    # 节点级别检索配置 (参数基于 parameter_tuning.py 分析结果)
    'nstf_node': QAConfig(
        ablation_mode=None,
        retrieval_strategy='node_level',
        node_topk=20,           # 分析推荐: 20 (平衡召回与质量)
        node_threshold=0.20,    # 分析推荐: 0.20 (保证 0% 空结果率)
        include_timestamp=True,
        group_by_clip=True,
        include_semantic=False,
        preserve_clip_order=True,
    ),
    # NSTF级别检索配置 (基于 Stage 1/2 实验验证)
    'nstf_level': QAConfig(
        ablation_mode=None,
        retrieval_strategy='nstf_level',
        nstf_threshold=0.30,        # Stage 1验证: 降低阈值提高命中率
        nstf_min_confidence=0.25,   # 极低置信度触发fallback
        nstf_max_procedures=3,
        nstf_include_evidence=True,
    ),
}


def get_ablation_config(mode: str) -> QAConfig:
    """获取指定消融模式的配置"""
    if mode not in ABLATION_CONFIGS:
        raise ValueError(f"未知消融模式: {mode}. 可选: {list(ABLATION_CONFIGS.keys())}")
    return ABLATION_CONFIGS[mode]
