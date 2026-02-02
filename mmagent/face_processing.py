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
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import json
import os
import logging
import gc
from insightface.app import FaceAnalysis
from mmagent.src.face_extraction import extract_faces
from mmagent.src.face_clustering import cluster_faces
from mmagent.utils.video_processing import process_video_clip

# 从环境变量获取 InsightFace 路径
INSIGHTFACE_HOME = os.environ.get("INSIGHTFACE_HOME", "/data1/rongjiej/BytedanceM3Agent/models/insightface")
# 确保目录存在
os.makedirs(INSIGHTFACE_HOME, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(BASE_DIR, "configs", "processing_config.json")
processing_config = json.load(open(config_path))

# 读取GPU配置
GPU_CONFIG = processing_config.get('gpu_config', {
    'gpu_id': 'auto',
    'force_cpu': False,
    'face_detection_size': [480, 480],
    'auto_fallback_to_cpu': True,
    'max_retry_on_oom': 2
})

def clear_gpu_memory():
    """清理GPU内存"""
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
    except:
        gc.collect()

# 全局变量（延迟初始化）
face_app = None
face_app_ctx_id = None

# 全局变量（延迟初始化）
face_app = None
face_app_ctx_id = None

def get_face_app():
    """
    获取人脸识别模型（延迟初始化）
    只在第一次调用时初始化，避免不必要的GPU占用
    
    GPU配置读取自 configs/processing_config.json:
    - gpu_id: 'auto' | 0-7 | -1(CPU)
    - force_cpu: true/false
    - face_detection_size: [width, height]
    """
    global face_app, face_app_ctx_id
    
    if face_app is not None:
        return face_app
    
    # 首次调用，初始化模型
    import onnxruntime as ort
    logger = logging.getLogger(__name__)
    
    available_providers = ort.get_available_providers()
    logger.info(f"🔧 可用的 ONNX Runtime Providers: {available_providers}")
    
    # 读取GPU配置（优先环境变量，其次配置文件）
    force_cpu = os.environ.get('INSIGHTFACE_FORCE_CPU', str(GPU_CONFIG.get('force_cpu', False))).lower() == 'true'
    
    if force_cpu:
        logger.info("🔧 强制使用CPU模式（INSIGHTFACE_FORCE_CPU=true）")
        face_app = FaceAnalysis(name="buffalo_l", root=INSIGHTFACE_HOME, providers=['CPUExecutionProvider'])
        face_app.prepare(ctx_id=-1, det_size=(480, 480))  # 降低尺寸减少内存
        face_app_ctx_id = -1
        logger.info("✅ InsightFace 成功初始化（CPU模式）")
        return face_app
    
    # GPU 模式：从配置文件读取GPU ID
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
    gpu_ids = [int(x.strip()) for x in cuda_visible.split(',') if x.strip()]
    num_gpus = len(gpu_ids)
    
    # 读取配置的GPU ID
    config_gpu_id = GPU_CONFIG.get('gpu_id', 'auto')
    if config_gpu_id == 'auto':
        ctx_id = 0  # 自动模式：使用映射后的第一个GPU
        logger.info(f"🔧 InsightFace 配置: GPU自动模式，使用映射后的GPU 0")
    elif isinstance(config_gpu_id, int):
        if config_gpu_id == -1:
            # 配置指定CPU模式
            logger.info("🔧 配置文件指定CPU模式")
            face_app = FaceAnalysis(name="buffalo_l", root=INSIGHTFACE_HOME, providers=['CPUExecutionProvider'])
            det_size = tuple(GPU_CONFIG.get('face_detection_size', [480, 480]))
            face_app.prepare(ctx_id=-1, det_size=det_size)
            face_app_ctx_id = -1
            logger.info(f"✅ InsightFace 成功初始化（CPU模式，检测尺寸={det_size}）")
            return face_app
        elif 0 <= config_gpu_id < num_gpus:
            ctx_id = config_gpu_id
            logger.info(f"🔧 使用配置文件指定的GPU {ctx_id} (物理GPU: {gpu_ids[ctx_id] if ctx_id < len(gpu_ids) else 'N/A'})")
        else:
            logger.warning(f"⚠️ 配置的GPU ID {config_gpu_id} 超出范围，使用GPU 0")
            ctx_id = 0
    else:
        ctx_id = 0
        logger.warning(f"⚠️ 无效的GPU配置 '{config_gpu_id}'，使用GPU 0")
    
    logger.info(f"🔧 InsightFace 配置: 可用 {num_gpus} 个GPU (CUDA_VISIBLE_DEVICES={cuda_visible})")
    
    # 尝试在GPU上初始化，失败则降级到CPU
    max_retry = GPU_CONFIG.get('max_retry_on_oom', 2)
    for attempt in range(max_retry):
        try:
            
            face_app = FaceAnalysis(
                name="buffalo_l",
                root=INSIGHTFACE_HOME,
                providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            
            # 从配置读取检测尺寸，失败时逐步降低
            base_size = GPU_CONFIG.get('face_detection_size', [480, 480])
            if attempt == 0:
                det_size = tuple(base_size)
            elif attempt == 1:
                det_size = (max(base_size[0] - 160, 320), max(base_size[1] - 160, 320))
            else:
                det_size = (320, 320)
            
            logger.info(f"🔧 尝试初始化 InsightFace (GPU {ctx_id}, 检测尺寸={det_size}, 尝试{attempt+1}/{max_retry})...")
            face_app.prepare(ctx_id=ctx_id, det_size=det_size)
            
            face_app_ctx_id = ctx_id
            logger.info(f"✅ InsightFace 成功初始化在 GPU {ctx_id} (物理GPU: {gpu_ids[0]}, 检测尺寸={det_size})")
            return face_app
            
        except Exception as e:
            logger.warning(f"⚠️ InsightFace 在 GPU 初始化失败 (尝试{attempt+1}/{max_retry}): {e}")
            if attempt == max_retry - 1:  # 最后一次尝试也失败
                break
    
    # GPU初始化失败，检查是否允许降级到CPU
    if GPU_CONFIG.get('auto_fallback_to_cpu', True):
        logger.warning("⚠️ GPU初始化失败，降级到CPU模式")
        face_app = FaceAnalysis(name="buffalo_l", root=INSIGHTFACE_HOME, providers=['CPUExecutionProvider'])
        det_size = tuple(GPU_CONFIG.get('face_detection_size', [480, 480]))
        face_app.prepare(ctx_id=-1, det_size=det_size)
        face_app_ctx_id = -1
        logger.info(f"✅ InsightFace 成功初始化（CPU模式，检测尺寸={det_size}）")
        return face_app
    else:
        raise RuntimeError("GPU初始化失败且不允许降级到CPU（auto_fallback_to_cpu=false）")

cluster_size = processing_config["cluster_size"]
logger = logging.getLogger(__name__)

class Face:
    def __init__(self, frame_id, bounding_box, face_emb, cluster_id, extra_data):
        self.frame_id = frame_id
        self.bounding_box = bounding_box
        self.face_emb = face_emb
        self.cluster_id = cluster_id
        self.extra_data = extra_data

def get_face(frames):
    """获取帧中的人脸（延迟初始化face_app）"""
    app = get_face_app()  # 延迟初始化
    extracted_faces = extract_faces(app, frames)
    faces = [Face(frame_id=f['frame_id'], bounding_box=f['bounding_box'], face_emb=f['face_emb'], cluster_id=f['cluster_id'], extra_data=f['extra_data']) for f in extracted_faces]
    return faces

def cluster_face(faces):
    faces_json = [{'frame_id': f.frame_id, 'bounding_box': f.bounding_box, 'face_emb': f.face_emb, 'cluster_id': f.cluster_id, 'extra_data': f.extra_data} for f in faces]
    clustered_faces = cluster_faces(faces_json, 20, 0.5)
    faces = [Face(frame_id=f['frame_id'], bounding_box=f['bounding_box'], face_emb=f['face_emb'], cluster_id=f['cluster_id'], extra_data=f['extra_data']) for f in clustered_faces]
    return faces

def process_faces(video_graph, base64_frames, save_path, preprocessing=[]):
    """
    Process video frames to detect, cluster and track faces.

    Args:
        video_graph: Graph object to store face embeddings and relationships
        base64_frames (list): List of base64 encoded video frames to process

    Returns:
        dict: Mapping of face IDs to lists of face detections, where each face detection contains:
            - frame_id (int): Frame number where face was detected
            - bounding_box (list): Face bounding box coordinates [x1,y1,x2,y2]
            - face_emb (list): Face embedding vector
            - cluster_id (int): ID of face cluster from initial clustering
            - extra_data (dict): Additional face detection metadata
            - matched_node (int): ID of matched face node in video graph

    The function:
    1. Splits frames into batches and processes them in parallel to detect faces
    2. Clusters detected faces to group similar faces together
    3. Converts face detections to JSON format
    4. Updates video graph with face embeddings and relationships
    5. Returns mapping of face IDs to face detections
    """
    logger.info(f"🔍 [process_faces] 开始处理人脸检测")
    logger.info(f"🔍 [process_faces] 输入帧数: {len(base64_frames)}")
    logger.info(f"🔍 [process_faces] 保存路径: {save_path}")
    
    # 优化批处理大小，避免内存溢出
    # 原版: batch_size = max(len(base64_frames) // cluster_size, 4)
    # 优化: 限制批处理大小在合理范围内
    batch_size = max(min(len(base64_frames) // cluster_size, 16), 4)
    logger.info(f"🔍 [process_faces] 批处理大小: {batch_size}")
    
    def _process_batch(params):
        """
        Process a batch of video frames to detect faces.

        Args:
            params (tuple): A tuple containing:
                - frames (list): List of video frames to process
                - offset (int): Frame offset to add to detected face frame IDs

        Returns:
            list: List of detected faces with adjusted frame IDs

        The function:
        1. Extracts frames and offset from input params
        2. Creates face detection request for the batch
        3. Gets face detection response from service
        4. Adjusts frame IDs of detected faces by adding offset
        5. Returns list of detected faces
        """
        frames = params[0]
        offset = params[1]
        faces = get_face(frames)
        for face in faces:
            face.frame_id += offset
        return faces

    def get_embeddings(base64_frames, batch_size):
        num_batches = (len(base64_frames) + batch_size - 1) // batch_size
        batched_frames = [
            (base64_frames[i * batch_size : (i + 1) * batch_size], i * batch_size)
            for i in range(num_batches)
        ]

        faces = []

        # 优化并行处理: 限制最大worker数量，避免GPU内存溢出
        # 根据可用GPU数量动态调整
        # 如果有多个GPU，可以适当增加并行度；否则保持较低的并行度
        cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '0')
        num_gpus = len(cuda_visible.split(','))
        max_workers = min(num_batches, num_gpus * 4 if num_gpus > 0 else 4)
        
        logger.info(f"🔧 批处理配置: {num_batches} 个批次, batch_size={batch_size}, max_workers={max_workers}")

        # parallel process the batches
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for batch_faces in tqdm(
                executor.map(_process_batch, batched_frames), total=num_batches, desc="处理人脸批次"
            ):
                faces.extend(batch_faces)

        faces = cluster_face(faces)
        return faces

    def establish_mapping(faces, key="cluster_id", filter=None):
        mapping = {}
        filtered_count = 0
        for face in faces:
            if key not in face.keys():
                raise ValueError(f"key {key} not found in faces")
            if filter and not filter(face):
                filtered_count += 1
                continue
            id = face[key]
            if id not in mapping:
                mapping[id] = []
            mapping[id].append(face)
        
        if filtered_count > 0:
            logger.info(f"⚠️ [establish_mapping] 共过滤掉 {filtered_count}/{len(faces)} 个人脸 "
                       f"(detection_threshold={processing_config['face_detection_score_threshold']}, "
                       f"quality_threshold={processing_config['face_quality_score_threshold']})")
        # sort the faces in each cluster by detection score and quality score
        max_faces = processing_config["max_faces_per_character"]
        for id in mapping:
            mapping[id] = sorted(
                mapping[id],
                key=lambda x: (
                    float(x["extra_data"]["face_detection_score"]),
                    float(x["extra_data"]["face_quality_score"]),
                ),
                reverse=True,
            )[:max_faces]
        return mapping

    def filter_score_based(face):
        dthresh = processing_config["face_detection_score_threshold"]
        qthresh = processing_config["face_quality_score_threshold"]
        dscore = float(face["extra_data"]["face_detection_score"])
        qscore = float(face["extra_data"]["face_quality_score"])
        passed = dscore > dthresh and qscore > qthresh
        
        return passed

    def update_videograph(video_graph, tempid2faces):
        id2faces = {}
        for tempid, faces in tempid2faces.items():
            if tempid == -1:
                continue
            if len(faces) == 0:
                continue
            face_info = {
                "embeddings": [face["face_emb"] for face in faces],
                "contents": [face["extra_data"]["face_base64"] for face in faces],
            }
            matched_nodes = video_graph.search_img_nodes(face_info)
            if len(matched_nodes) > 0:
                matched_node = matched_nodes[0][0]
                video_graph.update_node(matched_node, face_info)
                for face in faces:
                    face["matched_node"] = matched_node
            else:
                matched_node = video_graph.add_img_node(face_info)
                for face in faces:
                    face["matched_node"] = matched_node
            if matched_node not in id2faces:
                id2faces[matched_node] = []
            id2faces[matched_node].extend(faces)
        
        max_faces = processing_config["max_faces_per_character"]
        for id, faces in id2faces.items():
            id2faces[id] = sorted(
                faces,
                key=lambda x: (
                    float(x["extra_data"]["face_detection_score"]),
                    float(x["extra_data"]["face_quality_score"]),
                ),
                reverse=True
            )[:max_faces]

        return id2faces
    
    # Check if intermediate results exist
    try:
        logger.info(f"🔍 [process_faces] 尝试加载已有的中间结果: {save_path}")
        with open(save_path, "r") as f:
            faces_json = json.load(f)
        logger.info(f"✅ [process_faces] 成功加载已有结果，检测到 {len(faces_json)} 个人脸")
    except Exception as e:
        logger.info(f"⚠️ [process_faces] 无法加载已有结果: {e}，开始重新检测人脸")
        
        try:
            faces = get_embeddings(base64_frames, batch_size)
            logger.info(f"🔍 [process_faces] 人脸检测完成，共检测到 {len(faces)} 个人脸")

            faces_json = [
                {
                    "frame_id": face.frame_id,
                    "bounding_box": face.bounding_box,
                    "face_emb": face.face_emb,
                    "cluster_id": int(face.cluster_id),
                    "extra_data": face.extra_data,
                }
                for face in faces
            ]

            os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
            with open(save_path, "w") as f:
                json.dump(faces_json, f)
            logger.info(f"✅ [process_faces] 中间结果已保存到: {save_path}")
            
            # 清理GPU内存
            clear_gpu_memory()
        except Exception as detection_error:
            logger.error(f"❌ [process_faces] 人脸检测过程出错: {detection_error}")
            import traceback
            logger.error(f"❌ [process_faces] 错误堆栈:\n{traceback.format_exc()}")
            # 返回空字典，而不是让程序崩溃
            return {}
            
    if "face" in preprocessing:
        logger.info(f"🔍 [process_faces] preprocessing模式，直接返回")
        return

    if len(faces_json) == 0:
        logger.info(f"⚠️ [process_faces] 未检测到任何人脸，返回空字典")
        return {}

    tempid2faces = establish_mapping(faces_json, key="cluster_id", filter=filter_score_based)
    logger.info(f"🔍 [process_faces] 建立映射完成，共 {len(tempid2faces)} 个聚类")
    
    # 打印每个聚类的详细信息
    for cluster_id, faces in tempid2faces.items():
        logger.info(f"🔍 [process_faces] 聚类 {cluster_id}: {len(faces)} 个人脸")
        if len(faces) > 0:
            sample_face = faces[0]
            dscore = float(sample_face['extra_data']['face_detection_score'])
            qscore = float(sample_face['extra_data']['face_quality_score'])
            logger.info(f"   - 样本人脸: frame={sample_face['frame_id']}, "
                       f"detection_score={dscore:.3f}, "
                       f"quality_score={qscore:.3f}")
    
    if len(tempid2faces) == 0:
        logger.info(f"⚠️ [process_faces] 聚类后没有符合条件的人脸，返回空字典")
        logger.info(f"   - 检测阈值: detection={processing_config['face_detection_score_threshold']}, "
                   f"quality={processing_config['face_quality_score_threshold']}")
        return {}

    # 如果video_graph为None，则直接返回聚类结果，不更新video_graph
    if video_graph is None:
        logger.info(f"🔍 [process_faces] video_graph=None，跳过video_graph更新，直接返回聚类结果")
        
        # 构建简化的id2faces：使用cluster_id作为key
        id2faces = {}
        for cluster_id, faces in tempid2faces.items():
            if cluster_id == -1:
                continue
            if len(faces) == 0:
                continue
            # 按检测分数和质量分数排序，保留top-k
            max_faces = processing_config["max_faces_per_character"]
            sorted_faces = sorted(
                faces,
                key=lambda x: (
                    float(x["extra_data"]["face_detection_score"]),
                    float(x["extra_data"]["face_quality_score"]),
                ),
                reverse=True
            )[:max_faces]
            id2faces[f"character_{cluster_id}"] = sorted_faces
        
        logger.info(f"✅ [process_faces] 返回 {len(id2faces)} 个聚类角色")
        
        # 清理GPU内存
        clear_gpu_memory()
        
        return id2faces
    
    # 正常模式：更新video_graph
    id2faces = update_videograph(video_graph, tempid2faces)
    logger.info(f"✅ [process_faces] 更新VideoGraph完成，最终返回 {len(id2faces)} 个人物")
    
    # 清理GPU内存
    clear_gpu_memory()

    return id2faces

def main():
    _, frames, _ = process_video_clip(
        "/mnt/hdfs/foundation/longlin.kylin/mmagent/data/video_clips/CZ_2/-OCrS_r5GHc/11.mp4"
    )
    process_faces(None, frames, "data/temp/face_detection_results.json", preprocessing=["face"])

if __name__ == "__main__":
    main()