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
import cv2
import numpy as np
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import base64

def test(frames, results):
    print("request recieved. now responding.")
    results.put('1')

def extract_faces(face_app, image_list, num_workers=2):
    """
    从图片列表中提取人脸
    
    Args:
        face_app: InsightFace 应用实例
        image_list: base64 编码的图片列表
        num_workers: 并行工作线程数（降低以避免GPU内存溢出）
    
    Returns:
        list: 提取的人脸信息列表
    """
    print(f"🔍 [extract_faces] 开始提取人脸，输入图片数: {len(image_list)}")
    lock = Lock()
    faces = []  # 初始化结果列表
    total_detected = 0  # 统计检测到的人脸总数

    def process_image(args):
        frame_idx, img_base64 = args
        try:
            # 将base64解码为图片
            img_bytes = base64.b64decode(img_base64)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is None:
                return []

            # 调用 InsightFace 进行人脸检测
            detected_faces = face_app.get(img)
            frame_faces = []
            
            if len(detected_faces) > 0:
                print(f"  ✅ 帧 {frame_idx}: 检测到 {len(detected_faces)} 个人脸")

            for face in detected_faces:
                bbox = [int(x) for x in face.bbox.astype(int).tolist()]
                dscore = face.det_score
                embedding = [float(x) for x in face.normed_embedding.tolist()]

                embedding_np = np.array(face.embedding)
                qscore = np.linalg.norm(embedding_np, ord=2)

                height = bbox[3] - bbox[1]
                width = bbox[2] - bbox[0]
                aspect_ratio = height / width if width > 0 else 0

                face_type = "ortho" if 1 < aspect_ratio < 1.5 else "side"

                face_img = img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
                
                # 检查人脸图片是否有效
                if face_img is None or face_img.size == 0:
                    continue
                    
                _, buffer = cv2.imencode('.jpg', face_img)
                face_base64 = base64.b64encode(buffer).decode('utf-8')

                face_info = {
                    "frame_id": frame_idx,
                    "bounding_box": bbox,
                    "face_emb": embedding,
                    "cluster_id": -1,
                    "extra_data": {
                        "face_type": face_type,
                        "face_base64": face_base64,
                        "face_detection_score": str(dscore),
                        "face_quality_score": str(qscore)
                    },
                }
                
                frame_faces.append(face_info)

            return frame_faces

        except Exception as e:
            # 更详细的错误日志
            import traceback
            error_msg = f"处理图片 {frame_idx} 时出错: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return []

    indexed_inputs = list(enumerate(image_list))

    # 降低并行度，避免GPU内存溢出
    # 原版 num_workers=4，现在默认为2
    print(f"🔍 [extract_faces] 使用 {num_workers} 个工作线程进行并行处理")
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        for frame_faces in tqdm(
            executor.map(process_image, indexed_inputs), 
            total=len(image_list),
            desc="提取人脸"
        ):
            faces.extend(frame_faces)
            total_detected += len(frame_faces)

    print(f"✅ [extract_faces] 人脸提取完成，共检测到 {total_detected} 个人脸 (来自 {len(image_list)} 帧)")
    if total_detected == 0:
        print(f"⚠️ [extract_faces] 警告：未检测到任何人脸！可能原因：")
        print(f"   1. 视频中确实没有人脸")
        print(f"   2. 人脸太小或模糊")
        print(f"   3. InsightFace 模型配置问题")
        print(f"   4. 图片解码失败")
    
    return faces