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
        row = await db.execute_fetchall("SELECT plan, actual, completed FROM daily_plans WHERE date=date('now')")
        if row:
            return {"has_plan": True, "plan": json.loads(row[0][0]), "actual": json.loads(row[0][1] or "{}"), "completed": row[0][2]}

        # 自动生成计划：找出最需要学习的知识点
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
    plan = {"math": [], "physics": [], "english": []}

    for subject in ["math", "physics", "english"]:
        # 优先：错题本到期复习
        errors = await db.execute_fetchall(
            """SELECT eb.node_id, kn.name FROM error_book eb
               JOIN knowledge_nodes kn ON eb.node_id = kn.node_id
               WHERE kn.subject=? AND eb.next_review <= date('now')
               LIMIT 3""",
            (subject,)
        )
        for e in errors:
            plan[subject].append({"type": "review", "node_id": e[0], "name": e[1], "minutes": 10})

        # 其次：掌握度最低的知识点
        weak = await db.execute_fetchall(
            """SELECT kn.node_id, kn.name, COALESCE(ms.mastery, 0) as mastery
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject=?
               ORDER BY mastery ASC
               LIMIT 2""",
            (subject,)
        )
        for w in weak:
            task_type = "learn" if w[2] == 0 else "practice"
            plan[subject].append({"type": task_type, "node_id": w[0], "name": w[1], "minutes": 20})

    return plan


@router.get("/path/{subject}")
async def get_learning_path(subject: str):
    """获取某科的学习路径（按依赖关系排序）"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT kn.node_id, kn.name, kn.grade, kn.semester, kn.chapter, kn.prerequisites,
                      COALESCE(ms.mastery, 0) as mastery, COALESCE(ms.status, 'not_started') as status
               FROM knowledge_nodes kn
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject=?
               ORDER BY kn.grade, kn.semester, kn.node_id""",
            (subject,)
        )
        path = []
        for r in rows:
            path.append({
                "node_id": r[0], "name": r[1], "grade": r[2], "semester": r[3],
                "chapter": r[4], "prerequisites": json.loads(r[5] or "[]"),
                "mastery": r[6], "status": r[7]
            })
        return path
    finally:
        await db.close()
