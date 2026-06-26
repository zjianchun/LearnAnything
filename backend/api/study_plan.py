"""学习计划生成API"""
import json
from fastapi import APIRouter
from db.database import get_db

router = APIRouter()


@router.get("/today")
async def get_today_plan():
    """获取今日学习计划"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT plan, actual, completed FROM daily_plans WHERE date=date('now')")
        row = await cursor.fetchone()
        if row:
            return {"has_plan": True, "plan": json.loads(row["plan"]),
                    "actual": json.loads(row["actual"] or "{}"), "completed": row["completed"]}

        # 自动生成计划
        plan = await _generate_plan(db)
        await db.execute(
            "INSERT OR REPLACE INTO daily_plans (date, plan) VALUES (date('now'), ?)",
            (json.dumps(plan, ensure_ascii=False),)
        )
        await db.commit()
        return {"has_plan": True, "plan": plan, "actual": {}, "completed": 0}
    finally:
        await db.close()


async def _generate_plan(db) -> dict:
    """根据当前学情自动生成每日计划"""
    plan: dict[str, list] = {"math": [], "physics": [], "english": []}

    for subject in ["math", "physics", "english"]:
        # 优先：错题本到期复习
        cursor = await db.execute(
            """SELECT eb.node_id, kn.name FROM error_book eb
               JOIN knowledge_nodes kn ON eb.node_id = kn.node_id
               WHERE kn.subject=? AND eb.next_review <= date('now')
               LIMIT 3""",
            (subject,)
        )
        errors = await cursor.fetchall()
        for e in errors:
            plan[subject].append({"type": "review", "node_id": e["node_id"], "name": e["name"], "minutes": 10})

        # 其次：掌握度最低的知识点练习
        cursor = await db.execute(
            """SELECT kn.node_id, kn.name, COALESCE(ms.mastery, 0) as mastery
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject=?
               ORDER BY mastery ASC
               LIMIT 2""",
            (subject,)
        )
        weak = await cursor.fetchall()
        for w in weak:
            task_type = "learn" if w["mastery"] == 0 else "practice"
            plan[subject].append({"type": task_type, "node_id": w["node_id"], "name": w["name"], "minutes": 20})

    return plan


@router.get("/path/{subject}")
async def get_learning_path(subject: str):
    """获取某科的学习路径"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.node_id, kn.name, kn.grade, kn.semester, kn.chapter, kn.prerequisites,
                      COALESCE(ms.mastery, 0) as mastery, COALESCE(ms.status, 'not_started') as status
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject=?
               ORDER BY kn.grade, kn.semester, kn.node_id""",
            (subject,)
        )
        rows = await cursor.fetchall()
        return [
            {"node_id": r["node_id"], "name": r["name"], "grade": r["grade"], "semester": r["semester"],
             "chapter": r["chapter"], "prerequisites": json.loads(r["prerequisites"] or "[]"),
             "mastery": r["mastery"], "status": r["status"]}
            for r in rows
        ]
    finally:
        await db.close()
