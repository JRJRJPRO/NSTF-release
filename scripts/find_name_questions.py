#!/usr/bin/env python3
"""在 annotation 中搜索有人名的问题"""

import json
import re
from pathlib import Path

def find_questions_with_names():
    # 常见人名列表
    name_patterns = [
        r'\b[A-Z][a-z]+\b',  # 首字母大写的词（可能是人名）
    ]
    
    # 明确的人名
    known_names = ['Saxon', 'John', 'Mary', 'Mike', 'Tom', 'Sarah', 'David', 'Lisa', 
                   'Chris', 'Emily', 'James', 'Anna', 'Steve', 'Jessica', 'Bob', 'Alice']
    
    results = []
    
    for dataset in ['robot', 'web']:
        ann_path = Path(f"/data1/rongjiej/NSTF_MODEL/data/annotations/{dataset}.json")
        if not ann_path.exists():
            continue
        
        print(f"\n检查 {dataset}.json...")
        
        with open(ann_path, 'r') as f:
            data = json.load(f)
        
        count = 0
        for video_name, questions in data.items():
            for q in questions:
                question_text = q.get('question', '')
                answer_text = str(q.get('answer', ''))
                combined = question_text + ' ' + answer_text
                
                # 检查是否包含已知人名
                for name in known_names:
                    if name in combined:
                        results.append({
                            'dataset': dataset,
                            'video': video_name,
                            'question': question_text,
                            'answer': answer_text,
                            'name_found': name
                        })
                        count += 1
                        if count >= 5:  # 每个数据集最多 5 个
                            break
                if count >= 5:
                    break
            if count >= 5:
                break
        
        print(f"  找到 {count} 个包含人名的问题")
    
    print("\n" + "=" * 60)
    print("找到的有人名的问题:")
    print("=" * 60)
    
    for r in results:
        print(f"\n📹 视频: {r['video']} ({r['dataset']})")
        print(f"   人名: {r['name_found']}")
        print(f"   问题: {r['question'][:100]}")
        print(f"   答案: {r['answer'][:100]}")

if __name__ == "__main__":
    find_questions_with_names()
