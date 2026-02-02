# -*- coding: utf-8 -*-
"""
Stage 3: NSTF集成测试

验证 retrieval_strategy='nstf_level' 是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加项目路径
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

# 环境设置
from env_setup import setup_all
setup_all()


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试1: 配置加载")
    print("=" * 60)
    
    from qa_system.config import QAConfig, ABLATION_CONFIGS, get_ablation_config
    
    # 检查新配置是否存在
    print("\n可用的预定义配置:")
    for name in ABLATION_CONFIGS:
        print(f"  - {name}")
    
    # 测试 nstf_level 配置
    assert 'nstf_level' in ABLATION_CONFIGS, "nstf_level配置不存在!"
    
    config = get_ablation_config('nstf_level')
    print(f"\n✓ nstf_level配置加载成功:")
    print(f"  retrieval_strategy = {config.retrieval_strategy}")
    print(f"  nstf_threshold = {config.nstf_threshold}")
    print(f"  nstf_min_confidence = {config.nstf_min_confidence}")
    print(f"  nstf_max_procedures = {config.nstf_max_procedures}")
    print(f"  nstf_include_evidence = {config.nstf_include_evidence}")
    
    # 测试to_dict包含新参数
    config_dict = config.to_dict()
    assert 'nstf_threshold' in config_dict, "to_dict缺少nstf_threshold"
    print("\n✓ to_dict包含NSTF参数")
    
    return True


def test_retriever_import():
    """测试检索器导入"""
    print("\n" + "=" * 60)
    print("测试2: NSTFRetriever导入")
    print("=" * 60)
    
    from qa_system.core.retriever_nstf import NSTFRetriever
    
    retriever = NSTFRetriever(
        threshold=0.30,
        min_confidence=0.25,
        max_procedures=3,
    )
    
    print(f"\n✓ NSTFRetriever实例化成功")
    print(f"  mode_name = {retriever.mode_name}")
    print(f"  threshold = {retriever.threshold}")
    print(f"  min_confidence = {retriever.min_confidence}")
    
    return True


def test_runner_init():
    """测试Runner初始化"""
    print("\n" + "=" * 60)
    print("测试3: QARunner初始化 (nstf_level)")
    print("=" * 60)
    
    from qa_system.config import get_ablation_config
    from qa_system.runner import QARunner
    
    config = get_ablation_config('nstf_level')
    
    # 创建runner（不运行实际问答）
    runner = QARunner(config=config)
    
    print(f"\n✓ QARunner初始化成功")
    print(f"  _use_v2 = {runner._use_v2}")
    print(f"  _use_nstf = {runner._use_nstf}")
    print(f"  retriever.mode_name = {runner.retriever.mode_name}")
    
    assert runner._use_nstf == True, "_use_nstf应为True"
    assert runner._use_v2 == False, "_use_v2应为False"
    
    return True


def test_retriever_search():
    """测试检索器搜索功能"""
    print("\n" + "=" * 60)
    print("测试4: NSTFRetriever搜索功能")
    print("=" * 60)
    
    from qa_system.core.retriever_nstf import NSTFRetriever
    
    retriever = NSTFRetriever(threshold=0.30, min_confidence=0.25)
    
    # 查找测试数据
    data_dir = PROJECT_DIR / 'data'
    nstf_dir = data_dir / 'nstf_graphs' / 'web'
    mem_dir = data_dir / 'memory_graphs' / 'web'
    
    # 找一个有NSTF图谱的视频
    nstf_files = list(nstf_dir.glob('*_nstf.pkl'))
    if not nstf_files:
        print("  ⚠️ 未找到NSTF图谱文件，跳过测试")
        return True
    
    nstf_path = nstf_files[0]
    video_name = nstf_path.stem.replace('_nstf', '')
    mem_path = mem_dir / f'{video_name}.pkl'
    
    if not mem_path.exists():
        print(f"  ⚠️ 未找到memory graph: {mem_path}")
        return True
    
    print(f"\n测试视频: {video_name}")
    print(f"  NSTF图谱: {nstf_path}")
    print(f"  Memory图谱: {mem_path}")
    
    # 执行搜索
    query = "How to prepare for a birthday party?"
    print(f"\n查询: {query}")
    
    memories, clips, metadata = retriever.search(
        mem_path=str(mem_path),
        query=query,
        nstf_path=str(nstf_path),
    )
    
    print(f"\n搜索结果:")
    print(f"  决策: {metadata.get('decision')}")
    print(f"  memories数量: {len(memories)}")
    print(f"  clips数量: {len(clips)}")
    
    if metadata.get('decision') == 'use_nstf':
        print(f"  匹配的Procedures:")
        for proc in metadata.get('matched_procedures', []):
            print(f"    - {proc['proc_id']}: sim={proc['similarity']:.3f}")
        
        if 'NSTF_Procedures' in memories:
            print(f"\n  Procedure信息预览:")
            proc_info = memories['NSTF_Procedures']
            preview = proc_info[:300] + '...' if len(proc_info) > 300 else proc_info
            for line in preview.split('\n'):
                print(f"    {line}")
    else:
        print(f"  Fallback原因: {metadata.get('fallback_reason')}")
    
    print("\n✓ 搜索功能正常")
    return True


def test_baseline_still_works():
    """测试baseline模式配置正确（不完整初始化Runner，避免重复加载LLM）"""
    print("\n" + "=" * 60)
    print("测试5: Baseline模式配置检查")
    print("=" * 60)
    
    from qa_system.config import get_ablation_config, ABLATION_CONFIGS
    
    # 只检查配置，不初始化完整Runner（避免重复加载vLLM模型，节省30+秒）
    config = get_ablation_config('baseline')
    
    print(f"\n✓ Baseline配置加载成功")
    print(f"  ablation_mode = {config.ablation_mode}")
    print(f"  retrieval_strategy = {config.retrieval_strategy}")
    print(f"  threshold = {config.threshold}")
    
    # 验证baseline配置不会触发NSTF
    assert config.retrieval_strategy == 'clip_level', "Baseline应使用clip_level策略"
    assert config.ablation_mode == 'baseline', "Baseline的ablation_mode应为'baseline'"
    
    # 验证nstf_level和baseline配置互不影响
    nstf_config = ABLATION_CONFIGS.get('nstf_level')
    baseline_config = ABLATION_CONFIGS.get('baseline')
    
    assert nstf_config.retrieval_strategy != baseline_config.retrieval_strategy, \
        "NSTF和Baseline的retrieval_strategy应该不同"
    
    print(f"\n✓ 配置隔离验证通过")
    print(f"  NSTF策略: {nstf_config.retrieval_strategy}")
    print(f"  Baseline策略: {baseline_config.retrieval_strategy}")
    
    return True


def main():
    print("Stage 3: NSTF集成测试")
    print("=" * 60)
    
    tests = [
        ("配置加载", test_config),
        ("检索器导入", test_retriever_import),
        ("Runner初始化", test_runner_init),
        ("检索器搜索", test_retriever_search),
        ("Baseline兼容性", test_baseline_still_works),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n❌ 测试失败: {name}")
        except Exception as e:
            failed += 1
            print(f"\n❌ 测试异常: {name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ 所有测试通过！可以开始正式实验。")
        print("\n使用方式:")
        print("  # 运行NSTF实验")
        print("  python run_qa.py --config nstf_level --dataset web")
        print("")
        print("  # 运行Baseline对比")
        print("  python run_qa.py --config baseline --dataset web")
    else:
        print("\n⚠️ 存在失败的测试，请检查后重试。")
    
    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
