# -*- coding: utf-8 -*-
"""
NSTF 问答系统

模块结构:
- prompts/: Prompt模板文件
- config/: 配置文件
- core/: 核心功能模块
  - retriever.py: 检索模块（Baseline/NSTF/消融）
  - evaluator.py: 答案评估模块
  - llm_client.py: LLM客户端封装
- runner.py: 主运行器
"""

from .runner import QARunner

__all__ = ['QARunner']
