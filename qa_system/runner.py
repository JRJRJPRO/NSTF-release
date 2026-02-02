# -*- coding: utf-8 -*-
"""
问答系统主运行器

功能与 BytedanceM3Agent/m3_agent/control.py 完全一致，但采用模块化设计
支持结构化存储（按照 STORAGE_SCHEMA.md 规范）
"""

import os
import re
import json
import time
import gc
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .config import QAConfig
from .prompts import get_system_prompt, get_instruction
from .core import Retriever, Evaluator, LLMClient


# Schema 版本
SCHEMA_VERSION = "1.0"

# 动作解析正则
ACTION_PATTERN = r"Action: \[(.*)\].*Content: (.*)"


def get_method_name(ablation_mode: Optional[str]) -> str:
    """根据 ablation_mode 获取 method 名称"""
    if ablation_mode is None or ablation_mode == 'full_nstf':
        return 'nstf'
    elif ablation_mode == 'baseline':
        return 'baseline'
    elif ablation_mode == 'prototype':
        return 'ablation_prototype'
    elif ablation_mode == 'structure':
        return 'ablation_structure'
    else:
        return ablation_mode


class ResultStore:
    """
    结构化结果存储管理器
    
    按照 STORAGE_SCHEMA.md 规范：
    - 路径: results/<method>/<dataset>/<video_id>/<question_id>.json
    - 索引: results/<method>/index_<dataset>.jsonl
    """
    
    def __init__(self, base_dir: Path, method: str, dataset: str):
        """
        Args:
            base_dir: 结果根目录 (NSTF_MODEL/results)
            method: 方法名称 (baseline/nstf/ablation_*)
            dataset: 数据集名称 (robot/web)
        """
        self.base_dir = Path(base_dir)
        self.method = method
        self.dataset = dataset
        
        # 方法目录
        self.method_dir = self.base_dir / method
        # 数据集目录
        self.dataset_dir = self.method_dir / dataset
        # 索引文件
        self.index_file = self.method_dir / f'index_{dataset}.jsonl'
        
        # 确保目录存在
        self.method_dir.mkdir(parents=True, exist_ok=True)
    
    def get_result_path(self, video_id: str, question_id: str) -> Path:
        """获取单个结果文件路径"""
        return self.dataset_dir / video_id / f'{question_id}.json'
    
    def exists(self, video_id: str, question_id: str) -> bool:
        """检查结果是否已存在"""
        return self.get_result_path(video_id, question_id).exists()
    
    def get_completed_ids(self) -> set:
        """获取已完成的问题ID集合（通过扫描文件系统）"""
        completed = set()
        if not self.dataset_dir.exists():
            return completed
        
        for video_dir in self.dataset_dir.iterdir():
            if video_dir.is_dir():
                for json_file in video_dir.glob('*.json'):
                    # 排除临时文件
                    if not json_file.name.endswith('.tmp'):
                        completed.add(json_file.stem)
        return completed
    
    def save(self, result: dict) -> bool:
        """
        保存单个结果（原子写入）
        
        1. 写入临时文件 .tmp
        2. rename 为正式文件
        3. 追加索引
        
        Returns:
            是否保存成功
        """
        video_id = result['video_id']
        question_id = result['id']
        
        # 确保视频目录存在
        video_dir = self.dataset_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # 目标路径
        target_path = video_dir / f'{question_id}.json'
        tmp_path = video_dir / f'{question_id}.json.tmp'
        
        try:
            # 1. 写入临时文件
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 2. 原子 rename
            tmp_path.replace(target_path)
            
            # 3. 追加索引
            self._append_index(result)
            
            return True
            
        except Exception as e:
            print(f"  ⚠️ 保存失败: {e}")
            # 清理临时文件
            if tmp_path.exists():
                tmp_path.unlink()
            return False
    
    def _append_index(self, result: dict):
        """追加索引条目"""
        index_entry = {
            'id': result['id'],
            'video_id': result['video_id'],
            'status': result.get('status', 'success'),
            'type_original': result.get('type_original', []),
            'type_query': result.get('type_query'),
            'gpt_eval': result.get('gpt_eval', False),
            'num_rounds': result.get('num_rounds', 0),
            'elapsed_time_sec': result.get('elapsed_time_sec', 0),
            'search_count': result.get('search_count', 0),
            'timestamp': result.get('timestamp'),
        }
        
        with open(self.index_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(index_entry, ensure_ascii=False) + '\n')


class QARunner:
    """问答系统运行器 - 完整功能版本"""
    
    def __init__(
        self,
        config: QAConfig = None,
        data_dir: str = None,
        output_dir: str = None,
    ):
        """
        Args:
            config: 配置对象，None则使用默认配置
            data_dir: 数据目录，默认为 NSTF_MODEL/data
            output_dir: 输出目录，默认为 NSTF_MODEL/results
        """
        # 路径设置
        self.nstf_model_dir = Path(__file__).parent.parent
        self.data_dir = Path(data_dir) if data_dir else self.nstf_model_dir / 'data'
        self.output_dir = Path(output_dir) if output_dir else self.nstf_model_dir / 'results'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置
        self.config = config or QAConfig.load_default()
        
        # 初始化组件
        self._init_components()
        
        # 结果
        self.results = []
    
    def _init_components(self):
        """初始化各组件"""
        # 根据配置选择检索器
        if self.config.retrieval_strategy == 'node_level':
            # 使用 V2 检索器（节点级别）
            from .core.retriever_v2 import RetrieverV2
            self.retriever = RetrieverV2(
                strategy='node_level',
                threshold=self.config.node_threshold,
                topk=self.config.node_topk,
                include_timestamp=self.config.include_timestamp,
                group_by_clip=self.config.group_by_clip,
                include_semantic=self.config.include_semantic,
                preserve_clip_order=self.config.preserve_clip_order,
            )
            self._use_v2 = True
            self._use_nstf = False
            print(f"✓ 检索器初始化: RetrieverV2 (node_level)")
            print(f"  topk={self.config.node_topk}, threshold={self.config.node_threshold}")
        elif self.config.retrieval_strategy == 'nstf_level':
            # 使用 NSTF 检索器（Procedure级别）
            from .core.retriever_nstf import NSTFRetriever
            self.retriever = NSTFRetriever(
                threshold=self.config.nstf_threshold,
                min_confidence=self.config.nstf_min_confidence,
                max_procedures=self.config.nstf_max_procedures,
                topk_baseline=self.config.topk,
                threshold_baseline=self.config.threshold_baseline,
                include_episodic_evidence=self.config.nstf_include_evidence,
            )
            self._use_v2 = False
            self._use_nstf = True
            print(f"✓ 检索器初始化: NSTFRetriever (nstf_level)")
            print(f"  threshold={self.config.nstf_threshold}, min_confidence={self.config.nstf_min_confidence}")
        else:
            # 使用原始检索器（clip 级别，baseline 兼容）
            self.retriever = Retriever(
                ablation_mode=self.config.ablation_mode,
                threshold=self.config.threshold,
                threshold_baseline=self.config.threshold_baseline,
                topk=self.config.topk,
            )
            self._use_v2 = False
            self._use_nstf = False
            print(f"✓ 检索器初始化: {self.retriever.mode_name}")
        
        # LLM客户端
        self.llm = LLMClient(
            source=self.config.llm_source,
            model=self.config.llm_model,
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            max_tokens=self.config.max_tokens,
        )
        
        # 评估器
        self.evaluator = Evaluator(
            model=self.config.gpt_model,
            timeout=self.config.eval_timeout,
        )
        print(f"✓ 评估器初始化: {self.config.gpt_model}")
    
    def load_annotations(self, dataset: str = None, data_file: str = None) -> Dict:
        """加载annotation数据
        
        Args:
            dataset: 数据集名称 (robot/web)，从默认路径加载
            data_file: 自定义数据文件路径，优先级高于dataset
        """
        if data_file:
            data_path = Path(data_file)
        else:
            data_path = self.data_dir / 'annotations' / f'{dataset}.json'
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ 加载数据: {data_path.name} ({len(data)} 个视频)")
        return data
    
    def load_video_list(self, video_list_file: str) -> List[str]:
        """从JSON文件加载视频列表
        
        Args:
            video_list_file: 视频列表文件路径
            
        Returns:
            视频ID列表
        """
        with open(video_list_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 支持两种格式: {"videos": [...]} 或 [...]
        if isinstance(data, list):
            videos = data
        else:
            videos = data.get('videos', [])
        
        print(f"✓ 加载视频列表: {len(videos)} 个视频")
        return videos
    
    def detect_nstf_graph(self, video_name: str, dataset: str) -> Optional[str]:
        """检测NSTF图谱是否存在
        
        优先级：incremental > static
        """
        nstf_dir = self.data_dir / 'nstf_graphs' / dataset
        
        # 优先查找增量构建的图谱
        incremental_path = nstf_dir / f'{video_name}_nstf_incremental.pkl'
        if incremental_path.exists():
            return str(incremental_path)
        
        # 其次查找静态构建的图谱
        static_path = nstf_dir / f'{video_name}_nstf.pkl'
        if static_path.exists():
            return str(static_path)
        
        return None
    
    def prepare_data(
        self,
        annotations: Dict,
        dataset: str,
        video_names: List[str] = None,
    ) -> List[Dict]:
        """
        准备批量数据
        
        Args:
            annotations: annotation数据
            dataset: 数据集名称
            video_names: 指定视频列表（可选）
            
        Returns:
            数据列表
        """
        data_list = []
        nstf_count = 0
        
        if video_names is None:
            video_names = list(annotations.keys())
        
        for video_name in video_names:
            if video_name not in annotations:
                continue
            
            video_data = annotations[video_name]
            
            # 检测NSTF图谱
            nstf_path = self.detect_nstf_graph(video_name, dataset)
            nstf_available = nstf_path is not None
            if nstf_available:
                nstf_count += 1
            
            # 构造mem_path
            mem_path = video_data.get('mem_path')
            if not mem_path:
                mem_path = f'data/memory_graphs/{dataset}/{video_name}.pkl'
            if not os.path.isabs(mem_path):
                mem_path = str(self.data_dir.parent / mem_path)
            
            for qa in video_data.get('qa_list', []):
                item = {
                    'id': qa.get('question_id', f'{video_name}_Q{len(data_list)+1}'),
                    'video_id': video_name,
                    'mem_path': mem_path,
                    'question': qa['question'],
                    'answer': qa['answer'],
                    'type': qa.get('type', []),
                    'type_query': qa.get('type_query'),  # 从原始数据读取 type_query
                    'nstf_available': nstf_available,
                    'nstf_path': nstf_path,
                }
                if 'before_clip' in qa:
                    item['before_clip'] = qa['before_clip']
                data_list.append(item)
        
        print(f"✓ 数据准备完成: {len(data_list)} 个问题")
        print(f"  NSTF图谱覆盖: {nstf_count}/{len(video_names)} 个视频")
        
        return data_list
    
    def _get_system_prompt(self, nstf_available: bool) -> str:
        """获取 system prompt"""
        return get_system_prompt(
            ablation_mode=self.config.ablation_mode,
            nstf_available=nstf_available
        )
    
    def _get_instruction(self, nstf_available: bool) -> str:
        """获取 instruction"""
        return get_instruction(
            ablation_mode=self.config.ablation_mode,
            nstf_available=nstf_available
        )
    
    def _init_conversation(self, data: Dict) -> Dict:
        """初始化对话"""
        nstf_available = data.get('nstf_available', False)
        prompt = self._get_system_prompt(nstf_available)
        data['conversations'] = [
            {"role": "system", "content": prompt.format(question=data['question'])},
            {"role": "user", "content": "Searched knowledge: {}"}
        ]
        data['finish'] = False
        data['current_clips'] = []
        data['retrieval_trace'] = []  # 新增：检索追踪
        # 存储 instruction 供后续使用
        data['_instruction'] = self._get_instruction(nstf_available)
        return data
    
    def _process_response(self, data: Dict, round_idx: int) -> Dict:
        """处理模型响应，执行搜索或提取答案
        
        Args:
            data: 问题数据
            round_idx: 当前轮次索引（从0开始）
        """
        if data['finish']:
            return data
        
        response = data['conversations'][-1]['content']
        
        # 移除thinking标签后解析
        clean_response = response.split("</think>")[-1] if "</think>" in response else response
        match = re.search(ACTION_PATTERN, clean_response, re.DOTALL)
        
        if match:
            action = match.group(1)
            content = match.group(2)
        else:
            action = "Search"
            content = None
        
        if action == "Answer":
            data['response'] = content
            data['finish'] = True
        else:
            # 执行检索（与原始代码一致，即使 content 为 None 也继续）
            memories = {}
            retrieval_info = None
            
            if content:
                if self._use_v2:
                    # 使用 V2 检索器（节点级别）
                    result = self.retriever.search(
                        mem_path=data['mem_path'],
                        query=content,
                        current_context=data.get('current_context', []),
                        before_clip=data.get('before_clip'),
                    )
                    memories = result['memories']
                    data['current_context'] = result['context']
                    retrieval_info = result['metadata']
                elif self._use_nstf:
                    # 使用 NSTF 检索器（Procedure级别）
                    memories, data['current_clips'], retrieval_info = self.retriever.search(
                        mem_path=data['mem_path'],
                        query=content,
                        current_clips=data['current_clips'],
                        nstf_path=data.get('nstf_path'),
                        before_clip=data.get('before_clip'),
                    )
                    # 记录NSTF决策信息
                    if retrieval_info:
                        data['nstf_decision'] = retrieval_info.get('decision', 'unknown')
                        if 'matched_procedures' in retrieval_info:
                            data['matched_procedures'] = retrieval_info['matched_procedures']
                else:
                    # 使用原始检索器（clip 级别）
                    memories, data['current_clips'], retrieval_info = self.retriever.search(
                        mem_path=data['mem_path'],
                        query=content,
                        current_clips=data['current_clips'],
                        nstf_path=data.get('nstf_path'),
                        before_clip=data.get('before_clip'),
                    )
                
                # 记录检索追踪（仅当 content 非空且有结果时）
                if memories:
                    trace_entry = {
                        'round': round_idx + 1,
                        'query': content.strip() if content else '',
                        'num_results': len(memories),
                        'clips': self._extract_clip_info(memories, retrieval_info)
                    }
                    # 添加NSTF特有的追踪信息
                    if self._use_nstf and retrieval_info:
                        trace_entry['nstf_decision'] = retrieval_info.get('decision')
                        trace_entry['matched_procedures'] = retrieval_info.get('matched_procedures', [])
                    data['retrieval_trace'].append(trace_entry)
            
            search_result = "Searched knowledge: " + json.dumps(
                memories, ensure_ascii=False
            ).encode("utf-8", "ignore").decode("utf-8")
            
            if not memories:
                search_result += "\n(The search result is empty. Please try searching from another perspective.)"
            
            data['conversations'].append({"role": "user", "content": search_result})
        
        return data
    
    def _extract_clip_info(self, memories: Dict, retrieval_info: Any) -> List[Dict]:
        """从检索结果中提取 clip 信息"""
        clips = []
        for key, value in memories.items():
            # 尝试解析 clip_id
            clip_id = None
            source = 'episodic'
            
            if key == 'NSTF_Procedures':
                # NSTF 程序性知识
                source = 'procedure'
                continue  # 程序性知识单独处理
            elif key.startswith('clip_'):
                try:
                    clip_id = int(key.split('_')[1])
                except:
                    pass
            
            if clip_id is not None:
                clips.append({
                    'clip_id': clip_id,
                    'score': None,  # 当前检索器未返回分数，预留
                    'source': source
                })
        
        return clips
    
    def _extract_final_answer(self, data: Dict) -> str:
        """从对话中提取最终答案
        
        重要：只有当 action == "Answer" 时才返回 Content，
        如果模型始终输出 Search action，则返回空字符串（与原始代码一致）
        """
        if 'response' in data:
            return data['response']
        
        # 从最后的assistant消息中提取（只提取 Answer action 的内容）
        for conv in reversed(data['conversations']):
            if conv.get('role') == 'assistant':
                content = conv.get('content', '')
                
                # 移除thinking
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
                
                # 检查是否是 Answer action
                match = re.search(ACTION_PATTERN, content, re.DOTALL)
                if match:
                    action = match.group(1)
                    answer_content = match.group(2)
                    # 只有 Answer action 才返回内容
                    if action == "Answer":
                        return answer_content.strip()
                    # 如果是 Search action，继续查找上一条 assistant 消息
                    continue
        
        # 没有找到有效的 Answer，返回空字符串（与原始代码一致）
        return ""
    
    def run_single(self, data: Dict) -> Dict:
        """
        处理单个问题（完整多轮对话）
        
        Args:
            data: 问题数据
            
        Returns:
            包含结果的数据（含轮次、时间、检索追踪等信息）
        """
        start_time = time.time()
        
        # 重要：每个新问题开始时重置检索器状态
        # 用 try-finally 确保异常时也能 reset
        try:
            if self._use_v2:
                self.retriever.reset()
            
            # 初始化对话
            data = self._init_conversation(data)
            
            # V2 检索器使用 current_context，V1 使用 current_clips
            if self._use_v2:
                data['current_context'] = []
            
            # 记录实际轮次
            actual_rounds = 0
            
            # 多轮推理
            for round_idx in range(self.config.total_round):
                if data['finish']:
                    break
                
                actual_rounds += 1
                
                # 准备消息
                messages = []
                instruction = data.get('_instruction', get_instruction(ablation_mode='baseline'))
                for conv in data['conversations']:
                    msg = conv.copy()
                    if conv['role'] == 'user' and conv == data['conversations'][-1]:
                        msg['content'] += instruction
                        if round_idx == self.config.total_round - 1:
                            msg['content'] += "\n(The Action of this round must be [Answer]. If there is insufficient information, you can make reasonable guesses.)"
                    messages.append(msg)
                
                # 生成回复
                response = self.llm.generate(messages)
                data['conversations'].append({"role": "assistant", "content": response})
                
                # 处理响应（搜索或答案），传入 round_idx 用于记录检索追踪
                data = self._process_response(data, round_idx)
            
            # 提取最终答案
            if 'response' not in data:
                data['response'] = self._extract_final_answer(data)
            
            # 记录效率指标
            elapsed_time = time.time() - start_time
            data['num_rounds'] = actual_rounds
            data['elapsed_time_sec'] = round(elapsed_time, 2)
            
            # 计算有效检索次数（retrieval_trace 中的条目数即为有效检索次数）
            data['search_count'] = len(data.get('retrieval_trace', []))
            
            return data
            
        finally:
            # 无论成功失败都 reset，避免状态污染到下一个问题
            if self._use_v2:
                self.retriever.reset()
    
    def run(
        self,
        dataset: str = 'robot',
        video_names: List[str] = None,
        video_list_file: str = None,
        data_file: str = None,
        query_type_file: str = None,
        limit: int = None,
        output_file: str = None,
        resume: bool = True,
        force: bool = False,
    ) -> Dict:
        """
        运行问答测试
        
        Args:
            dataset: 数据集名称 ('robot' 或 'web')
            video_names: 指定视频列表
            video_list_file: 视频列表JSON文件路径
            data_file: 自定义问答数据文件路径
            query_type_file: Query Type 标注文件路径（用于合并 type_query）
            limit: 最大题数限制
            output_file: 自定义输出文件路径（指定则使用旧的 JSONL 模式）
            resume: 是否从断点续跑（仅 output_file 模式有效）
            force: 是否强制覆盖已有结果（仅结构化存储模式有效）
            
        Returns:
            统计结果
        """
        # 加载数据
        annotations = self.load_annotations(dataset, data_file)
        
        # 确定视频列表
        if video_list_file:
            video_names = self.load_video_list(video_list_file)
        
        data_list = self.prepare_data(annotations, dataset, video_names)
        
        # 加载 Query Type 标注（如果提供）
        query_type_map = {}
        if query_type_file:
            query_type_map = self._load_query_type_map(query_type_file)
            print(f"✓ 加载 Query Type 标注: {len(query_type_map)} 个问题")
        
        if limit:
            data_list = data_list[:limit]
        
        # 确定存储模式
        use_structured_storage = (output_file is None)
        method_name = get_method_name(self.config.ablation_mode)
        
        if use_structured_storage:
            # 结构化存储模式
            store = ResultStore(self.output_dir, method_name, dataset)
            
            if force:
                print(f"⚠️ 强制模式: 将覆盖已有结果")
                completed_ids = set()
            else:
                completed_ids = store.get_completed_ids()
                if completed_ids:
                    print(f"✓ 已完成: {len(completed_ids)} 个问题")
        else:
            # 自定义输出模式（旧的 JSONL 模式）
            store = None
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 断点续跑
            completed_ids = set()
            if resume and output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            item = json.loads(line.strip())
                            if 'id' in item:
                                completed_ids.add(item['id'])
                        except:
                            pass
                print(f"✓ 断点续跑: 已完成 {len(completed_ids)} 个问题")
        
        # 过滤已完成
        total_before_filter = len(data_list)
        data_list = [d for d in data_list if d['id'] not in completed_ids]
        print(f"待处理: {len(data_list)} 个问题")
        
        # 如果没有待处理的问题，给出明确提示
        if len(data_list) == 0 and len(completed_ids) > 0:
            print(f"\n{'='*60}")
            print(f"⚠️ 所有 {len(completed_ids)} 个问题都已完成，没有新问题需要处理")
            print(f"如需重新运行，请使用 --force 参数")
            print(f"{'='*60}")
            
            if use_structured_storage:
                print(f"结果目录: {store.dataset_dir}")
                print(f"索引文件: {store.index_file}")
            
            return {
                'total': len(completed_ids),
                'correct': 0,  # 无法统计已完成的正确数
                'accuracy': None,  # 明确表示未统计
                'avg_rounds': None,
                'avg_time_sec': None,
                'method': method_name,
                'dataset': dataset,
                'skipped': True,
                'message': f'所有 {len(completed_ids)} 个问题已完成，使用 --force 重新运行',
            }
        
        # 统计变量（只统计本次运行的结果）
        results_count = 0
        correct_count = 0
        total_rounds = 0
        total_time = 0.0
        
        # 逐个处理
        for idx, data in enumerate(data_list):
            print(f"\n[{idx+1}/{len(data_list)}] {data['id']}")
            print(f"  Q: {data['question'][:80]}...")
            
            try:
                # 运行问答
                result = self.run_single(data)
                
                # 评估
                result['gpt_eval'] = self.evaluator.evaluate(
                    result['question'],
                    result.get('response', ''),
                    result['answer']
                )
                
                # 构造完整结果（按 Schema）
                full_result = self._build_full_result(
                    result, dataset, method_name, query_type_map
                )
                
                print(f"  A: {result.get('response', '')[:80]}...")
                print(f"  GT: {result['answer'][:80]}...")
                print(f"  {'✓ 正确' if result['gpt_eval'] else '✗ 错误'} | 轮次: {result.get('num_rounds', '?')} | 耗时: {result.get('elapsed_time_sec', '?')}s")
                
                # 保存结果
                if use_structured_storage:
                    store.save(full_result)
                else:
                    # 旧的 JSONL 模式
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(full_result, ensure_ascii=False) + '\n')
                
                # 更新统计
                results_count += 1
                if full_result.get('gpt_eval', False):
                    correct_count += 1
                total_rounds += full_result.get('num_rounds', 0)
                total_time += full_result.get('elapsed_time_sec', 0)
                
            except Exception as e:
                print(f"  ⚠️ 处理失败: {e}")
                # 保存错误状态
                error_result = self._build_error_result(
                    data, dataset, method_name, query_type_map, str(e)
                )
                if use_structured_storage:
                    store.save(error_result)
                else:
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(error_result, ensure_ascii=False) + '\n')
                results_count += 1
                continue
            
            # 定期清理内存
            if (idx + 1) % 50 == 0:
                gc.collect()
        
        # 统计
        accuracy = correct_count / results_count if results_count > 0 else 0
        avg_rounds = total_rounds / results_count if results_count > 0 else 0
        avg_time = total_time / results_count if results_count > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"测试完成")
        print(f"{'='*60}")
        if len(completed_ids) > 0:
            print(f"已跳过: {len(completed_ids)} 个（已完成）")
        print(f"本次处理: {results_count}")
        print(f"正确数: {correct_count}")
        print(f"准确率: {accuracy:.2%}")
        print(f"平均轮次: {avg_rounds:.2f}")
        print(f"平均耗时: {avg_time:.2f}s")
        
        if use_structured_storage:
            print(f"结果目录: {store.dataset_dir}")
            print(f"索引文件: {store.index_file}")
        else:
            print(f"结果文件: {output_file}")
        
        return {
            'total': results_count,
            'correct': correct_count,
            'accuracy': accuracy,
            'avg_rounds': round(avg_rounds, 2),
            'avg_time_sec': round(avg_time, 2),
            'method': method_name,
            'dataset': dataset,
        }
    
    def _load_query_type_map(self, query_type_file: str) -> Dict[str, str]:
        """加载 Query Type 标注映射"""
        query_type_map = {}
        with open(query_type_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for video_id, video_data in data.items():
            for qa in video_data.get('qa_list', []):
                qid = qa.get('question_id')
                qtype = qa.get('type')
                if qid and qtype:
                    # type 可能是字符串或其他格式
                    if isinstance(qtype, str):
                        query_type_map[qid] = qtype
        
        return query_type_map
    
    def _build_full_result(
        self,
        result: Dict,
        dataset: str,
        method: str,
        query_type_map: Dict[str, str],
    ) -> Dict:
        """构造符合 Schema 的完整结果"""
        question_id = result['id']
        
        return {
            # 元信息
            'schema_version': SCHEMA_VERSION,
            'status': 'success',
            'error_message': None,
            
            # 基础标识
            'id': question_id,
            'video_id': result['video_id'],
            'dataset': dataset,
            'method': method,
            
            # 问题信息
            'question': result['question'],
            'answer': result['answer'],
            
            # 类型标注
            'type_original': result.get('type', []),
            # type_query: 优先使用外部标注文件覆盖，否则用原始数据中的
            'type_query': query_type_map.get(question_id) or result.get('type_query'),
            
            # 结果
            'response': result.get('response', ''),
            'gpt_eval': result.get('gpt_eval', False),
            
            # 效率指标
            'num_rounds': result.get('num_rounds', 0),
            'elapsed_time_sec': result.get('elapsed_time_sec', 0),
            
            # 检索统计
            'search_count': result.get('search_count', 0),
            'retrieval_trace': result.get('retrieval_trace', []),
            
            # Token 统计（预留）
            'token_stats': {
                'total_input_tokens': None,
                'total_output_tokens': None,
            },
            
            # 图谱信息
            'nstf_available': result.get('nstf_available', False),
            'nstf_path': result.get('nstf_path'),
            'mem_path': result.get('mem_path', ''),
            
            # 运行环境
            'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.') + f'{datetime.now().microsecond // 1000:03d}',
            'llm_model': self.config.llm_model,
            'gpt_model': self.config.gpt_model,
            
            # 对话历史
            'conversations': result.get('conversations', []),
        }
    
    def _build_error_result(
        self,
        data: Dict,
        dataset: str,
        method: str,
        query_type_map: Dict[str, str],
        error_message: str,
    ) -> Dict:
        """构造错误状态的结果"""
        question_id = data['id']
        
        return {
            # 元信息
            'schema_version': SCHEMA_VERSION,
            'status': 'error',
            'error_message': error_message,
            
            # 基础标识
            'id': question_id,
            'video_id': data['video_id'],
            'dataset': dataset,
            'method': method,
            
            # 问题信息
            'question': data['question'],
            'answer': data['answer'],
            
            # 类型标注
            'type_original': data.get('type', []),
            'type_query': query_type_map.get(question_id),
            
            # 结果（错误时为空）
            'response': '',
            'gpt_eval': False,
            
            # 效率指标
            'num_rounds': data.get('num_rounds', 0),
            'elapsed_time_sec': data.get('elapsed_time_sec', 0),
            
            # 检索统计
            'search_count': 0,
            'retrieval_trace': [],
            
            # Token 统计（预留）
            'token_stats': {
                'total_input_tokens': None,
                'total_output_tokens': None,
            },
            
            # 图谱信息
            'nstf_available': data.get('nstf_available', False),
            'nstf_path': data.get('nstf_path'),
            'mem_path': data.get('mem_path', ''),
            
            # 运行环境
            'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.') + f'{datetime.now().microsecond // 1000:03d}',
            'llm_model': self.config.llm_model,
            'gpt_model': self.config.gpt_model,
            
            # 对话历史
            'conversations': data.get('conversations', []),
        }
