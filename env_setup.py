# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

NSTF_MODEL_DIR = Path(__file__).parent.resolve()

from dotenv import load_dotenv
load_dotenv(NSTF_MODEL_DIR / '.env')

BYTEDANCE_DIR = Path(os.environ.get('BYTEDANCE_DIR', str(NSTF_MODEL_DIR / 'external' / 'M3Agent')))

DATA_DIR = NSTF_MODEL_DIR / 'data'
MODELS_DIR = NSTF_MODEL_DIR / 'models'
CONFIGS_DIR = NSTF_MODEL_DIR / 'configs'
EXPERIMENTS_DIR = NSTF_MODEL_DIR / 'experiments'
RESULTS_DIR = NSTF_MODEL_DIR / 'results'


def setup_paths():
    if str(NSTF_MODEL_DIR) not in sys.path:
        sys.path.insert(0, str(NSTF_MODEL_DIR))
    if BYTEDANCE_DIR.exists() and str(BYTEDANCE_DIR) not in sys.path:
        sys.path.insert(0, str(BYTEDANCE_DIR))


def setup_videograph():
    try:
        import mmagent.videograph
        sys.modules["videograph"] = mmagent.videograph
    except ImportError:
        pass


def setup_all():
    setup_paths()
    setup_videograph()


setup_paths()
