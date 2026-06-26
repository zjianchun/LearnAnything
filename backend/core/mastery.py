"""掌握度计算与学习路径引擎"""
import json
from datetime import datetime, timedelta


def calc_mastery(records: list[dict]) -> float:
    """基于最近10次做题记录计算掌握度 (0.0~1.0)"""
    if not records:
        return 0.0
    recent = records[-10:]
    total_weight = 0.0
    score = 0.0
    for i, r in enumerate(recent):
        weight = 0.5 + 0.5 * ((i + 1) / len(recent))
        diff_weight = {1: 0.8, 2: 1.0, 3: 1.3}.get(r.get("difficulty", 1), 1.0)
        score += r["correct"] * weight * diff_weight
        total_weight += weight * diff_weight
    return round(score / total_weight, 3) if total_weight > 0 else 0.0


def get_status(mastery: float) -> str:
    if mastery >= 0.8:
        return "mastered"
    elif mastery > 0:
        return "learning"
    return "not_started"


def next_review_date(review_stage: int) -> str:
    """遗忘曲线复习间隔: 1天/3天/7天/15天"""
    intervals = {0: 1, 1: 3, 2: 7, 3: 15}
    days = intervals.get(review_stage, 30)
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def find_weak_prerequisites(node_id: str, nodes: dict, mastery_map: dict) -> list[str]:
    """找出某知识点的薄弱前置知识（掌握度<0.6），最多回溯2层"""
    weak = []
    visited = set()

    def _trace(nid: str, depth: int):
        if depth > 2 or nid in visited:
            return
        visited.add(nid)
        node = nodes.get(nid)
        if not node:
            return
        prereqs = json.loads(node.get("prerequisites", "[]"))
        for p in prereqs:
            m = mastery_map.get(p, 0.0)
            if m < 0.6:
                weak.append({"node_id": p, "mastery": m, "depth": depth})
            _trace(p, depth + 1)

    _trace(node_id, 1)
    return weak
