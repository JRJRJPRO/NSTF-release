# analysis_graph 模块

"""
NSTF 图谱分析工具

使用方法:
    python -m analysis_graph.analyze_nstf kitchen_03 --dataset robot
    python -m analysis_graph.analyze_nstf kitchen_03 --mode incremental --output report.json
"""

from .analyze_nstf import NSTFGraphAnalyzer

__all__ = ['NSTFGraphAnalyzer']
