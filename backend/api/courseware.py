"""课件库 / 课件缺口报告 API"""
import json
from pathlib import Path
from fastapi import APIRouter
from db.database import get_db

router = APIRouter()

ROOT = Path(__file__).parent.parent  # /app
CW_DIR = ROOT / "courseware"
CW_INDEX_FILE = ROOT / "data" / "courseware-index.json"

_cw_index = None


def _load_index() -> dict:
    global _cw_index
    if _cw_index is None:
        try:
            _cw_index = json.loads(CW_INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            _cw_index = {}
    return _cw_index


def _self_hosted(subject: str, node_id: str) -> bool:
    return (CW_DIR / subject / node_id / "index.html").exists()


@router.get("/library/{subject}")
async def library(subject: str):
    """课件库：该科各节点的课件状态（已自托管 / 可拉取 / 无）"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.node_id, kn.name, kn.grade, kn.chapter, kn.exam_weight,
                      COALESCE(ms.mastery,0) AS mastery
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject=? ORDER BY kn.grade, kn.semester""",
            (subject,)
        )
        rows = await cursor.fetchall()
        index = _load_index()
        items = []
        for r in rows:
            nid = r["node_id"]
            available = index.get(nid, [])
            hosted = _self_hosted(subject, nid)
            items.append({
                "node_id": nid, "name": r["name"], "grade": r["grade"],
                "chapter": r["chapter"], "exam_weight": r["exam_weight"],
                "mastery": r["mastery"],
                "self_hosted": hosted,
                "available_count": len(available),
                "courses": available,
                "status": "hosted" if hosted else ("available" if available else "none"),
            })
        return {"subject": subject, "total": len(items),
                "hosted": sum(1 for x in items if x["self_hosted"]),
                "items": items}
    finally:
        await db.close()


@router.get("/gap/{subject}")
async def gap_report(subject: str):
    """课件缺口报告：按 考频 × 掌握度 排优先级，列出最该生成/拉取的课件"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.node_id, kn.name, kn.grade, kn.chapter, kn.exam_weight,
                      COALESCE(ms.mastery,0) AS mastery
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject=? ORDER BY kn.grade, kn.semester""",
            (subject,)
        )
        rows = await cursor.fetchall()
        index = _load_index()
        weight_rank = {"high": 0, "medium": 1, "low": 2}
        gaps = []
        for r in rows:
            nid = r["node_id"]
            if _self_hosted(subject, nid):
                continue  # 已自托管，不算缺口
            available = index.get(nid, [])
            gaps.append({
                "node_id": nid, "name": r["name"], "grade": r["grade"],
                "chapter": r["chapter"], "exam_weight": r["exam_weight"],
                "mastery": r["mastery"],
                "available_count": len(available),
                "source": "pull" if available else "generate",
            })
        # 优先级：考频高→掌握度低→年级低
        gaps.sort(key=lambda g: (weight_rank.get(g["exam_weight"], 1),
                                 g["mastery"], g["grade"] or 0))
        return {"subject": subject, "gap_total": len(gaps), "gaps": gaps}
    finally:
        await db.close()
