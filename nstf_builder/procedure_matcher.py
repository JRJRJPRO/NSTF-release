# -*- coding: utf-8 -*-
"""
ProcedureMatcher - Procedure 匹配器

用于增量构建时判断新检测到的程序是否应该与已有 Procedure 合并

多信号融合: goal相似度(50%) + 类型匹配(20%) + 动词重叠(30%)
"""

import re
import numpy as np
from typing import Dict, List, Optional, Set

from .utils import get_normalized_embedding


class ProcedureMatcher:
    """
    Procedure 匹配器 - 用于增量更新
    
    多信号融合判断是否应该合并:
    - goal_sim: 目标语义相似度 (50%)
    - type_match: 类型匹配 (20%)  
    - verb_overlap: 关键动词重叠 (30%)
    """
    
    def __init__(
        self,
        match_threshold: float = 0.70,
        weights: Dict[str, float] = None,
        debug: bool = False
    ):
        """
        Args:
            match_threshold: 匹配阈值，高于此值则合并
            weights: 各信号权重，默认 {'goal': 0.5, 'type': 0.2, 'verb': 0.3}
            debug: 是否输出调试信息
        """
        self.match_threshold = match_threshold
        self.weights = weights or {'goal': 0.5, 'type': 0.2, 'verb': 0.3}
        self.debug = debug
        self.decision_log = []  # 记录所有决策便于审核
    
    def match_existing(
        self, 
        nstf_graph: Dict, 
        detected: Dict
    ) -> Optional[Dict]:
        """
        判断检测到的程序是否与已有 Procedure 匹配
        
        Args:
            nstf_graph: 当前 NSTF 图谱
            detected: 新检测到的程序信息，包含 goal, type 等
            
        Returns:
            匹配的 Procedure（用于合并）或 None（需要创建新的）
        """
        proc_nodes = nstf_graph.get('procedure_nodes', {})
        if not proc_nodes:
            return None
        
        detected_goal = detected.get('goal', '')
        detected_type = detected.get('type', 'task')
        
        # 计算检测目标的 embedding
        detected_emb = get_normalized_embedding(detected_goal)
        detected_verbs = self._extract_verbs(detected_goal)
        
        candidates = []
        
        for proc_id, proc in proc_nodes.items():
            signals = self._compute_signals(
                detected_emb, detected_type, detected_verbs,
                proc
            )
            
            # 加权得分
            score = (
                self.weights['goal'] * signals['goal_sim'] +
                self.weights['type'] * signals['type_match'] +
                self.weights['verb'] * signals['verb_overlap']
            )
            
            candidates.append({
                'proc_id': proc_id,
                'proc': proc,
                'score': score,
                'signals': signals
            })
        
        # 找最佳匹配
        best = max(candidates, key=lambda x: x['score'])
        
        # 记录决策
        decision = {
            'detected_goal': detected_goal[:50],
            'detected_type': detected_type,
            'best_match': best['proc_id'],
            'score': round(best['score'], 4),
            'signals': {k: round(v, 4) for k, v in best['signals'].items()},
            'decision': 'merge' if best['score'] >= self.match_threshold else 'create_new'
        }
        self.decision_log.append(decision)
        
        if self.debug:
            print(f"  Match: {decision['decision']} → {best['proc_id']} "
                  f"(score={best['score']:.3f}, goal_sim={best['signals']['goal_sim']:.3f})")
        
        return best['proc'] if best['score'] >= self.match_threshold else None
    
    def _compute_signals(
        self,
        detected_emb: np.ndarray,
        detected_type: str,
        detected_verbs: Set[str],
        proc: Dict
    ) -> Dict[str, float]:
        """计算各项匹配信号"""
        signals = {}
        
        # 信号 1: Goal 语义相似度
        proc_emb = proc.get('embeddings', {}).get('goal_emb')
        if proc_emb is not None:
            signals['goal_sim'] = float(np.dot(detected_emb, proc_emb))
        else:
            signals['goal_sim'] = 0.0
        
        # 信号 2: 类型匹配
        proc_type = proc.get('proc_type', 'task')
        signals['type_match'] = 1.0 if detected_type == proc_type else 0.5
        
        # 信号 3: 关键动词重叠 (Jaccard)
        proc_verbs = self._extract_verbs(proc.get('goal', ''))
        signals['verb_overlap'] = self._jaccard(detected_verbs, proc_verbs)
        
        return signals
    
    def _extract_verbs(self, text: str) -> Set[str]:
        """提取动词（扩展的动词列表）"""
        # 通用动词 + 领域动词
        verb_patterns = [
            # 通用动作
            r'\b(make|cook|prepare|clean|wash|wipe|put|place|store|open|close|turn|check|get|take|give|find|use|move|bring|carry|hold|set|keep|leave|start|stop|finish|begin|end)\b',
            # 厨房相关
            r'\b(chop|stir|fry|boil|bake|pour|mix|season|slice|peel|heat|cool|freeze|defrost|marinate|grill|roast|steam|sauté)\b',
            # 清洁相关
            r'\b(scrub|sweep|mop|dust|vacuum|rinse|dry|polish|tidy|organize|arrange|sort|dispose|throw|discard)\b',
            # 社交相关
            r'\b(greet|talk|ask|answer|tell|say|explain|discuss|help|assist|serve|offer|invite|welcome)\b',
            # 动名词形式
            r'\b(making|cooking|preparing|cleaning|washing|wiping|putting|placing|storing|opening|closing|turning|checking|getting|taking)\b',
        ]
        
        verbs = set()
        text_lower = text.lower()
        for pattern in verb_patterns:
            matches = re.findall(pattern, text_lower)
            verbs.update(matches)
        
        return verbs
    
    def _jaccard(self, set1: Set[str], set2: Set[str]) -> float:
        """Jaccard 相似度"""
        if not set1 and not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def get_decision_summary(self) -> Dict:
        """获取决策统计摘要"""
        if not self.decision_log:
            return {'total': 0, 'merges': 0, 'creates': 0}
        
        merges = sum(1 for d in self.decision_log if d['decision'] == 'merge')
        creates = len(self.decision_log) - merges
        
        return {
            'total': len(self.decision_log),
            'merges': merges,
            'creates': creates,
            'merge_rate': merges / len(self.decision_log) if self.decision_log else 0
        }
    
    def clear_log(self):
        """清空决策日志"""
        self.decision_log = []
