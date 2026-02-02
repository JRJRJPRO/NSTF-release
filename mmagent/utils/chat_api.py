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
import openai
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import logging

# Import Google GenerativeAI for Gemini models
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 确保 INFO 级别日志可见

# 如果没有 handler，添加一个控制台 handler
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Disable httpx logging
logging.getLogger("httpx").setLevel(logging.CRITICAL)
# Disable urllib3 logging (which httpx uses)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
# Disable httpcore logging (which httpx uses)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)

# api utils
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
processing_config = json.load(open(os.path.join(BASE_DIR, "configs", "processing_config.json")))
temp = processing_config["temperature"]
MAX_RETRIES = processing_config["max_retries"]

try:
    config = json.load(open(os.path.join(BASE_DIR, "configs", "api_config.json")))
    client = {}
    gemini_models = {}  # Store Gemini model instances
    
    for model_name in config.keys():
        if "gemini" in model_name.lower() and GEMINI_AVAILABLE:
            # Configure Gemini API
            genai.configure(api_key=config[model_name]["api_key"])
            # Create GenerativeModel instance for Gemini
            print(f"✅ 初始化 Gemini 模型: {model_name}")
            gemini_models[model_name] = genai.GenerativeModel(f"models/{model_name}")
            print(f"   模型对象: {gemini_models[model_name]}")
        else:
            # Check configuration format and choose appropriate client
            if "azure_endpoint" in config[model_name] and config[model_name]["azure_endpoint"]:
                # Use Azure OpenAI client
                client[model_name] = openai.AzureOpenAI(
                    azure_endpoint=config[model_name]["azure_endpoint"],
                    api_version=config[model_name]["api_version"],
                    api_key=config[model_name]["api_key"],
                )
            elif "base_url" in config[model_name] and config[model_name]["base_url"]:
                # Use OpenAI client with custom base URL
                client[model_name] = openai.OpenAI(
                    base_url=config[model_name]["base_url"],
                    api_key=config[model_name]["api_key"],
                )
            else:
                # Use standard OpenAI client
                client[model_name] = openai.OpenAI(
                    api_key=config[model_name]["api_key"],
                )
except:
    pass

def get_response(model, messages, timeout=30):
    """Get chat completion response from specified model.

    Args:
        model (str): Model identifier
        messages (list): List of message dictionaries

    Returns:
        tuple: (response content, total tokens used)
    """
    
    # 优先检查 Gemini: 如果模型名包含 "gemini" 且 Gemini 可用,使用 Gemini API
    if "gemini" in model.lower() and GEMINI_AVAILABLE:
        # 如果模型不在 gemini_models 中,尝试动态初始化
        if model not in gemini_models:
            try:
                # 使用 api_config.json 中的配置
                if model in config:
                    genai.configure(api_key=config[model]["api_key"])
                    gemini_models[model] = genai.GenerativeModel(f"models/{model}")
                else:
                    raise KeyError(f"Model {model} not in config")
            except Exception as e:
                # 回退到 OpenAI 路径
                response = client[model].chat.completions.create(
                    model=model, messages=messages, temperature=temp, timeout=timeout, max_tokens=8192
                )
                return response.choices[0].message.content, response.usage.total_tokens
        
        return get_gemini_response(model, messages, timeout)
    else:
        # Handle OpenAI-compatible API
        response = client[model].chat.completions.create(
            model=model, messages=messages, temperature=temp, timeout=timeout, max_tokens=8192
        )
        
        # return answer and number of tokens
        return response.choices[0].message.content, response.usage.total_tokens

def get_gemini_response(model, messages, timeout=30):
    """Get response from Gemini API.
    
    Args:
        model (str): Model identifier
        messages (list): List of message dictionaries in OpenAI format
        timeout (int): Timeout in seconds
        
    Returns:
        tuple: (response content, estimated tokens used)
    """
    try:
        
        # Convert OpenAI format messages to Gemini format
        gemini_content = convert_openai_to_gemini_messages(messages)
        
        # Get Gemini model instance
        gemini_model = gemini_models[model]
        
        # Generate response with proper content list
        response = gemini_model.generate_content(
            gemini_content,  # Now this is a list of content parts
            generation_config=genai.types.GenerationConfig(
                temperature=temp,
                max_output_tokens=8192,
            ),
            request_options={"timeout": timeout}
        )
        
        # Extract response text
        response_text = response.text
        
        # Try to get actual token usage if available
        try:
            estimated_tokens = response.usage_metadata.total_token_count
        except:
            # Fallback to rough estimation
            estimated_tokens = len(response_text.split()) * 1.3
        
        return response_text, int(estimated_tokens)
        
    except Exception as e:
        raise Exception(f"Gemini API error: {e}")

def convert_openai_to_gemini_messages(messages):
    """Convert OpenAI format messages to Gemini format.
    
    Args:
        messages (list): List of message dictionaries in OpenAI format
        
    Returns:
        list: Gemini-compatible content parts
    """
    import base64
    from PIL import Image
    from io import BytesIO
    
    content_parts = []
    
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        
        if role == "system":
            # System messages become part of user content in Gemini
            content_parts.append(f"System: {content}")
        elif role == "user":
            if isinstance(content, str):
                # Simple string content
                content_parts.append(content)
            elif isinstance(content, list):
                # Complex content with multiple parts (text, images, videos, etc.)
                for part in content:
                    if isinstance(part, dict):
                        part_type = part.get("type", "")
                        if part_type == "text":
                            text_content = part.get("text", "")
                            content_parts.append(text_content)
                        elif part_type == "image_url":
                            # Handle base64 encoded media
                            image_url = part.get("image_url", {}).get("url", "")
                            
                            if image_url.startswith("data:"):
                                # Parse data URL: data:<mime_type>;base64,<data>
                                try:
                                    # Extract mime type and base64 data
                                    header, b64_data = image_url.split(",", 1)
                                    mime_type = header.split(":")[1].split(";")[0]
                                    
                                    if mime_type.startswith("video/"):
                                        # Upload video to Gemini
                                        # For Gemini Files API, we need to save to temp file
                                        import tempfile
                                        import os
                                        
                                        logger.info(f"🎬 检测到视频内容，准备上传到 Gemini Files API")
                                        
                                        video_bytes = base64.b64decode(b64_data)
                                        ext = mime_type.split("/")[1]
                                        
                                        logger.info(f"📦 视频大小: {len(video_bytes)} bytes, 格式: {ext}")
                                        
                                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                                            tmp.write(video_bytes)
                                            tmp_path = tmp.name
                                        
                                        logger.info(f"💾 临时文件已保存: {tmp_path}")
                                        
                                        try:
                                            # Upload video to Gemini Files API
                                            logger.info(f"⬆️  正在上传视频到 Gemini...")
                                            
                                            video_file = genai.upload_file(path=tmp_path)
                                            
                                            logger.info(f"✅ 视频上传成功: {video_file.name}")
                                            
                                            # Wait for file to be processed
                                            import time
                                            max_wait = 60  # 最多等待60秒
                                            wait_interval = 2  # 每2秒检查一次
                                            elapsed = 0
                                            
                                            logger.info(f"⏳ 等待文件处理完成...")
                                            
                                            while elapsed < max_wait:
                                                # Get file status
                                                file_status = genai.get_file(video_file.name)
                                                
                                                if file_status.state.name == "ACTIVE":
                                                    logger.info(f"✅ 文件处理完成，状态: ACTIVE")
                                                    break
                                                elif file_status.state.name == "FAILED":
                                                    error_msg = f"文件处理失败: {file_status.state.name}"
                                                    logger.error(f"❌ {error_msg}")
                                                    raise Exception(error_msg)
                                                else:
                                                    logger.info(f"⏳ 文件状态: {file_status.state.name}, 已等待 {elapsed}秒...")
                                                    time.sleep(wait_interval)
                                                    elapsed += wait_interval
                                            
                                            if elapsed >= max_wait:
                                                error_msg = f"文件处理超时 (>{max_wait}秒)"
                                                logger.error(f"❌ {error_msg}")
                                                raise Exception(error_msg)
                                            
                                            content_parts.append(video_file)
                                        except Exception as upload_error:
                                            logger.error(f"❌ 视频上传失败: {upload_error}")
                                            raise
                                        finally:
                                            # Clean up temp file
                                            if os.path.exists(tmp_path):
                                                os.unlink(tmp_path)
                                                logger.info(f"🗑️  临时文件已清理")
                                    
                                    elif mime_type.startswith("image/"):
                                        # Decode image and add as PIL Image
                                        img_data = base64.b64decode(b64_data)
                                        img = Image.open(BytesIO(img_data))
                                        content_parts.append(img)
                                    
                                    elif mime_type.startswith("audio/"):
                                        # Audio currently not directly supported, add placeholder
                                        content_parts.append("[Audio content]")
                                    
                                except Exception as e:
                                    logger.warning(f"Failed to process media: {e}")
                                    content_parts.append("[Failed to process media]")
                            else:
                                # Regular URL (not base64)
                                content_parts.append(f"[External media: {image_url}]")
                    else:
                        # Fallback for other formats
                        content_parts.append(str(part))
            else:
                # Fallback for other content types
                content_parts.append(str(content))
        elif role == "assistant":
            # For conversation history, we might need to handle this differently
            # For now, treat as user content
            content_parts.append(f"Assistant: {content}")
    
    return content_parts

def get_response_with_retry(model, messages, timeout=30):
    """Retry get_response with error handling.
    
    改进：最多重试7次，每次等待10秒（504超时不无限等待）

    Args:
        model (str): Model identifier
        messages (list): List of message dictionaries

    Returns:
        tuple: (response content, total tokens used)
        
    Raises:
        Exception: If all retries fail
    """
    max_retries = 7  # 最多重试7次
    retry_delay = 10  # 每次等待10秒
    
    for i in range(max_retries):
        try:
            return get_response(model, messages, timeout)
        except Exception as e:
            error_str = str(e).lower()
            # 504超时特殊处理
            if "504" in error_str or "timeout" in error_str:
                logger.warning(f"Retry {i+1}/{max_retries} (timeout): {str(e)[:80]}")
            else:
                logger.warning(f"Retry {i+1}/{max_retries}: {str(e)[:80]}")
            
            if i < max_retries - 1:
                sleep(retry_delay)
            continue
    raise Exception(f"Failed to get response after {max_retries} retries")

def parallel_get_response(model, messages, timeout=30):
    """Process multiple messages in parallel using ThreadPoolExecutor.
    Messages are processed in batches, with each batch completing before starting the next.

    Args:
        model (str): Model identifier
        messages (list): List of message lists to process

    Returns:
        tuple: (list of responses, total tokens used)
    """
    batch_size = config[model]["qpm"]
    responses = []
    total_tokens = 0

    for i in range(0, len(messages), batch_size):
        batch = messages[i:i + batch_size]
        with ThreadPoolExecutor(max_workers=len(batch)) as executor:
            batch_responses = list(executor.map(lambda msg: get_response_with_retry(model, msg, timeout), batch))
            
        # Extract answers and tokens from batch responses
        batch_answers = [response[0] for response in batch_responses]
        batch_tokens = [response[1] for response in batch_responses]
        
        responses.extend(batch_answers)
        total_tokens += sum(batch_tokens)

    return responses, total_tokens


def get_embedding(model, text, timeout=15):
    """Get embedding for text using specified model.

    Args:
        model (str): Model identifier
        text (str): Text to embed

    Returns:
        tuple: (embedding vector, total tokens used)
    """
    response = client[model].embeddings.create(input=text, model=model, timeout=timeout)
    return response.data[0].embedding, response.usage.total_tokens


def get_embedding_with_retry(model, text, timeout=15):
    """Retry get_embedding up to MAX_RETRIES times with error handling.

    Args:
        model (str): Model identifier
        text (str): Text to embed

    Returns:
        tuple: (embedding vector, total tokens used)
        
    Raises:
        Exception: If all retries fail
    """
    for i in range(MAX_RETRIES):
        try:
            return get_embedding(model, text, timeout)
        except Exception as e:
            sleep(20)
            logger.warning(f"Retry {i} times, exception: {e} from get embedding")
            continue
    raise Exception(f"Failed to get embedding after {MAX_RETRIES} retries")

def parallel_get_embedding(model, texts, timeout=15):
    """Process multiple texts in parallel to get embeddings.

    Args:
        model (str): Model identifier
        texts (list): List of texts to embed

    Returns:
        tuple: (list of embeddings, total tokens used)
    """
    batch_size = config[model]["qpm"]
    embeddings = []
    total_tokens = 0
    
    # Process texts in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        max_workers = len(batch)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(lambda x: get_embedding_with_retry(model, x, timeout), batch))
            
        # Split batch results into embeddings and tokens
        batch_embeddings = [result[0] for result in results]
        batch_tokens = [result[1] for result in results]
        
        embeddings.extend(batch_embeddings)
        total_tokens += sum(batch_tokens)
        
    return embeddings, total_tokens

def get_whisper(model, file_path):
    """Transcribe audio file using Whisper model.

    Args:
        model (str): Model identifier
        file_path (str): Path to audio file

    Returns:
        str: Transcription text
    """
    file = open(file_path, "rb")
    return client[model].audio.transcriptions.create(model=model, file=file).text

def get_whisper_with_retry(model, file_path):
    """Retry Whisper transcription with error handling.

    Args:
        model (str): Model identifier
        file_path (str): Path to audio file

    Returns:
        str: Transcription text
        
    Raises:
        Exception: If all retries fail
    """
    for i in range(MAX_RETRIES):
        try:
            return get_whisper(model, file_path)
        except Exception as e:
            sleep(20)
            logger.warning(f"Retry {i} times, exception: {e}")
    raise Exception(f"Failed to get response after {MAX_RETRIES} retries")

def parallel_get_whisper(model, file_paths):
    """Process multiple audio files in parallel using Whisper model.

    Args:
        model (str): Model identifier
        file_paths (list): List of audio file paths

    Returns:
        list: List of transcription results
    """
    batch_size = config[model]["qpm"]
    responses = []
    
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]
        max_workers = len(batch)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_responses = list(executor.map(lambda x: get_whisper_with_retry(model, x), batch))
            
        responses.extend(batch_responses)
        
    return responses

def get_whisper_with_retry(model, file_path):
    """Retry Whisper transcription with error handling.

    Args:
        model (str): Model identifier
        file_path (str): Path to audio file

    Returns:
        str: Transcription text
        
    Raises:
        Exception: If all retries fail
    """
    for i in range(MAX_RETRIES):
        try:
            return get_whisper(model, file_path)
        except Exception as e:
            sleep(20)
            logger.warning(f"Retry {i} times, exception: {e}")
    raise Exception(f"Failed to get response after {MAX_RETRIES} retries")

def parallel_get_whisper(model, file_paths):
    """Process multiple audio files in parallel using Whisper model.

    Args:
        model (str): Model identifier
        file_paths (list): List of audio file paths

    Returns:
        list: List of transcription results
    """
    batch_size = config[model]["qpm"]
    responses = []
    
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]
        max_workers = len(batch)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_responses = list(executor.map(lambda x: get_whisper_with_retry(model, x), batch))
            
        responses.extend(batch_responses)
        
    return responses

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
    messages.append(
        {"role": "system", "content": "You are an expert in video understanding."}
    )
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
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{img_format};base64,{img}",
                                "detail": "high",
                            },
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
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{img_format};base64,{img[1]}",
                            "detail": "high",
                        },
                    })
        elif input["type"] == "video_url":
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": input["content"]},
                }
            )
        elif input["type"] in ["video_base64/mp4", "video_base64/webm"]:
            video_format = input["type"].split("/")[1]
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:video/{video_format};base64,{input['content']}"},
                }
            )
        elif input["type"] in ["audio_base64/mp3", "audio_base64/wav"]:
            audio_format = input["type"].split("/")[1]
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:audio/{audio_format};base64,{input['content']}"
                    },
                }
            )
        else:
            raise ValueError(f"Invalid input type: {input['type']}")
    messages.append({"role": "user", "content": content})
    return messages

def print_messages(messages):
    for message in messages:
        if message["role"] == "user":
            for item in message["content"]:
                if item["type"] == "text":
                    logger.debug(item['text'])
