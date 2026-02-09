# NSTF: Neural-Symbolic Task Flow for Video Understanding

Official implementation of **"Neural-Symbolic Task Flow: Structured Memory Augmentation for Long-Form Video Question Answering"**.

## Overview

NSTF enhances video memory graphs with structured procedural knowledge through a two-stage pipeline:
1. **NSTF Graph Construction** — Extracts and fuses procedures, character profiles, and episodic links on top of baseline memory graphs.
2. **Structure-Aware QA** — A retrieval-augmented QA system that leverages the enriched graph for multi-type question answering (Factual, Procedural, Character, Constraint).

## Repository Structure

```
NSTF/
├── env_setup.py                  # Environment configuration
├── configs/                      # Global configs
│   ├── memory_config.json
│   └── processing_config.json
├── mmagent/                      # Core video processing modules
│   ├── face_processing.py
│   ├── memory_processing.py
│   ├── videograph.py
│   ├── src/                      # Face detection & clustering
│   └── utils/                    # API clients, embeddings, etc.
├── nstf_builder/                 # NSTF graph construction
│   ├── builder.py                # Static builder
│   ├── incremental_builder.py    # Incremental builder (recommended)
│   ├── extractor.py              # Procedure structure extractor
│   ├── character_resolver.py     # Character ID resolver
│   ├── episodic_linker.py        # Episodic link validator
│   ├── dag_fusion.py             # DAG-based procedure fusion
│   └── procedure_matcher.py      # Procedure matcher
├── qa_system/                    # Question answering system
│   ├── runner.py                 # Unified QA runner
│   ├── core/
│   │   ├── llm_client.py         # LLM client (cloud/local)
│   │   ├── retriever.py          # Baseline retriever
│   │   ├── retriever_nstf.py     # NSTF-enhanced retriever
│   │   ├── hybrid_retriever.py   # Hybrid retrieval
│   │   ├── evaluator.py          # Answer evaluator
│   │   ├── query_classifier.py   # Query type classifier
│   │   └── strategies/           # Retrieval strategies
│   └── prompts/                  # Prompt templates
├── experiments/                  # Experiment entry scripts
│   ├── build_nstf.py             # Build NSTF graphs
│   └── run_qa.py                 # Run QA experiments
├── analysis/                     # Graph & QA analysis tools
├── data/
│   └── annotations/              # QA annotations
│       ├── robot.json
│       └── web.json
├── clip_list/                    # Video clip lists
└── speakerlab/                   # Speaker recognition module
```

## Setup

### Prerequisites

- Python 3.10+
- PyTorch 2.0+
- CUDA-compatible GPU

### Installation

```bash
# Clone the repository
git clone https://github.com/JRJRJPRO/NSTF.git
cd NSTF

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and model paths
```

### Environment Variables

Create a `.env` file in the project root:

```env
# LLM Configuration
CONTROL_LLM_SOURCE=cloud          # cloud or local
CONTROL_LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# GPU Configuration
GPU_DEVICES=0,1,2,3
GPU_MEMORY_UTILIZATION=0.85

# Paths (optional, defaults are relative to project root)
BYTEDANCE_DIR=./external/M3Agent
INSIGHTFACE_HOME=./models/insightface
```

## Usage

### 1. Build NSTF Graphs

```bash
# Incremental build for all robot videos (recommended)
python experiments/build_nstf.py --dataset robot --mode incremental --force

# Build for specific videos
python experiments/build_nstf.py --dataset robot --videos kitchen_03 --mode incremental
```

### 2. Run QA Experiments

```bash
# Baseline
python experiments/run_qa.py --dataset robot --ablation baseline

# NSTF with procedure-level retrieval
python experiments/run_qa.py --dataset robot --ablation nstf_level

# NSTF with node-level retrieval
python experiments/run_qa.py --dataset robot --ablation nstf_node
```

## Data

The QA annotations are provided in `data/annotations/`:
- `robot.json` — Indoor robot scenario questions
- `web.json` — Web video scenario questions

Memory graphs and NSTF graphs (generated artifacts) are excluded from this repository due to size. Use the build scripts above to regenerate them.

## Acknowledgments

This project builds upon [M3-Agent](https://github.com/AIM3-RUC/M3-Agent) by Bytedance Ltd. The `mmagent/` and `speakerlab/` modules are adapted from the original M3-Agent codebase under the Apache 2.0 License.

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

