"""知识地图 / 全科图谱 / 学习路径 API"""
import json
from fastapi import APIRouter
from db.database import get_db
from api.settings import get_enabled_subjects

router = APIRouter()

# 学科展示元数据（顺序 + 图标 + 中文名）
SUBJECT_META = {
    "math":       {"name": "数学", "icon": "📐", "order": 1},
    "physics":    {"name": "物理", "icon": "⚡", "order": 2},
    "chemistry":  {"name": "化学", "icon": "🧪", "order": 3},
    "english":    {"name": "英语", "icon": "🔤", "order": 4},
    "chinese":    {"name": "语文", "icon": "📝", "order": 5},
    "biology":    {"name": "生物", "icon": "🌱", "order": 6},
    "geography":  {"name": "地理", "icon": "🗺️", "order": 7},
    "history":    {"name": "历史", "icon": "📜", "order": 8},
    "politics":   {"name": "道法", "icon": "⚖️", "order": 9},
}

DOMAIN_NAMES = {
    "number-algebra": "数与代数", "geometry": "图形与几何", "statistics": "统计与概率",
}


@router.get("/subjects")
async def list_subjects():
    """全科列表 + 每科节点数/掌握进度（全科图谱总览用）"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.subject,
                      COUNT(*) AS total,
                      SUM(CASE WHEN COALESCE(ms.mastery,0) >= 0.8 THEN 1 ELSE 0 END) AS mastered,
                      SUM(CASE WHEN COALESCE(ms.mastery,0) > 0 AND COALESCE(ms.mastery,0) < 0.8 THEN 1 ELSE 0 END) AS learning,
                      AVG(COALESCE(ms.mastery,0)) AS avg_mastery
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               GROUP BY kn.subject"""
        )
        rows = await cursor.fetchall()
        result = []
        for r in rows:
            meta = SUBJECT_META.get(r["subject"], {"name": r["subject"], "icon": "📚", "order": 99})
            result.append({
                "subject": r["subject"], "name": meta["name"], "icon": meta["icon"],
                "order": meta["order"], "total": r["total"], "mastered": r["mastered"],
                "learning": r["learning"], "avg_mastery": round(r["avg_mastery"] or 0, 3),
            })
        result.sort(key=lambda x: x["order"])
        enabled = get_enabled_subjects()
        return [r for r in result if r["subject"] in enabled]
    finally:
        await db.close()


@router.get("/map/{subject}")
async def knowledge_map(subject: str):
    """单学科知识地图：节点 + 依赖边 + 掌握度叠加（按domain/grade分组）"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.node_id, kn.name, kn.grade, kn.semester, kn.chapter, kn.domain,
                      kn.prerequisites, kn.exam_weight, kn.exam_points,
                      COALESCE(ms.mastery, 0) AS mastery,
                      COALESCE(ms.status, 'not_started') AS status,
                      kn.teachany_node, kn.courseware_path
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject = ?
               ORDER BY kn.grade, kn.semester""",
            (subject,)
        )
        rows = await cursor.fetchall()
        if not rows:
            return {"subject": subject, "nodes": [], "edges": [], "domains": []}

        node_ids = {r["node_id"] for r in rows}
        nodes, edges, domains = [], [], {}
        for r in rows:
            prereqs = json.loads(r["prerequisites"] or "[]")
            nodes.append({
                "node_id": r["node_id"], "name": r["name"], "grade": r["grade"],
                "semester": r["semester"], "chapter": r["chapter"], "domain": r["domain"],
                "mastery": r["mastery"], "status": r["status"],
                "exam_weight": r["exam_weight"], "exam_points": r["exam_points"],
                "prerequisites": prereqs,
                "has_courseware": bool(r["teachany_node"] or r["courseware_path"]),
            })
            # 依赖边（仅保留同学科内的）
            for p in prereqs:
                if p in node_ids:
                    edges.append({"from": p, "to": r["node_id"]})
            d = r["domain"] or "other"
            domains.setdefault(d, {"id": d, "name": DOMAIN_NAMES.get(d, d), "count": 0})
            domains[d]["count"] += 1

        meta = SUBJECT_META.get(subject, {"name": subject, "icon": "📚"})
        return {
            "subject": subject, "name": meta["name"], "icon": meta["icon"],
            "nodes": nodes, "edges": edges, "domains": list(domains.values()),
        }
    finally:
        await db.close()


@router.get("/node/{node_id}")
async def node_detail(node_id: str):
    """单节点详情：含课标点、前置/后继、掌握度"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.*, COALESCE(ms.mastery,0) AS mastery,
                      COALESCE(ms.status,'not_started') AS status, ms.last_practice
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.node_id = ?""",
            (node_id,)
        )
        r = await cursor.fetchone()
        if not r:
            return {"error": "node not found"}

        # 后继节点（谁依赖我）
        cursor = await db.execute(
            "SELECT node_id, name FROM knowledge_nodes WHERE subject=? AND prerequisites LIKE ?",
            (r["subject"], f'%"{node_id}"%')
        )
        successors = [{"node_id": x["node_id"], "name": x["name"]} for x in await cursor.fetchall()]

        # 前置节点名称
        prereq_ids = json.loads(r["prerequisites"] or "[]")
        prereqs = []
        for pid in prereq_ids:
            c2 = await db.execute("SELECT name, COALESCE((SELECT mastery FROM mastery_summary WHERE node_id=?),0) AS m FROM knowledge_nodes WHERE node_id=?", (pid, pid))
            pr = await c2.fetchone()
            if pr:
                prereqs.append({"node_id": pid, "name": pr["name"], "mastery": pr["m"]})

        # 该节点题目数
        c3 = await db.execute("SELECT COUNT(*) AS c FROM questions WHERE node_id=?", (node_id,))
        q_count = (await c3.fetchone())["c"]

        return {
            "node_id": r["node_id"], "subject": r["subject"], "name": r["name"],
            "grade": r["grade"], "semester": r["semester"], "chapter": r["chapter"],
            "domain": r["domain"], "exam_weight": r["exam_weight"], "exam_points": r["exam_points"],
            "estimated_minutes": r["estimated_minutes"],
            "mastery": r["mastery"], "status": r["status"], "last_practice": r["last_practice"],
            "curriculum_points": json.loads(r["curriculum_points"] or "[]"),
            "teachany_node": r["teachany_node"], "courseware_path": r["courseware_path"],
            "prerequisites": prereqs, "successors": successors, "question_count": q_count,
        }
    finally:
        await db.close()


@router.get("/path/{subject}")
async def learning_path(subject: str):
    """个性化学习路径：按 依赖拓扑 + 掌握度 + 考频 生成有序路径。
    每个节点状态：mastered(已掌握)/learning(学习中)/ready(可学)/locked(前置未达标)。
    'ready' 中按考频排序得到'下一步推荐'。"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.node_id, kn.name, kn.grade, kn.semester, kn.chapter, kn.domain,
                      kn.prerequisites, kn.exam_weight, kn.exam_points, kn.teachany_node,
                      COALESCE(ms.mastery, 0) AS mastery
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject = ?
               ORDER BY kn.grade, kn.semester""",
            (subject,)
        )
        rows = await cursor.fetchall()
        if not rows:
            return {"subject": subject, "path": [], "next_up": []}

        mastery = {r["node_id"]: r["mastery"] for r in rows}
        ids = set(mastery.keys())
        weight_rank = {"high": 0, "medium": 1, "low": 2}

        path = []
        for r in rows:
            prereqs = [p for p in json.loads(r["prerequisites"] or "[]") if p in ids]
            m = r["mastery"]
            unmet = [p for p in prereqs if mastery.get(p, 0) < 0.8]
            if m >= 0.8:
                state = "mastered"
            elif m > 0:
                state = "learning"
            elif not unmet:
                state = "ready"
            else:
                state = "locked"
            path.append({
                "node_id": r["node_id"], "name": r["name"], "grade": r["grade"],
                "semester": r["semester"], "chapter": r["chapter"], "domain": r["domain"],
                "exam_weight": r["exam_weight"], "exam_points": r["exam_points"],
                "mastery": m, "state": state,
                "blocked_by": unmet,
                "has_courseware": bool(r["teachany_node"]),
            })

        # 下一步推荐：ready + learning，按 考频→年级 排序，取前5
        candidates = [n for n in path if n["state"] in ("ready", "learning")]
        candidates.sort(key=lambda n: (
            0 if n["state"] == "learning" else 1,
            weight_rank.get(n["exam_weight"], 1),
            n["grade"] or 0, n["semester"],
        ))
        next_up = candidates[:5]

        meta = SUBJECT_META.get(subject, {"name": subject, "icon": "📚"})
        stats = {
            "mastered": sum(1 for n in path if n["state"] == "mastered"),
            "learning": sum(1 for n in path if n["state"] == "learning"),
            "ready": sum(1 for n in path if n["state"] == "ready"),
            "locked": sum(1 for n in path if n["state"] == "locked"),
            "total": len(path),
        }
        return {"subject": subject, "name": meta["name"], "icon": meta["icon"],
                "path": path, "next_up": next_up, "stats": stats}
    finally:
        await db.close()
