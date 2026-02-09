# -*- coding: utf-8 -*-
"""
NSTF Environment Setup Module

Handles:
1. Path configuration (from .env)
2. sys.path setup
3. videograph module fix

All other modules should import this module for path configuration.
"""

import os
import sys
from pathlib import Path

# === Core Paths ===
NSTF_MODEL_DIR = Path(__file__).parent.resolve()

# Load .env
from dotenv import load_dotenv
load_dotenv(NSTF_MODEL_DIR / '.env')

# BytedanceM3Agent path (from .env, with fallback)
BYTEDANCE_DIR = Path(os.environ.get('BYTEDANCE_DIR', str(NSTF_MODEL_DIR / 'external' / 'M3Agent')))

# === Common Paths ===
DATA_DIR = NSTF_MODEL_DIR / 'data'
MODELS_DIR = NSTF_MODEL_DIR / 'models'
CONFIGS_DIR = NSTF_MODEL_DIR / 'configs'
EXPERIMENTS_DIR = NSTF_MODEL_DIR / 'experiments'
RESULTS_DIR = NSTF_MODEL_DIR / 'results'


def setup_paths():
    """
    Set up sys.path to enable importing mmagent and other modules.
    Safe to call multiple times.
    """
    if str(NSTF_MODEL_DIR) not in sys.path:
        sys.path.insert(0, str(NSTF_MODEL_DIR))

    if BYTEDANCE_DIR.exists() and str(BYTEDANCE_DIR) not in sys.path:
        sys.path.insert(0, str(BYTEDANCE_DIR))


def setup_videograph():
    """
    Fix videograph module import issue.
    Some internal imports use 'import videograph' directly.
    """
    try:
        import mmagent.videograph
        sys.modules["videograph"] = mmagent.videograph
    except ImportError:
        pass


def setup_all():
    """
    Full initialization: paths + videograph fix.
    Call once in main entry scripts.
    """
    setup_paths()
    setup_videograph()


# Auto-setup on import
setup_paths()
