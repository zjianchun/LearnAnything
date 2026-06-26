"""统计与家长看板API"""
import json
from fastapi import APIRouter
from db.database import get_db

router = APIRouter()


@router.get("/today")
async def today_stats():
    """今日学习统计"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM daily_stats WHERE date=date('now')")
        r = await cursor.fetchone()
        if not r:
            return {"date": None, "math_minutes": 0, "physics_minutes": 0, "english_minutes": 0,
                    "questions_total": 0, "questions_correct": 0}
        return {
            "date": r["date"], "math_minutes": r["math_minutes"],
            "physics_minutes": r["physics_minutes"], "english_minutes": r["english_minutes"],
            "math_correct_rate": r["math_correct_rate"], "physics_correct_rate": r["physics_correct_rate"],
            "english_correct_rate": r["english_correct_rate"],
            "questions_total": r["questions_total"], "questions_correct": r["questions_correct"],
            "nodes_learned": json.loads(r["nodes_learned"] or "[]")
        }
    finally:
        await db.close()


@router.get("/weekly")
async def weekly_stats():
    """最近7天趋势"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM daily_stats WHERE date >= date('now', '-7 days') ORDER BY date"
        )
        rows = await cursor.fetchall()
        return [
            {"date": r["date"], "math_minutes": r["math_minutes"],
             "physics_minutes": r["physics_minutes"], "english_minutes": r["english_minutes"],
             "math_correct_rate": r["math_correct_rate"], "physics_correct_rate": r["physics_correct_rate"],
             "english_correct_rate": r["english_correct_rate"],
             "questions_total": r["questions_total"], "questions_correct": r["questions_correct"]}
            for r in rows
        ]
    finally:
        await db.close()


@router.get("/mastery-map")
async def mastery_map():
    """全部知识点掌握度地图"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.node_id, kn.subject, kn.name, kn.grade, kn.chapter,
                      COALESCE(ms.mastery, 0) as mastery, COALESCE(ms.status, 'not_started') as status
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               ORDER BY kn.subject, kn.grade, kn.node_id"""
        )
        rows = await cursor.fetchall()
        result: dict[str, list] = {}
        for r in rows:
            subject = r["subject"]
            result.setdefault(subject, []).append({
                "node_id": r["node_id"], "name": r["name"], "grade": r["grade"],
                "chapter": r["chapter"], "mastery": r["mastery"], "status": r["status"]
            })
        return result
    finally:
        await db.close()


@router.get("/error-book")
async def error_book_summary():
    """错题本概览"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT eb.question_id, eb.node_id, eb.error_count, eb.review_stage, eb.next_review,
                      q.question, kn.name as node_name
               FROM error_book eb
               JOIN questions q ON eb.question_id = q.id
               JOIN knowledge_nodes kn ON eb.node_id = kn.node_id
               ORDER BY eb.next_review"""
        )
        rows = await cursor.fetchall()
        return [
            {"question_id": r["question_id"], "node_id": r["node_id"], "error_count": r["error_count"],
             "review_stage": r["review_stage"], "next_review": r["next_review"],
             "question": r["question"], "node_name": r["node_name"]}
            for r in rows
        ]
    finally:
        await db.close()
