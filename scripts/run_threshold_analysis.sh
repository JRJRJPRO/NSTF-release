#!/bin/bash
# Retrieval Threshold 分析 - 一键运行脚本

echo "=========================================="
echo "Retrieval Threshold 分析"
echo "=========================================="
echo ""

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || exit 1

echo "📍 工作目录: $PROJECT_ROOT"
echo ""

# 创建输出目录
mkdir -p analysis_results
echo "✅ 创建输出目录: analysis_results/"
echo ""

# 步骤1: 快速分析当前结果
echo "=========================================="
echo "步骤 1/2: 分析当前实验结果"
echo "=========================================="
echo ""
echo "正在运行: python scripts/analyze_current_results.py"
echo ""

python3 scripts/analyze_current_results.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 步骤1完成！"
    echo "   结果文件: analysis_results/current_performance_summary.json"
else
    echo ""
    echo "❌ 步骤1失败！"
    exit 1
fi

echo ""
echo "=========================================="
echo "步骤 2/2: 深度分析 Threshold 影响"
echo "=========================================="
echo ""
echo "⚠️  注意: 此步骤需要调用OpenAI API"
echo "   - 运行时间: 5-15分钟 (取决于问题数量)"
echo "   - API费用: 约$0.1-0.5"
echo ""
read -p "是否继续运行深度分析? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在运行: python scripts/analyze_retrieval_threshold.py"
    echo ""
    
    python3 scripts/analyze_retrieval_threshold.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 步骤2完成！"
        echo "   结果文件: analysis_results/threshold_analysis_robot.json"
    else
        echo ""
        echo "❌ 步骤2失败！"
    fi
else
    echo "⏭️  跳过深度分析"
fi

echo ""
echo "=========================================="
echo "分析完成！"
echo "=========================================="
echo ""
echo "📁 结果文件:"
echo "   - analysis_results/current_performance_summary.json"
echo "   - analysis_results/threshold_analysis_robot.json (如果运行了步骤2)"
echo ""
echo "📖 详细说明:"
echo "   - cat THRESHOLD_ANALYSIS_SUMMARY.md"
echo "   - cat scripts/README_threshold_analysis.md"
echo ""
echo "💡 下一步:"
echo "   1. 查看分析结果: cat analysis_results/current_performance_summary.json"
echo "   2. 根据结果调整threshold (如需要): vi ../BytedanceM3Agent/m3_agent/control.py"
echo "   3. 重新运行实验验证: cd ../BytedanceM3Agent && bash run_nstf_test.sh"
echo ""
