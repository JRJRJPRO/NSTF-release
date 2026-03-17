# NS-Mem

**Neural-Symbolic Memory Augmentation for Long-Form Video Question Answering**

NS-Mem augments video memory graphs with structured procedural knowledge. It constructs a neural-symbolic task flow (NSTF) over baseline memory graphs by extracting and fusing procedures, character profiles, and episodic links, then performs structure-aware retrieval for multi-type video QA.

## Directory Structure

```
├── env_setup.py            # Environment configuration
├── configs/                # Configuration files
├── nstf_builder/           # NSTF graph construction
├── qa_system/              # QA retrieval and evaluation
├── experiments/            # Entry scripts
├── mmagent/                # Video processing modules
└── data/annotations/       # QA annotation files
```

## Usage

**Build NSTF graphs:**
```bash
python experiments/build_nstf.py --dataset robot --mode incremental --force
```

**Run QA experiments:**
```bash
python experiments/run_qa.py --dataset robot --ablation nstf_level
```

## Requirements

- Python 3.10+
- PyTorch 2.0+
- CUDA-compatible GPU
- API keys configured in `.env`
