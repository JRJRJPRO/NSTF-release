#!/usr/bin/env python3
"""
图谱与问答分析统一入口

使用方法:
    # 解析指定视频列表
    python analysis/run.py --video-list analysis/video_list.json
    
    # 解析单个视频
    python analysis/run.py --video study_07
    
    # 强制重新解析
    python analysis/run.py --video study_07 --force
    
    # 只解析图谱
    python analysis/run.py --video study_07 --graph-only
    
    # 只解析问答
    python analysis/run.py --video study_07 --qa-only
    
    # 指定方法
    python analysis/run.py --video study_07 --method nstf
"""

import os
import sys
import json
import argparse
from datetime import datetime

# 添加父目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BASE_PATH)

from analysis.parsers.graph_parser import GraphParser
from analysis.parsers.nstf_graph_parser import NSTFGraphParser
from analysis.parsers.qa_parser import QAParser


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        config_path = os.path.join(SCRIPT_DIR, "config.json")
    
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默认配置
    return {
        "output_path": "analysis/data",
        "skip_existing": True,
        "default_method": "baseline"
    }


def load_video_list(list_path: str) -> list:
    """加载视频列表"""
    with open(list_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'videos' in data:
        return data['videos']
    else:
        raise ValueError(f"无法解析视频列表文件: {list_path}")


def validate_paths(base_path: str, method: str = "baseline") -> bool:
    """
    验证关键路径是否存在
    
    Args:
        base_path: 基础路径
        method: 方法名 (baseline/nstf/nstf_level 等)
        
    Returns:
        True 如果所有路径有效，否则 False
    """
    errors = []
    warnings = []
    
    # 检查 baseline 图谱目录（始终需要）
    for dataset in ["robot", "web"]:
        path = os.path.join(base_path, f"data/memory_graphs/{dataset}")
        if not os.path.exists(path):
            errors.append(f"Baseline 图谱目录不存在: {path}")
    
    # 检查 NSTF 图谱目录（如果使用 NSTF 方法）
    if method in ["nstf", "nstf_level", "nstf_node"]:
        for dataset in ["robot", "web"]:
            path = os.path.join(base_path, f"data/nstf_graphs/{dataset}")
            if not os.path.exists(path):
                warnings.append(f"NSTF 图谱目录不存在: {path}")
    
    # 检查结果目录
    result_method = "nstf" if method.startswith("nstf") else method
    for dataset in ["robot", "web"]:
        path = os.path.join(base_path, f"results/{result_method}/{dataset}")
        if not os.path.exists(path):
            warnings.append(f"结果目录不存在: {path}")
    
    if errors:
        print("[路径验证失败]")
        for e in errors:
            print(f"  - {e}")
        return False
    
    if warnings:
        print("[路径警告]")
        for w in warnings:
            print(f"  - {w}")
    
    return True


def validate_video_list(videos: list, base_path: str, method: str = "baseline") -> tuple:
    """
    验证视频列表中的视频是否存在
    
    Args:
        videos: 视频列表
        base_path: 基础路径
        method: 方法名 (baseline/nstf/nstf_level 等)
    
    Returns:
        (valid_videos, invalid_videos, nstf_missing) 元组
    """
    valid, invalid = [], []
    nstf_missing = []  # 有 baseline 但没有 nstf 图谱的视频
    
    for vid in videos:
        # 检查 baseline 图谱是否存在
        robot_graph = os.path.join(base_path, f"data/memory_graphs/robot/{vid}.pkl")
        web_graph = os.path.join(base_path, f"data/memory_graphs/web/{vid}.pkl")
        
        if os.path.exists(robot_graph) or os.path.exists(web_graph):
            valid.append(vid)
            
            # 如果使用 NSTF 方法，检查 NSTF 图谱
            if method in ["nstf", "nstf_level", "nstf_node"]:
                nstf_robot = os.path.join(base_path, f"data/nstf_graphs/robot/{vid}_nstf.pkl")
                nstf_web = os.path.join(base_path, f"data/nstf_graphs/web/{vid}_nstf.pkl")
                if not os.path.exists(nstf_robot) and not os.path.exists(nstf_web):
                    nstf_missing.append(vid)
        else:
            invalid.append(vid)
    
    return valid, invalid, nstf_missing


def should_skip(video_id: str, output_path: str, method: str, skip_existing: bool, 
                graph_only: bool, qa_only: bool) -> bool:
    """判断是否跳过该视频"""
    if not skip_existing:
        return False
    
    # 输出路径: output_path/{method}/{video_id}
    video_dir = os.path.join(output_path, method, video_id)
    graph_file = os.path.join(video_dir, "graph_analysis.md")
    qa_dir = os.path.join(video_dir, "qa_results")
    
    if graph_only:
        return os.path.exists(graph_file)
    
    if qa_only:
        return os.path.exists(qa_dir) and len(os.listdir(qa_dir)) > 0
    
    # 两者都要检查
    graph_exists = os.path.exists(graph_file)
    qa_exists = os.path.exists(qa_dir) and len(os.listdir(qa_dir)) > 0
    
    return graph_exists and qa_exists


def process_video(video_id: str, config: dict, args) -> dict:
    """处理单个视频"""
    result = {
        "video_id": video_id,
        "graph_success": False,
        "nstf_graph_success": False,
        "qa_success": False,
        "skipped": False,
        "error": None
    }
    
    method = args.method or config.get("default_method", "baseline")
    output_path = os.path.join(BASE_PATH, config["output_path"])
    # 输出路径: output_path/{method}/{video_id}
    video_output_dir = os.path.join(output_path, method, video_id)
    
    # 检查是否跳过
    if should_skip(video_id, output_path, method, config.get("skip_existing", True) and not args.force,
                   args.graph_only, args.qa_only):
        print(f"[跳过] {video_id} (已存在)")
        result["skipped"] = True
        return result
    
    print(f"\n{'='*60}")
    print(f"处理视频: {video_id}")
    print(f"方法: {method}")
    print(f"{'='*60}")
    
    is_nstf_method = method in ["nstf", "nstf_level", "nstf_node"]
    total_steps = 3 if is_nstf_method else 2
    
    # 解析图谱
    if not args.qa_only:
        # Step 1: 解析 Baseline 图谱
        print(f"\n[1/{total_steps}] 解析 Baseline 图谱...")
        graph_parser = GraphParser(BASE_PATH)
        try:
            result["graph_success"] = graph_parser.parse(video_id, video_output_dir)
        except Exception as e:
            print(f"[错误] Baseline 图谱解析失败: {e}")
            result["error"] = str(e)
        
        # Step 2: 如果是 NSTF 方法，额外解析 NSTF 图谱
        if is_nstf_method:
            print(f"\n[2/{total_steps}] 解析 NSTF 图谱...")
            nstf_parser = NSTFGraphParser(BASE_PATH)
            try:
                nstf_success = nstf_parser.parse(video_id, video_output_dir)
                result["nstf_graph_success"] = nstf_success
                if not nstf_success:
                    print(f"[警告] NSTF 图谱不存在或解析失败，将只使用 Baseline 分析")
            except Exception as e:
                print(f"[错误] NSTF 图谱解析失败: {e}")
                result["nstf_graph_success"] = False
    else:
        result["graph_success"] = True  # 跳过视为成功
        if is_nstf_method:
            result["nstf_graph_success"] = True
    
    # 解析问答
    if not args.graph_only:
        step_num = total_steps
        print(f"\n[{step_num}/{total_steps}] 解析问答结果 ({method})...")
        qa_parser = QAParser(BASE_PATH)
        try:
            result["qa_success"] = qa_parser.parse(video_id, video_output_dir, method)
        except Exception as e:
            print(f"[错误] 问答解析失败: {e}")
            result["error"] = str(e)
    else:
        result["qa_success"] = True  # 跳过视为成功
    
    return result


def main():
    parser = argparse.ArgumentParser(description="图谱与问答分析工具")
    
    # 输入选项（二选一）
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--video", type=str, help="单个视频 ID")
    input_group.add_argument("--video-list", type=str, help="视频列表 JSON 文件路径")
    
    # 解析选项
    parser.add_argument("--graph-only", action="store_true", help="只解析图谱")
    parser.add_argument("--qa-only", action="store_true", help="只解析问答")
    parser.add_argument("--method", type=str, default=None, help="问答方法 (baseline/nstf)")
    parser.add_argument("--force", action="store_true", help="强制重新解析（忽略已存在）")
    parser.add_argument("--config", type=str, default=None, help="配置文件路径")
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 获取方法名
    method = args.method or config.get("default_method", "baseline")
    
    # 路径验证
    if not validate_paths(BASE_PATH, method):
        print("\n[错误] 路径验证失败，请检查目录结构")
        sys.exit(1)
    
    # 获取视频列表
    if args.video:
        videos = [args.video]
    else:
        videos = load_video_list(args.video_list)
    
    # 视频列表预检查
    valid_videos, invalid_videos, nstf_missing = validate_video_list(videos, BASE_PATH, method)
    
    if invalid_videos:
        print(f"\n[警告] 以下 {len(invalid_videos)} 个视频的 Baseline 图谱不存在，将跳过:")
        for vid in invalid_videos:
            print(f"  - {vid}")
        videos = valid_videos
    
    if nstf_missing and method in ["nstf", "nstf_level", "nstf_node"]:
        print(f"\n[警告] 以下 {len(nstf_missing)} 个视频缺少 NSTF 图谱，将只分析 Baseline:")
        for vid in nstf_missing:
            print(f"  - {vid}")
    
    if not videos:
        print("\n[错误] 没有有效的视频可处理")
        sys.exit(1)
    
    print(f"")
    print(f"{'#'*60}")
    print(f"# 图谱与问答分析工具")
    print(f"# 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# 待处理视频: {len(videos)} 个")
    print(f"# 方法: {method}")
    if method in ["nstf", "nstf_level", "nstf_node"]:
        print(f"# NSTF 图谱可用: {len(videos) - len(nstf_missing)} 个")
    print(f"{'#'*60}")
    
    # 处理每个视频
    results = []
    for video_id in videos:
        result = process_video(video_id, config, args)
        results.append(result)
    
    # 汇总
    print(f"\n{'='*60}")
    print("处理完成")
    print(f"{'='*60}")
    
    skipped = sum(1 for r in results if r["skipped"])
    graph_success = sum(1 for r in results if r["graph_success"] and not r["skipped"])
    nstf_success = sum(1 for r in results if r.get("nstf_graph_success") and not r["skipped"])
    qa_success = sum(1 for r in results if r["qa_success"] and not r["skipped"])
    errors = [r for r in results if r["error"]]
    
    print(f"总计: {len(results)} 个视频")
    print(f"跳过: {skipped} 个")
    print(f"Baseline 图谱解析成功: {graph_success} 个")
    if method in ["nstf", "nstf_level", "nstf_node"]:
        print(f"NSTF 图谱解析成功: {nstf_success} 个")
    print(f"问答解析成功: {qa_success} 个")
    
    if errors:
        print(f"\n错误列表:")
        for r in errors:
            print(f"  - {r['video_id']}: {r['error']}")
    
    # 输出目录
    output_path = os.path.join(BASE_PATH, config["output_path"])
    print(f"\n输出目录: {output_path}")


if __name__ == "__main__":
    main()
