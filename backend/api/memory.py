"""艾宾浩斯记忆系统 API"""
from datetime import date, timedelta
from fastapi import APIRouter, Request
from db.database import get_db

router = APIRouter()

# 艾宾浩斯间隔天数 (stage → days until next review)
INTERVALS = {0: 0, 1: 1, 2: 3, 3: 7, 4: 15, 5: 30, 6: 9999}


@router.get("/today")
async def today_queue(subject: str = "", limit: int = 0):
    """获取今日复习队列(到期复习+新卡)"""
    from api.settings import _load
    if limit <= 0:
        limit = _load().get("daily_new_cards", 20)
    today = str(date.today())
    db = await get_db()
    try:
        # 到期需复习的
        if subject:
            cursor = await db.execute(
                """SELECT mp.*, mc.front, mc.back, mc.subject, mc.category, mc.audio_url
                   FROM memory_progress mp JOIN memory_cards mc ON mp.card_id = mc.id
                   WHERE mp.review_date <= ? AND mp.stage < 6 AND mc.subject = ?
                   ORDER BY mp.stage ASC, mp.review_date ASC LIMIT ?""",
                (today, subject, limit))
        else:
            cursor = await db.execute(
                """SELECT mp.*, mc.front, mc.back, mc.subject, mc.category, mc.audio_url
                   FROM memory_progress mp JOIN memory_cards mc ON mp.card_id = mc.id
                   WHERE mp.review_date <= ? AND mp.stage < 6
                   ORDER BY mp.stage ASC, mp.review_date ASC LIMIT ?""",
                (today, limit))
        due = [dict(r) for r in await cursor.fetchall()]

        # 如果到期的不够，补新卡
        new_cards = []
        if len(due) < limit:
            need = limit - len(due)
            sub_filter = "AND mc.subject = ?" if subject else ""
            params = [need] if not subject else [subject, need]
            cursor = await db.execute(
                f"""SELECT mc.* FROM memory_cards mc
                    WHERE mc.id NOT IN (SELECT card_id FROM memory_progress)
                    {sub_filter}
                    ORDER BY mc.difficulty ASC LIMIT ?""",
                tuple(params))
            new_cards = [dict(r) for r in await cursor.fetchall()]

        return {"due": due, "new": new_cards, "due_count": len(due), "new_count": len(new_cards)}
    finally:
        await db.close()


@router.post("/review")
async def submit_review(req: Request):
    """提交复习结果"""
    body = await req.json()
    card_id = body.get("card_id")
    correct = body.get("correct", False)
    today = str(date.today())

    db = await get_db()
    try:
        # 查已有进度
        cursor = await db.execute("SELECT * FROM memory_progress WHERE card_id=?", (card_id,))
        prog = await cursor.fetchone()

        if prog:
            stage = prog["stage"]
            streak = prog["correct_streak"]
            total_r = prog["total_reviews"] + 1
            total_c = prog["total_correct"] + (1 if correct else 0)

            if correct:
                streak += 1
                # 连续正确3次跳级
                if streak >= 3 and stage < 5:
                    stage = min(stage + 2, 6)
                    streak = 0
                else:
                    stage = min(stage + 1, 6)
            else:
                stage = 1  # 降回阶段1
                streak = 0

            next_date = str(date.today() + timedelta(days=INTERVALS.get(stage, 30)))
            await db.execute(
                """UPDATE memory_progress SET stage=?, review_date=?, correct_streak=?,
                   total_reviews=?, total_correct=?, last_reviewed=? WHERE card_id=?""",
                (stage, next_date, streak, total_r, total_c, today, card_id))
        else:
            # 新卡首次复习
            stage = 1 if correct else 0
            next_date = str(date.today() + timedelta(days=INTERVALS.get(stage, 1)))
            await db.execute(
                """INSERT INTO memory_progress (card_id, stage, review_date, correct_streak,
                   total_reviews, total_correct, last_reviewed) VALUES (?,?,?,?,?,?,?)""",
                (card_id, stage, next_date, 1 if correct else 0, 1, 1 if correct else 0, today))

        await db.commit()
        return {"ok": True, "new_stage": stage, "next_review": next_date}
    finally:
        await db.close()


@router.get("/stats")
async def memory_stats(subject: str = ""):
    """记忆进度统计"""
    db = await get_db()
    try:
        sub_filter = "AND mc.subject = ?" if subject else ""
        params = (subject,) if subject else ()

        # 各阶段分布
        cursor = await db.execute(
            f"""SELECT mp.stage, COUNT(*) as cnt FROM memory_progress mp
                JOIN memory_cards mc ON mp.card_id = mc.id
                WHERE 1=1 {sub_filter} GROUP BY mp.stage""", params)
        stages = {r["stage"]: r["cnt"] for r in await cursor.fetchall()}

        # 总卡片数
        cursor = await db.execute(
            f"SELECT COUNT(*) as cnt FROM memory_cards mc WHERE 1=1 {sub_filter}", params)
        total = (await cursor.fetchone())["cnt"]

        # 未开始的
        cursor = await db.execute(
            f"""SELECT COUNT(*) as cnt FROM memory_cards mc
                WHERE mc.id NOT IN (SELECT card_id FROM memory_progress)
                {sub_filter}""", params)
        not_started = (await cursor.fetchone())["cnt"]

        mastered = stages.get(6, 0)
        learning = sum(v for k, v in stages.items() if 0 < k < 6)

        return {
            "total": total, "not_started": not_started,
            "learning": learning, "mastered": mastered,
            "stages": stages,
        }
    finally:
        await db.close()


@router.get("/daily-target")
async def get_daily_target():
    """获取每日新卡目标（默认20，家长可调）"""
    from api.settings import _load
    settings = _load()
    return {"daily_new_cards": settings.get("daily_new_cards", 20)}


@router.put("/daily-target")
async def set_daily_target(req: Request):
    """家长设置每日新卡数量"""
    body = await req.json()
    count = max(5, min(100, body.get("count", 20)))
    from api.settings import _load, _save
    settings = _load()
    settings["daily_new_cards"] = count
    _save(settings)
    return {"daily_new_cards": count}
