# -*- coding: utf-8 -*-
"""
Prompt 模板加载器

目录结构:
prompts/
├── baseline/           # Baseline 模式 (原始 M3-Agent)
│   ├── system.txt     # System prompt
│   └── instruction.txt # 每轮指令
├── nstf/              # 完整 NSTF 模式
│   ├── system.txt
│   └── instruction.txt
├── ablation/          # 消融实验 (使用 baseline prompt)
│   └── README.md
└── evaluation.txt     # 评估 prompt (所有模式共用)
"""

from pathlib import Path
from typing import Optional

PROMPTS_DIR = Path(__file__).parent


def load_prompt(subdir: str, name: str) -> str:
    """加载指定子目录下的 prompt 模板
    
    Args:
        subdir: 子目录名 (baseline/nstf)
        name: prompt 文件名（不含 .txt 后缀）
        
    Returns:
        prompt 文本内容
    """
    prompt_path = PROMPTS_DIR / subdir / f"{name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt 文件不存在: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_prompt_mode(
    mode: Optional[str] = None,
    ablation_mode: Optional[str] = None, 
    nstf_available: bool = False
) -> str:
    """根据运行模式和 NSTF 可用性确定使用哪个 prompt 目录
    
    Args:
        mode: 新的运行模式 (baseline/nstf_full/ablation_*)
        ablation_mode: 旧的消融模式 (兼容性参数)
        nstf_available: 当前问题是否有 NSTF 图谱可用
        
    Returns:
        prompt 目录名 (baseline 或 nstf)
    """
    # 新 mode 参数优先
    if mode:
        if mode == 'nstf_full' and nstf_available:
            return 'nstf'
        elif mode.startswith('ablation_'):
            return 'baseline'
        elif mode == 'baseline':
            return 'baseline'
    
    # 兼容旧的 ablation_mode 参数
    if ablation_mode in ['baseline', 'prototype', 'structure']:
        return 'baseline'
    
    # 完整 NSTF 模式，且有图谱时使用 nstf prompt
    if nstf_available:
        return 'nstf'
    
    # 默认使用 baseline
    return 'baseline'


def get_system_prompt(
    mode: Optional[str] = None,
    ablation_mode: Optional[str] = None, 
    nstf_available: bool = False
) -> str:
    """获取 system prompt
    
    Args:
        mode: 新的运行模式
        ablation_mode: 旧的消融模式 (兼容性参数)
        nstf_available: 是否有 NSTF 图谱可用
    """
    prompt_mode = get_prompt_mode(mode, ablation_mode, nstf_available)
    return load_prompt(prompt_mode, 'system')


def get_instruction(
    mode: Optional[str] = None,
    ablation_mode: Optional[str] = None, 
    nstf_available: bool = False
) -> str:
    """获取 instruction prompt
    
    Args:
        mode: 新的运行模式
        ablation_mode: 旧的消融模式 (兼容性参数)
        nstf_available: 是否有 NSTF 图谱可用
    """
    prompt_mode = get_prompt_mode(mode, ablation_mode, nstf_available)
    return load_prompt(prompt_mode, 'instruction')


def get_evaluation_prompt() -> str:
    """获取评估 prompt（所有模式共用）"""
    prompt_path = PROMPTS_DIR / "evaluation.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"评估 Prompt 文件不存在: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()
