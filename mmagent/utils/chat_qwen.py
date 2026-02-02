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
import json
import logging
import torch
import os
from typing import Union, List, Dict
from transformers import Qwen2_5OmniProcessor, Qwen2_5OmniThinkerForConditionalGeneration, GenerationConfig
from qwen_omni_utils import process_mm_info

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set CUDA device
if 'CUDA_VISIBLE_DEVICES' in os.environ:
    os.environ['CUDA_VISIBLE_DEVICES'] = os.environ['CUDA_VISIBLE_DEVICES']
else:
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Default to GPU 0

# Configure logging
logger = logging.getLogger(__name__)

# 使用绝对路径加载配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
processing_config = json.load(open(os.path.join(BASE_DIR, "configs", "processing_config.json")))
temp = processing_config["temperature"]
MAX_RETRIES = processing_config["max_retries"]
processor, thinker = None, None

def get_response(messages):
    """Get chat completion response from specified model.

    Args:
        model (str): Model identifier
        messages (list): List of message dictionaries

    Returns:
        tuple: (response content, total tokens used)
    """
    global thinker, processor
    if thinker is None:
        # 使用 CUDA_VISIBLE_DEVICES 中的第一个 GPU（已经被映射过）
        # 例如: CUDA_VISIBLE_DEVICES=3,5 时，这里的 cuda:0 实际对应物理 GPU 3
        cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
        num_gpus = len(cuda_visible.split(','))
        
        print(f"🔧 [Qwen] CUDA_VISIBLE_DEVICES={cuda_visible}, 可用 {num_gpus} 个GPU")
        
        # 根据可用 GPU 数量决定 device_map 策略
        if num_gpus >= 2:
            # 多 GPU：使用 auto 让模型自动分配
            device_map = "auto"
            print(f"🔧 [Qwen] 使用多GPU模式 (device_map=auto)")
        else:
            # 单 GPU：强制使用映射后的 GPU 0
            device_map = {"": "cuda:0"}
            print(f"🔧 [Qwen] 使用单GPU模式 (device=cuda:0, 对应物理GPU {cuda_visible})")
        
        thinker = Qwen2_5OmniThinkerForConditionalGeneration.from_pretrained(
            processing_config["ckpt"],
            torch_dtype="auto",          # Let the model choose appropriate dtype
            device_map=device_map,       # 根据GPU数量选择策略
            attn_implementation="flash_attention_2",
        )
        thinker.eval()
        processor = Qwen2_5OmniProcessor.from_pretrained(processing_config["ckpt"])
        
        print(f"✅ [Qwen] 模型加载完成")
    
    # Ensure all operations use the same device
    device = next(thinker.parameters()).device
    
    text = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    generation_config = GenerationConfig(pad_token_id=151643, bos_token_id=151644, eos_token_id=151645)
    
    USE_AUDIO_IN_VIDEO = True
    audios, images, videos = process_mm_info(messages, use_audio_in_video=USE_AUDIO_IN_VIDEO)
    # Note: transformers 4.56+ uses 'audio' (singular) not 'audios' (plural)
    inputs = processor(text=text, audio=audios, images=images, videos=videos, return_tensors="pt", padding=True, use_audio_in_video=USE_AUDIO_IN_VIDEO)
    
    # Move all inputs to the same device as the model and ensure dtype consistency
    model_dtype = next(thinker.parameters()).dtype
    inputs = {k: v.to(device).to(model_dtype) if hasattr(v, 'to') and v.dtype.is_floating_point 
              else v.to(device) if hasattr(v, 'to') else v 
              for k, v in inputs.items()}

    # Inference: Generation of the output text and audio
    with torch.no_grad():
        generation = thinker.generate(**inputs, generation_config=generation_config, use_audio_in_video=USE_AUDIO_IN_VIDEO, max_new_tokens=4096, do_sample=True, temperature=temp)
        generate_ids = generation[:, inputs['input_ids'].size(1):]
        response = processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        token_count = len(generation[0])
        
    # Clean up
    del generation
    del generate_ids
    del inputs
    torch.cuda.empty_cache()
    
    return response, token_count

def generate_messages(inputs):
    """Generate message list for chat completion from mixed inputs.

    Args:
        inputs (list): List of input dictionaries with 'type' and 'content' keys
        type can be:
            "text" - text content
            "image/jpeg", "image/png" - base64 encoded images
            "video/mp4", "video/webm" - base64 encoded videos
            "video_url" - video URL
            "audio/mp3", "audio/wav" - base64 encoded audio
        content should be a string for text,
        a list of base64 encoded media for images/video/audio,
        or a string (url) for video_url
        inputs are like: 
        [
            {
                "type": "video_base64/mp4",
                "content": <base64>
            },
            {
                "type": "text",
                "content": "Describe the video content."
            },
            ...
        ]

    Returns:
        list: Formatted messages for chat completion
    """
    messages = []
    content = []
    for input in inputs:
        if not input["content"]:
            logger.warning("empty content, skip")
            continue
        if input["type"] == "text":
            content.append({"type": "text", "text": input["content"]})
        elif input["type"] in ["images/jpeg", "images/png"]:
            img_format = input["type"].split("/")[1]
            if isinstance(input["content"][0], str):
                content.extend(
                    [
                        {
                            "type": "image",
                            "image": f"data:image;base64,{img}",
                        }
                        for img in input["content"]
                    ]
                )
            else:
                for img in input["content"]:
                    content.append({
                        "type": "text",
                        "text": img[0],
                    })
                    content.append({
                        "type": "image",
                        "image": f"data:image;base64,{img[1]}"
                    })
        elif input["type"] in ["video_url", "video_base64/mp4", "video_base64/webm"]:
            content.append(
                {
                    "type": "video",
                    "video": input["content"],
                }
            )
        else:
            raise ValueError(f"Invalid input type: {input['type']}")
    messages.append({"role": "user", "content": content})
    return messages