# Copyright (2025) Bytedance Ltd. and/or its affiliates

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from typing import List
import os

# Global variables for local embedding model
local_tokenizer = None
local_model = None

def get_local_embeddings(texts: List[str], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[List[float]]:
    """Get embeddings using local sentence transformer model.
    
    Args:
        texts: List of texts to embed
        model_name: Name of the embedding model to use
        
    Returns:
        List of embedding vectors
    """
    global local_tokenizer, local_model
    
    # Load model if not already loaded
    if local_tokenizer is None or local_model is None:
        local_tokenizer = AutoTokenizer.from_pretrained(model_name)
        local_model = AutoModel.from_pretrained(model_name)
        
        # Move to GPU if available
        # 注意: CUDA_VISIBLE_DEVICES 已经设置,所以这里使用映射后的设备ID (0, 1, ...)
        # 而不是物理设备ID (3, 5, ...)
        if torch.cuda.is_available():
            device = "cuda:0"  # 使用第一个可见的GPU
            local_model = local_model.to(device)
            print(f"🔧 [LocalEmbedding] 加载到 {device} (物理GPU {os.environ.get('CUDA_VISIBLE_DEVICES', 'N/A').split(',')[0]})")
        local_model.eval()
    
    device = next(local_model.parameters()).device
    embeddings = []
    
    # Process texts in batches to avoid memory issues
    batch_size = 32
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        
        # Tokenize
        encoded_input = local_tokenizer(
            batch_texts, 
            padding=True, 
            truncation=True, 
            return_tensors='pt',
            max_length=512
        )
        
        # Move to device
        encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
        
        # Get embeddings
        with torch.no_grad():
            model_output = local_model(**encoded_input)
            # Use mean pooling
            attention_mask = encoded_input['attention_mask']
            token_embeddings = model_output.last_hidden_state
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            batch_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            
            # Normalize embeddings
            batch_embeddings = torch.nn.functional.normalize(batch_embeddings, p=2, dim=1)
            
            # Convert to list
            batch_embeddings = batch_embeddings.cpu().numpy().tolist()
            embeddings.extend(batch_embeddings)
    
    return embeddings

def parallel_get_local_embedding(texts: List[str]) -> tuple:
    """Get embeddings locally without API calls.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        tuple: (embeddings, 0) - 0 tokens since it's local
    """
    embeddings = get_local_embeddings(texts)
    return embeddings, 0  # No tokens used for local model