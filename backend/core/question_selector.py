"""智能选题引擎"""
import random


def select_questions(
    available: list[dict],
    mastery: float,
    count: int = 5,
    error_book_ids: list[str] | None = None,
) -> list[dict]:
    """
    根据掌握度选题:
    - 掌握度低(<0.5): 出简单题为主
    - 掌握度中(0.5-0.8): 混合难度
    - 掌握度高(>0.8): 出难题确认掌握
    优先插入错题本中到期复习的题
    """
    if not available:
        return []

    # 错题本到期的优先
    review_qs = []
    remaining = []
    error_book_ids = error_book_ids or []
    for q in available:
        if q["id"] in error_book_ids:
            review_qs.append(q)
        else:
            remaining.append(q)

    # 按掌握度决定难度分布
    if mastery < 0.5:
        target_diff = {1: 0.6, 2: 0.3, 3: 0.1}
    elif mastery < 0.8:
        target_diff = {1: 0.2, 2: 0.5, 3: 0.3}
    else:
        target_diff = {1: 0.1, 2: 0.3, 3: 0.6}

    # 按难度分桶
    buckets = {1: [], 2: [], 3: []}
    for q in remaining:
        d = q.get("difficulty", 1)
        buckets.setdefault(d, []).append(q)

    selected = review_qs[:count]
    slots = count - len(selected)

    for diff, ratio in target_diff.items():
        n = max(1, int(slots * ratio))
        pool = buckets.get(diff, [])
        selected.extend(random.sample(pool, min(n, len(pool))))

    return selected[:count]
