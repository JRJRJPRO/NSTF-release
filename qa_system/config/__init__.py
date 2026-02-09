# -*- coding: utf-8 -*-
"""
配置模块

支持三种运行模式:
1. baseline: M3-Agent 原始检索
2. nstf_full: 完整 NSTF 检索 + Logic Layer
3. ablation_*: 消融实验变体
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal

CONFIG_DIR = Path(__file__).parent


# ==================== 模式定义 ====================

QAMode = Literal["baseline", "nstf_full", "ablation_prototype", "ablation_structure"]


# ==================== 分离的检索配置 ====================

@dataclass
class BaselineConfig:
    """Baseline 模式配置 (M3-Agent 原始)"""
    threshold: float = 0.3              # 相似度阈值
    topk: int = 10                      # 检索 Top-K
    mem_wise: bool = False              # 是否全局检索


@dataclass
class NSTFConfig:
    """NSTF 模式配置"""
    # Procedure 匹配
    threshold: float = 0.35             # Procedure 匹配阈值（多粒度加权后）
    min_confidence: float = 0.30        # 最低置信度（低于此值触发 fallback）
    max_procedures: int = 3             # 最大返回 Procedure 数
    
    # Fallback 配置
    topk_baseline: int = 10             # Fallback 时的 baseline topk
    threshold_baseline: float = 0.3     # Baseline 阈值
    
    # 功能开关
    include_episodic_evidence: bool = True   # 是否返回 episodic 证据
    use_reranking: bool = False              # Type-Aware Re-ranking（暂未实现）
    use_dag_paths: bool = True               # 是否使用 DAG 多路径


@dataclass
class QAConfig:
    """问答系统配置"""
    
    # === 运行模式 ===
    # "baseline": M3-Agent 原始检索
    # "nstf_full": 完整 NSTF 检索 + Logic Layer
    # "ablation_prototype": 消融 - 无结构
    # "ablation_structure": 消融 - 有结构无推理
    mode: str = "baseline"
    
    # === 检索配置 ===
    topk: int = 10                      # 检索Top-K
    threshold: float = 0.05             # 相似度阈值（NSTF模式）
    threshold_baseline: float = 0.3     # Baseline相似度阈值
    total_round: int = 5                # 最大对话轮数
    batch_size: int = 4                 # 批处理大小
    
    # === 废弃字段（保留兼容性）===
    ablation_mode: Optional[str] = None
    retrieval_strategy: str = 'clip_level'
    
    # === NSTF 专用配置 ===
    nstf_threshold: float = 0.35
    nstf_min_confidence: float = 0.30
    nstf_max_procedures: int = 3
    nstf_include_evidence: bool = True
    nstf_use_reranking: bool = False
    nstf_use_dag_paths: bool = True
    
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
            'mode': self.mode,
            'topk': self.topk,
            'threshold': self.threshold,
            'threshold_baseline': self.threshold_baseline,
            'total_round': self.total_round,
            'batch_size': self.batch_size,
            'llm_source': self.llm_source,
            'llm_model': self.llm_model,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'max_tokens': self.max_tokens,
            'gpt_model': self.gpt_model,
            'eval_timeout': self.eval_timeout,
            # NSTF 配置
            'nstf_threshold': self.nstf_threshold,
            'nstf_min_confidence': self.nstf_min_confidence,
            'nstf_max_procedures': self.nstf_max_procedures,
            'nstf_include_evidence': self.nstf_include_evidence,
            'nstf_use_reranking': self.nstf_use_reranking,
            'nstf_use_dag_paths': self.nstf_use_dag_paths,
        }
    
    def get_baseline_config(self) -> 'BaselineConfig':
        """获取 Baseline 配置"""
        return BaselineConfig(
            threshold=self.threshold_baseline,
            topk=self.topk,
        )
    
    def get_nstf_config(self) -> 'NSTFConfig':
        """获取 NSTF 配置"""
        return NSTFConfig(
            threshold=self.nstf_threshold,
            min_confidence=self.nstf_min_confidence,
            max_procedures=self.nstf_max_procedures,
            topk_baseline=self.topk,
            threshold_baseline=self.threshold_baseline,
            include_episodic_evidence=self.nstf_include_evidence,
            use_reranking=self.nstf_use_reranking,
            use_dag_paths=self.nstf_use_dag_paths,
        )
    
    def save(self, path: str):
        """保存配置到JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


# ==================== 预定义配置 ====================

# 三种主要运行模式的配置
MODE_CONFIGS = {
    'baseline': QAConfig(
        mode='baseline',
        threshold_baseline=0.3,
        topk=10,
    ),
    'nstf_full': QAConfig(
        mode='nstf_full',
        nstf_threshold=0.30,
        nstf_min_confidence=0.25,
        nstf_max_procedures=3,
        nstf_include_evidence=True,
        nstf_use_reranking=True,
        nstf_use_dag_paths=True,
    ),
    'ablation_prototype': QAConfig(
        mode='ablation_prototype',
        threshold=0.05,
    ),
    'ablation_structure': QAConfig(
        mode='ablation_structure',
        threshold=0.05,
    ),
}


# 兼容旧版 ABLATION_CONFIGS
ABLATION_CONFIGS = {
    'baseline': MODE_CONFIGS['baseline'],
    'prototype': MODE_CONFIGS['ablation_prototype'],
    'structure': MODE_CONFIGS['ablation_structure'],
    'full_nstf': MODE_CONFIGS['nstf_full'],
}


def get_mode_config(mode: str) -> QAConfig:
    """获取指定模式的配置"""
    if mode in MODE_CONFIGS:
        return MODE_CONFIGS[mode]
    # 兼容旧版 ablation_mode
    if mode in ABLATION_CONFIGS:
        return ABLATION_CONFIGS[mode]
    raise ValueError(f"未知模式: {mode}. 可选: {list(MODE_CONFIGS.keys())}")


def get_ablation_config(mode: str) -> QAConfig:
    """获取指定消融模式的配置（兼容旧版）"""
    if mode not in ABLATION_CONFIGS:
        raise ValueError(f"未知消融模式: {mode}. 可选: {list(ABLATION_CONFIGS.keys())}")
    return ABLATION_CONFIGS[mode]
