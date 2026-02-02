#!/bin/bash
# Efficiency 实验 - 完整流程
#
# 使用方法:
#   bash run_experiment.sh          # 完整流程（生成图谱 + 测试 + 分析）
#   bash run_experiment.sh --test   # 只运行测试（假设图谱已生成）
#   bash run_experiment.sh --analyze # 只运行分析（假设测试已完成）

cd /data1/rongjiej/NSTF_MODEL

SCRIPTS_DIR="experiments/efficiency/scripts"
RESULTS_DIR="experiments/efficiency/results"

# 创建结果目录
mkdir -p $RESULTS_DIR

echo "=========================================="
echo "Efficiency 实验 - 完整流程"
echo "=========================================="
echo "视频数量: 20 个 robot 视频"
echo "=========================================="

# 解析参数
SKIP_BUILD=false
SKIP_TEST=false
ONLY_ANALYZE=false

for arg in "$@"; do
    case $arg in
        --test)
            SKIP_BUILD=true
            ;;
        --analyze)
            ONLY_ANALYZE=true
            SKIP_BUILD=true
            SKIP_TEST=true
            ;;
    esac
done

# Step 1: 生成 NSTF 图谱
if [ "$SKIP_BUILD" = false ]; then
    echo ""
    echo "Step 1: 生成 NSTF 图谱..."
    echo "=========================================="
    bash $SCRIPTS_DIR/build_nstf_graphs.sh
    if [ $? -ne 0 ]; then
        echo "NSTF 图谱生成失败!"
        exit 1
    fi
fi

# Step 2: 运行测试
if [ "$SKIP_TEST" = false ]; then
    echo ""
    echo "Step 2a: 运行 Baseline 测试..."
    echo "=========================================="
    bash $SCRIPTS_DIR/run_baseline.sh
    if [ $? -ne 0 ]; then
        echo "Baseline 测试失败!"
        exit 1
    fi
    
    echo ""
    echo "Step 2b: 运行 NSTF 测试..."
    echo "=========================================="
    bash $SCRIPTS_DIR/run_nstf.sh
    if [ $? -ne 0 ]; then
        echo "NSTF 测试失败!"
        exit 1
    fi
fi

# Step 3: 分析结果
echo ""
echo "Step 3: 分析轮次差异..."
echo "=========================================="
python $SCRIPTS_DIR/analyze_rounds.py

echo ""
echo "=========================================="
echo "实验完成!"
echo "=========================================="
echo "结果文件:"
echo "  - Baseline 结果: $RESULTS_DIR/baseline_results.jsonl"
echo "  - NSTF 结果:     $RESULTS_DIR/nstf_results.jsonl"
echo "  - 分析报告:      $RESULTS_DIR/analysis_report.json"
echo "=========================================="
