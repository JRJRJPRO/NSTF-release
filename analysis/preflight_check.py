#!/usr/bin/env python3
"""
分析模块预检查工具

在运行 run.py 之前，使用此脚本检查环境和数据完整性。

使用方法:
    python analysis/preflight_check.py
    python analysis/preflight_check.py --video-list analysis/video_list.json
    python analysis/preflight_check.py --video study_07
"""

import os
import sys
import json
import pickle
import argparse
from datetime import datetime
from typing import Tuple, List, Dict, Any

# 路径设置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(SCRIPT_DIR)

# ANSI 颜色
class Colors:
    OK = '\033[92m'      # 绿色
    WARN = '\033[93m'    # 黄色
    FAIL = '\033[91m'    # 红色
    BOLD = '\033[1m'
    END = '\033[0m'

def print_ok(msg):
    print(f"{Colors.OK}✓{Colors.END} {msg}")

def print_warn(msg):
    print(f"{Colors.WARN}⚠{Colors.END} {msg}")

def print_fail(msg):
    print(f"{Colors.FAIL}✗{Colors.END} {msg}")

def print_header(msg):
    print(f"\n{Colors.BOLD}=== {msg} ==={Colors.END}")


# ============ 检查函数 ============

def check_python_version() -> bool:
    """检查 Python 版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print_ok(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_fail(f"Python 版本过低: {version.major}.{version.minor} (需要 3.9+)")
        return False


def check_working_directory() -> bool:
    """检查工作目录"""
    cwd = os.getcwd()
    expected_markers = ['data', 'results', 'analysis']
    
    if os.path.basename(cwd) == 'NSTF_MODEL':
        print_ok(f"工作目录正确: {cwd}")
        return True
    
    # 检查是否在子目录中
    for marker in expected_markers:
        if not os.path.exists(os.path.join(BASE_PATH, marker)):
            print_fail(f"无法找到 {marker} 目录，请确认 BASE_PATH 正确: {BASE_PATH}")
            return False
    
    print_ok(f"BASE_PATH 检测正确: {BASE_PATH}")
    return True


def check_config_file() -> Tuple[bool, dict]:
    """检查配置文件"""
    config_path = os.path.join(SCRIPT_DIR, 'config.json')
    
    if not os.path.exists(config_path):
        print_fail(f"配置文件不存在: {config_path}")
        return False, {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print_ok(f"配置文件加载成功: {config_path}")
        return True, config
    except json.JSONDecodeError as e:
        print_fail(f"配置文件 JSON 格式错误: {e}")
        return False, {}


def check_graph_paths(config: dict) -> Tuple[int, int]:
    """检查图谱路径"""
    robot_found, web_found = 0, 0
    
    graph_paths = config.get('graph_paths', {})
    
    # Robot 图谱
    robot_path = os.path.join(BASE_PATH, graph_paths.get('robot', 'data/memory_graphs/robot'))
    if os.path.exists(robot_path):
        pkl_files = [f for f in os.listdir(robot_path) if f.endswith('.pkl')]
        robot_found = len(pkl_files)
        print_ok(f"Robot 图谱目录: {robot_found} 个 pkl 文件")
    else:
        print_fail(f"Robot 图谱目录不存在: {robot_path}")
    
    # Web 图谱
    web_path = os.path.join(BASE_PATH, graph_paths.get('web', 'data/memory_graphs/web'))
    if os.path.exists(web_path):
        pkl_files = [f for f in os.listdir(web_path) if f.endswith('.pkl')]
        web_found = len(pkl_files)
        print_ok(f"Web 图谱目录: {web_found} 个 pkl 文件")
    else:
        print_warn(f"Web 图谱目录不存在: {web_path}")
    
    return robot_found, web_found


def check_result_paths(config: dict, method: str = 'baseline') -> Tuple[int, int]:
    """检查结果路径"""
    robot_found, web_found = 0, 0
    
    result_paths = config.get('result_paths', {}).get(method, {})
    
    # Robot 结果
    robot_path = os.path.join(BASE_PATH, result_paths.get('robot', f'results/{method}/robot'))
    if os.path.exists(robot_path):
        video_dirs = [d for d in os.listdir(robot_path) if os.path.isdir(os.path.join(robot_path, d))]
        robot_found = len(video_dirs)
        print_ok(f"Robot 结果目录 ({method}): {robot_found} 个视频")
    else:
        print_fail(f"Robot 结果目录不存在: {robot_path}")
    
    # Web 结果
    web_path = os.path.join(BASE_PATH, result_paths.get('web', f'results/{method}/web'))
    if os.path.exists(web_path):
        video_dirs = [d for d in os.listdir(web_path) if os.path.isdir(os.path.join(web_path, d))]
        web_found = len(video_dirs)
        print_ok(f"Web 结果目录 ({method}): {web_found} 个视频")
    else:
        print_warn(f"Web 结果目录不存在: {web_path}")
    
    return robot_found, web_found


def check_pickle_compatibility(sample_video: str = None) -> bool:
    """检查 Pickle 兼容性"""
    
    # 找一个测试文件
    test_paths = []
    if sample_video:
        test_paths.append(os.path.join(BASE_PATH, f'data/memory_graphs/robot/{sample_video}.pkl'))
        test_paths.append(os.path.join(BASE_PATH, f'data/memory_graphs/web/{sample_video}.pkl'))
    
    # 默认测试文件
    robot_dir = os.path.join(BASE_PATH, 'data/memory_graphs/robot')
    if os.path.exists(robot_dir):
        pkl_files = [f for f in os.listdir(robot_dir) if f.endswith('.pkl')]
        if pkl_files:
            test_paths.append(os.path.join(robot_dir, pkl_files[0]))
    
    for test_path in test_paths:
        if os.path.exists(test_path):
            try:
                with open(test_path, 'rb') as f:
                    graph = pickle.load(f)
                
                # 检查结构
                graph_type = type(graph).__name__
                
                # 尝试获取节点
                nodes = None
                if hasattr(graph, 'nodes'):
                    nodes = graph.nodes
                elif isinstance(graph, dict) and 'nodes' in graph:
                    nodes = graph['nodes']
                
                if nodes is not None:
                    print_ok(f"Pickle 加载成功: {os.path.basename(test_path)}")
                    print_ok(f"  类型: {graph_type}, 节点数: {len(nodes)}")
                    
                    # 检查节点结构
                    if nodes:
                        sample_node = list(nodes.values())[0] if isinstance(nodes, dict) else nodes[0]
                        node_type = type(sample_node).__name__
                        print_ok(f"  节点类型: {node_type}")
                    return True
                else:
                    print_warn(f"图谱结构异常，无法获取 nodes 属性")
                    return False
                    
            except ModuleNotFoundError as e:
                print_fail(f"Pickle 加载失败 - 模块未找到: {e}")
                print_warn("  建议: 确保运行环境包含序列化时使用的模块")
                print_warn("  或者修改 graph_parser.py 使用通用反序列化")
                return False
            except Exception as e:
                print_fail(f"Pickle 加载失败: {e}")
                return False
    
    print_warn("未找到可测试的 pkl 文件")
    return False


def check_video_list(list_path: str = None) -> Tuple[List[str], List[str]]:
    """检查视频列表"""
    if list_path is None:
        list_path = os.path.join(SCRIPT_DIR, 'video_list.json')
    
    if not os.path.exists(list_path):
        print_warn(f"视频列表文件不存在: {list_path}")
        return [], []
    
    try:
        with open(list_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            videos = data
        elif isinstance(data, dict) and 'videos' in data:
            videos = data['videos']
        else:
            print_fail(f"视频列表格式无法识别")
            return [], []
        
        print_ok(f"视频列表加载成功: {len(videos)} 个视频")
        
    except json.JSONDecodeError as e:
        print_fail(f"视频列表 JSON 格式错误: {e}")
        return [], []
    
    # 验证每个视频
    valid, invalid = [], []
    for vid in videos:
        robot_graph = os.path.join(BASE_PATH, f'data/memory_graphs/robot/{vid}.pkl')
        web_graph = os.path.join(BASE_PATH, f'data/memory_graphs/web/{vid}.pkl')
        
        if os.path.exists(robot_graph) or os.path.exists(web_graph):
            valid.append(vid)
        else:
            invalid.append(vid)
    
    if valid:
        print_ok(f"  有效视频: {len(valid)} 个")
    if invalid:
        print_fail(f"  无效视频: {len(invalid)} 个")
        for vid in invalid[:5]:  # 只显示前5个
            print(f"    - {vid}")
        if len(invalid) > 5:
            print(f"    ... 还有 {len(invalid) - 5} 个")
    
    return valid, invalid


def check_single_video(video_id: str, method: str = 'baseline') -> dict:
    """检查单个视频的完整性"""
    result = {
        'video_id': video_id,
        'graph_exists': False,
        'graph_dataset': None,
        'qa_exists': False,
        'qa_count': 0,
        'qa_dataset': None
    }
    
    # 检查图谱
    for dataset in ['robot', 'web']:
        graph_path = os.path.join(BASE_PATH, f'data/memory_graphs/{dataset}/{video_id}.pkl')
        if os.path.exists(graph_path):
            result['graph_exists'] = True
            result['graph_dataset'] = dataset
            print_ok(f"图谱文件存在: {dataset}/{video_id}.pkl")
            break
    else:
        print_fail(f"图谱文件不存在: {video_id}.pkl")
    
    # 检查问答结果
    for dataset in ['robot', 'web']:
        result_dir = os.path.join(BASE_PATH, f'results/{method}/{dataset}/{video_id}')
        if os.path.exists(result_dir):
            json_files = [f for f in os.listdir(result_dir) if f.endswith('.json')]
            result['qa_exists'] = True
            result['qa_count'] = len(json_files)
            result['qa_dataset'] = dataset
            print_ok(f"问答结果存在: {dataset}/{video_id}/ ({len(json_files)} 个问题)")
            break
    else:
        print_fail(f"问答结果不存在: {video_id}/")
    
    return result


def check_output_directory() -> bool:
    """检查输出目录权限"""
    output_dir = os.path.join(SCRIPT_DIR, 'data')
    
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            print_ok(f"输出目录创建成功: {output_dir}")
            return True
        except PermissionError:
            print_fail(f"无法创建输出目录: {output_dir}")
            return False
    else:
        # 测试写入权限
        test_file = os.path.join(output_dir, '.write_test')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print_ok(f"输出目录可写: {output_dir}")
            return True
        except PermissionError:
            print_fail(f"输出目录不可写: {output_dir}")
            return False


def check_parsers_import() -> bool:
    """检查解析器模块导入"""
    try:
        sys.path.insert(0, BASE_PATH)
        from analysis.parsers.graph_parser import GraphParser
        from analysis.parsers.qa_parser import QAParser
        print_ok("解析器模块导入成功")
        return True
    except ImportError as e:
        print_fail(f"解析器模块导入失败: {e}")
        return False


# ============ 主函数 ============

def main():
    parser = argparse.ArgumentParser(description='分析模块预检查工具')
    parser.add_argument('--video', type=str, help='检查单个视频')
    parser.add_argument('--video-list', type=str, help='检查视频列表文件')
    parser.add_argument('--method', type=str, default='baseline', help='检查方法')
    args = parser.parse_args()
    
    print(f"\n{'#'*60}")
    print(f"# 分析模块预检查工具")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# BASE_PATH: {BASE_PATH}")
    print(f"{'#'*60}")
    
    issues = []
    
    # 1. 环境检查
    print_header("环境检查")
    if not check_python_version():
        issues.append("Python 版本过低")
    if not check_working_directory():
        issues.append("工作目录异常")
    
    # 2. 配置检查
    print_header("配置检查")
    config_ok, config = check_config_file()
    if not config_ok:
        issues.append("配置文件问题")
        config = {}
    
    # 3. 模块检查
    print_header("模块检查")
    if not check_parsers_import():
        issues.append("解析器模块导入失败")
    
    # 4. 数据路径检查
    print_header("数据路径检查")
    robot_graphs, web_graphs = check_graph_paths(config)
    robot_results, web_results = check_result_paths(config, args.method)
    
    if robot_graphs == 0 and web_graphs == 0:
        issues.append("没有找到图谱文件")
    if robot_results == 0 and web_results == 0:
        issues.append("没有找到结果文件")
    
    # 5. Pickle 兼容性检查
    print_header("Pickle 兼容性检查")
    if not check_pickle_compatibility(args.video):
        issues.append("Pickle 加载失败")
    
    # 6. 输出目录检查
    print_header("输出目录检查")
    if not check_output_directory():
        issues.append("输出目录问题")
    
    # 7. 视频列表检查
    if args.video_list:
        print_header("视频列表检查")
        valid, invalid = check_video_list(args.video_list)
        if invalid:
            issues.append(f"{len(invalid)} 个无效视频 ID")
    
    # 8. 单个视频检查
    if args.video:
        print_header(f"视频检查: {args.video}")
        check_single_video(args.video, args.method)
    
    # 汇总
    print_header("检查汇总")
    if issues:
        print_fail(f"发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("建议: 解决上述问题后再运行 run.py")
        return 1
    else:
        print_ok("所有检查通过!")
        print()
        print("可以运行:")
        if args.video:
            print(f"  python analysis/run.py --video {args.video}")
        elif args.video_list:
            print(f"  python analysis/run.py --video-list {args.video_list}")
        else:
            print("  python analysis/run.py --video-list analysis/video_list.json")
        return 0


if __name__ == '__main__':
    sys.exit(main())
