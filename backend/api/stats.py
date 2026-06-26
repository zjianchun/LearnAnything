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
        row = await db.execute_fetchall("SELECT * FROM daily_stats WHERE date=date('now')")
        if not row:
            return {"date": None, "math_minutes": 0, "physics_minutes": 0, "english_minutes": 0,
                    "questions_total": 0, "questions_correct": 0}
        r = row[0]
        return {
            "date": r[0], "math_minutes": r[1], "physics_minutes": r[2], "english_minutes": r[3],
            "math_correct_rate": r[4], "physics_correct_rate": r[5], "english_correct_rate": r[6],
            "questions_total": r[7], "questions_correct": r[8], "nodes_learned": json.loads(r[9] or "[]")
        }
    finally:
        await db.close()


@router.get("/weekly")
async def weekly_stats():
    """最近7天趋势"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT * FROM daily_stats WHERE date >= date('now', '-7 days') ORDER BY date"
        )
        return [
            {"date": r[0], "math_minutes": r[1], "physics_minutes": r[2], "english_minutes": r[3],
             "math_correct_rate": r[4], "physics_correct_rate": r[5], "english_correct_rate": r[6],
             "questions_total": r[7], "questions_correct": r[8]}
            for r in rows
        ]
    finally:
        await db.close()


@router.get("/mastery-map")
async def mastery_map():
    """全部知识点掌握度地图"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT kn.node_id, kn.subject, kn.name, kn.grade, kn.chapter,
                      COALESCE(ms.mastery, 0) as mastery, COALESCE(ms.status, 'not_started') as status
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               ORDER BY kn.subject, kn.grade, kn.node_id"""
        )
        result = {}
        for r in rows:
            subject = r[1]
            result.setdefault(subject, []).append({
                "node_id": r[0], "name": r[2], "grade": r[3],
                "chapter": r[4], "mastery": r[5], "status": r[6]
            })
        return result
    finally:
        await db.close()


@router.get("/error-book")
async def error_book_summary():
    """错题本概览"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT eb.question_id, eb.node_id, eb.error_count, eb.review_stage, eb.next_review,
                      q.question, kn.name as node_name
               FROM error_book eb
               JOIN questions q ON eb.question_id = q.id
               JOIN knowledge_nodes kn ON eb.node_id = kn.node_id
               ORDER BY eb.next_review"""
        )
        return [
            {"question_id": r[0], "node_id": r[1], "error_count": r[2],
             "review_stage": r[3], "next_review": r[4], "question": r[5], "node_name": r[6]}
            for r in rows
        ]
    finally:
        await db.close()
