# Efficiency Experiment

Measures retrieval efficiency: NSTF vs Baseline in terms of retrieval rounds needed.

## Metrics

| Metric | Description |
|--------|-------------|
| avg_rounds | Average retrieval rounds to reach correct answer |
| avg_time_sec | Average time per question (seconds) |
| accuracy | Overall accuracy |

## Usage

```bash
# Run baseline
python experiments/run_qa.py --dataset robot --ablation baseline

# Run NSTF
python experiments/run_qa.py --dataset robot --ablation nstf_level
```

## Expected Results

- NSTF requires fewer retrieval rounds than Baseline
- NSTF accuracy >= Baseline accuracy
