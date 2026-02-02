# -*- coding: utf-8 -*-
"""
NSTF_MODEL 环境设置模块

统一处理:
1. 路径配置（从 .env 读取）
2. sys.path 设置
3. videograph 模块修复

所有其他模块应导入此模块来获取路径配置
"""

import os
import sys
from pathlib import Path

# === 核心路径 ===
# NSTF_MODEL_DIR 通过相对路径确定（本文件在 NSTF_MODEL/ 下）
NSTF_MODEL_DIR = Path(__file__).parent.resolve()

# 加载 .env 环境变量
from dotenv import load_dotenv
load_dotenv(NSTF_MODEL_DIR / '.env')

# BytedanceM3Agent 路径（从 .env 读取，有默认值）
BYTEDANCE_DIR = Path(os.environ.get('BYTEDANCE_DIR', '/data1/rongjiej/BytedanceM3Agent'))

# === 常用路径 ===
DATA_DIR = NSTF_MODEL_DIR / 'data'
MODELS_DIR = NSTF_MODEL_DIR / 'models'
CONFIGS_DIR = NSTF_MODEL_DIR / 'configs'
EXPERIMENTS_DIR = NSTF_MODEL_DIR / 'experiments'
RESULTS_DIR = NSTF_MODEL_DIR / 'results'


def setup_paths():
    """
    设置 sys.path，确保可以导入 mmagent 等模块
    
    调用一次即可，重复调用无副作用
    """
    # 添加 NSTF_MODEL 到路径
    if str(NSTF_MODEL_DIR) not in sys.path:
        sys.path.insert(0, str(NSTF_MODEL_DIR))
    
    # 添加 BytedanceM3Agent 到路径（用于导入 neural_symbolic_experiments 等）
    if str(BYTEDANCE_DIR) not in sys.path:
        sys.path.insert(0, str(BYTEDANCE_DIR))


def setup_videograph():
    """
    修复 videograph 模块导入问题
    
    mmagent 内部有些地方直接 import videograph，需要重定向到 mmagent.videograph
    """
    try:
        import mmagent.videograph
        sys.modules["videograph"] = mmagent.videograph
    except ImportError:
        pass


def setup_all():
    """
    完整初始化：路径 + videograph 修复
    
    建议在主入口脚本中调用一次
    """
    setup_paths()
    setup_videograph()


# 自动执行基本设置（导入时）
setup_paths()
