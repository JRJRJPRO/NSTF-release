# -*- coding: utf-8 -*-
"""
答案评估模块

使用GPT评估模型回答的正确性
"""

import os
import sys
import time
from typing import Tuple, Optional
from pathlib import Path

# 统一环境设置
from env_setup import setup_paths
setup_paths()

import openai
from mmagent.utils.chat_api import generate_messages

# 加载prompt模板
from ..prompts import get_evaluation_prompt


class Evaluator:
    """答案评估器"""
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Args:
            model: GPT评估模型名称
            api_key: OpenAI API Key，默认从环境变量读取
            base_url: API base URL
            timeout: 请求超时秒数
            max_retries: 最大重试次数
        """
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 初始化客户端
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ 未设置OPENAI_API_KEY，评估功能将不可用")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        
        # 加载评估prompt模板
        self.prompt_template = get_evaluation_prompt()
    
    def _get_response(self, messages: list) -> Tuple[str, int]:
        """获取GPT响应"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            timeout=self.timeout,
            max_tokens=128,
        )
        return response.choices[0].message.content, response.usage.total_tokens
    
    def _get_response_with_retry(self, messages: list) -> Tuple[str, int]:
        """带重试的GPT调用"""
        for i in range(self.max_retries):
            try:
                return self._get_response(messages)
            except Exception as e:
                print(f"  评估重试 {i+1}/{self.max_retries}: {e}")
                time.sleep(5 * (i + 1))  # 递增等待
        raise Exception(f"评估失败，已重试{self.max_retries}次")
    
    def evaluate(
        self,
        question: str,
        prediction: str,
        ground_truth: str,
    ) -> bool:
        """
        评估答案是否正确
        
        Args:
            question: 问题
            prediction: 模型预测答案
            ground_truth: 标准答案
            
        Returns:
            bool: 是否正确
        """
        if not prediction or prediction.strip() == "":
            return False
        
        if self.client is None:
            # 无GPT时使用简单匹配
            return self._simple_match(prediction, ground_truth)
        
        try:
            # 构造评估prompt
            prompt_text = self.prompt_template.format(
                question=question,
                ground_truth_answer=ground_truth,
                agent_answer=prediction,
            )
            
            messages = generate_messages([{"type": "text", "content": prompt_text}])
            response, _ = self._get_response_with_retry(messages)
            
            return "yes" in response.lower()
            
        except Exception as e:
            print(f"  ⚠️ 评估失败: {e}")
            return self._simple_match(prediction, ground_truth)
    
    def _simple_match(self, prediction: str, ground_truth: str) -> bool:
        """简单字符串匹配（备用方案）"""
        pred = prediction.lower().strip()
        gt = ground_truth.lower().strip()
        
        # 完全包含
        if gt in pred or pred in gt:
            return True
        
        # Yes/No问题
        if gt in ['yes', 'no', 'yes.', 'no.']:
            return gt.replace('.', '') == pred.replace('.', '')
        
        return False
    
    def batch_evaluate(
        self,
        results: list,
        question_key: str = 'question',
        prediction_key: str = 'prediction',
        ground_truth_key: str = 'ground_truth',
        delay: float = 0.5,
    ) -> list:
        """
        批量评估
        
        Args:
            results: 结果列表
            question_key: 问题字段名
            prediction_key: 预测答案字段名
            ground_truth_key: 标准答案字段名
            delay: 每次评估间隔（秒）
            
        Returns:
            带评估结果的列表
        """
        for r in results:
            r['gpt_eval'] = self.evaluate(
                r[question_key],
                r.get(prediction_key, ''),
                r[ground_truth_key],
            )
            time.sleep(delay)
        
        return results
