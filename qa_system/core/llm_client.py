# -*- coding: utf-8 -*-
"""
LLM客户端模块

支持云端（OpenAI兼容API）和本地（vLLM）两种模式
所有配置统一从 NSTF_MODEL/.env 读取
"""

import os
import sys
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

# 统一环境设置
from env_setup import NSTF_MODEL_DIR

from dotenv import load_dotenv
load_dotenv(NSTF_MODEL_DIR / '.env', override=False)


def setup_gpu_for_local_llm():
    """为本地LLM设置GPU环境变量（必须在导入vLLM前调用）"""
    # 设置必要的环境变量
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = os.environ.get('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')
    os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = os.environ.get('VLLM_WORKER_MULTIPROC_METHOD', 'spawn')
    
    # GPU 配置
    gpu_devices = os.environ.get('GPU_DEVICES', '0,1,2,3')
    os.environ['CUDA_VISIBLE_DEVICES'] = gpu_devices
    
    # 计算参数
    gpu_list = [x.strip() for x in gpu_devices.split(',') if x.strip()]
    tensor_parallel_size = len(gpu_list)
    gpu_memory_utilization = float(os.environ.get('GPU_MEMORY_UTILIZATION', '0.85'))
    max_model_len = int(os.environ.get('MAX_MODEL_LEN', '8192'))
    max_num_seqs = int(os.environ.get('MAX_NUM_SEQS', '256'))
    enforce_eager = os.environ.get('ENFORCE_EAGER', 'false').lower() == 'true'
    
    print(f"GPU配置: 设备={gpu_devices}, 并行大小={tensor_parallel_size}")
    print(f"vLLM配置: 内存利用率={gpu_memory_utilization}, 最大长度={max_model_len}")
    
    return {
        'tensor_parallel_size': tensor_parallel_size,
        'gpu_memory_utilization': gpu_memory_utilization,
        'max_model_len': max_model_len,
        'max_num_seqs': max_num_seqs,
        'enforce_eager': enforce_eager,
    }


class LLMClient:
    """LLM客户端 - 统一封装云端和本地模型"""
    
    def __init__(
        self,
        source: str = "cloud",
        model: str = None,
        temperature: float = 0.6,
        top_p: float = 0.95,
        max_tokens: int = 4096,
        **kwargs
    ):
        """
        Args:
            source: 'cloud' 或 'local'
            model: 模型名称/路径
            temperature: 采样温度
            top_p: Top-p采样
            max_tokens: 最大生成token数
            **kwargs: 其他参数（如GPU配置）
        """
        self.source = source
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        
        if source == "cloud":
            self._init_cloud(model)
        elif source == "local":
            self._init_local(model, **kwargs)
        else:
            raise ValueError(f"未知LLM源: {source}")
    
    def _init_cloud(self, model: str = None):
        """初始化云端客户端"""
        from openai import OpenAI
        
        self.model = model or os.getenv("CONTROL_LLM_MODEL", "gemini-2.5-flash")
        self.client = OpenAI(
            api_key=os.getenv("CONTROL_LLM_API_KEY"),
            base_url=os.getenv("CONTROL_LLM_BASE_URL"),
        )
        print(f"✓ 云端LLM初始化: {self.model}")
    
    def _init_local(self, model: str = None, **kwargs):
        """初始化本地vLLM - 从 .env 读取所有配置"""
        # 先设置GPU环境变量（必须在导入vLLM前）
        gpu_config = setup_gpu_for_local_llm()
        
        from vllm import LLM, SamplingParams
        from transformers import AutoTokenizer
        
        # 本地模型路径
        self.model_path = str(NSTF_MODEL_DIR / "models" / "M3-Agent-Control")
        
        # 检查模型路径
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"本地模型不存在: {self.model_path}")
        
        print(f"加载本地模型: {self.model_path}")
        
        # 加载 tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        # 加载 vLLM 模型
        self.model = LLM(
            model=self.model_path,
            tensor_parallel_size=gpu_config['tensor_parallel_size'],
            gpu_memory_utilization=gpu_config['gpu_memory_utilization'],
            max_model_len=gpu_config['max_model_len'],
            max_num_seqs=gpu_config['max_num_seqs'],
            disable_log_stats=True,
            trust_remote_code=True,
            disable_custom_all_reduce=True,  # 多GPU重要
            enforce_eager=gpu_config['enforce_eager'],
            dtype="bfloat16"
        )
        
        self.sampling_params = SamplingParams(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=20,
            max_tokens=self.max_tokens
        )
        print(f"✓ 本地模型加载完成")
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        timeout: int = 120,
    ) -> str:
        """
        生成回复
        
        Args:
            messages: 对话消息列表 [{"role": "...", "content": "..."}]
            timeout: 超时秒数（云端）
            
        Returns:
            生成的文本
        """
        if self.source == "cloud":
            return self._generate_cloud(messages, timeout)
        else:
            return self._generate_local(messages)
    
    def _generate_cloud(self, messages: List[Dict], timeout: int) -> str:
        """云端生成"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                timeout=timeout,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  ⚠️ 云端生成失败: {e}")
            return ""
    
    def _generate_local(self, messages: List[Dict]) -> str:
        """本地vLLM生成"""
        try:
            # 使用tokenizer的chat template
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=True
            )
            
            # 检查长度 - 留出生成空间（从 .env 读取 MAX_MODEL_LEN）
            max_input_len = int(os.getenv('MAX_MODEL_LEN', '8192')) - self.max_tokens
            if len(input_ids) > max_input_len:
                print(f"  ⚠️ 输入过长 ({len(input_ids)} tokens)，截断处理 (限制: {max_input_len})")
                return "[SKIPPED: Input too long]"
            
            outputs = self.model.generate(
                prompts=[{"prompt_token_ids": input_ids}],
                sampling_params=self.sampling_params,
                use_tqdm=False,
            )
            return outputs[0].outputs[0].text
        except Exception as e:
            print(f"  ⚠️ 本地生成失败: {e}")
            return ""
    
    def batch_generate(
        self,
        batch_messages: List[List[Dict]],
        timeout: int = 120,
    ) -> List[str]:
        """
        批量生成（云端逐个，本地并行）
        
        Args:
            batch_messages: 批量对话列表
            timeout: 超时秒数
            
        Returns:
            生成文本列表
        """
        if self.source == "cloud":
            results = []
            for messages in batch_messages:
                results.append(self._generate_cloud(messages, timeout))
            return results
        else:
            return self._batch_generate_local(batch_messages)
    
    def _batch_generate_local(self, batch_messages: List[List[Dict]]) -> List[str]:
        """本地批量生成"""
        prompts = []
        valid_indices = []
        max_input_len = int(os.getenv('MAX_MODEL_LEN', '8192')) - self.max_tokens
        
        for i, messages in enumerate(batch_messages):
            input_ids = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                enable_thinking=True
            )
            if len(input_ids) <= max_input_len:
                prompts.append({"prompt_token_ids": input_ids})
                valid_indices.append(i)
        
        if not prompts:
            return ["[SKIPPED]"] * len(batch_messages)
        
        outputs = self.model.generate(
            prompts=prompts,
            sampling_params=self.sampling_params,
            use_tqdm=False,
        )
        
        results = ["[SKIPPED]"] * len(batch_messages)
        for idx, output in zip(valid_indices, outputs):
            results[idx] = output.outputs[0].text
        
        return results
