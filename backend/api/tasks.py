"""家长任务系统 API"""
import json
from datetime import date, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from db.database import get_db

router = APIRouter()


@router.post("/create")
async def create_task(req: Request):
    body = await req.json()
    title = body.get("title", "").strip()
    if not title:
        return JSONResponse(status_code=400, content={"error": "需要title"})

    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO tasks (title, type, subject, node_id, target_count,
               deadline, repeat_frequency, repeat_end, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, body.get("type", "custom"), body.get("subject"),
             body.get("node_id"), body.get("target_count", 0),
             body.get("deadline", str(date.today())),
             body.get("repeat_frequency"), body.get("repeat_end"),
             body.get("note"))
        )
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()


@router.get("/list")
async def list_tasks(status: str = "all"):
    db = await get_db()
    try:
        if status == "all":
            cursor = await db.execute("SELECT * FROM tasks ORDER BY created_at DESC")
        else:
            cursor = await db.execute("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC", (status,))
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


@router.get("/today")
async def today_tasks():
    """学生获取今日待完成任务"""
    today = str(date.today())
    db = await get_db()
    try:
        # 活跃任务: deadline >= today 且未完成
        cursor = await db.execute(
            """SELECT * FROM tasks WHERE status='active' AND deadline >= ?
               ORDER BY deadline ASC""", (today,))
        active = [dict(r) for r in await cursor.fetchall()]

        # 循环任务: 每天/每周重复的
        cursor = await db.execute(
            """SELECT * FROM tasks WHERE repeat_frequency IS NOT NULL
               AND status='active' AND (repeat_end IS NULL OR repeat_end >= ?)
               ORDER BY created_at DESC""", (today,))
        recurring = [dict(r) for r in await cursor.fetchall()]

        # 过期标红
        cursor = await db.execute(
            """SELECT * FROM tasks WHERE status='active' AND deadline < ?""", (today,))
        expired = [dict(r) for r in await cursor.fetchall()]
        for t in expired:
            t["overdue"] = True

        # 合并去重
        seen = set()
        result = []
        for t in expired + active:
            if t["id"] not in seen:
                seen.add(t["id"])
                if t.get("deadline", "") < today:
                    t["overdue"] = True
                result.append(t)

        return result
    finally:
        await db.close()


@router.post("/{task_id}/complete")
async def complete_task(task_id: int, req: Request):
    body = await req.json() if req.headers.get("content-type") else {}
    db = await get_db()
    try:
        await db.execute(
            """UPDATE tasks SET status='completed', completed_at=datetime('now','localtime'),
               result_data=? WHERE id=?""",
            (json.dumps(body.get("result", {}), ensure_ascii=False), task_id)
        )
        await db.commit()

        # 如果是循环任务，生成下一个
        cursor = await db.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        task = await cursor.fetchone()
        if task and task["repeat_frequency"]:
            freq = task["repeat_frequency"]
            old_deadline = task["deadline"]
            if freq == "daily":
                new_deadline = str(date.fromisoformat(old_deadline) + timedelta(days=1))
            else:
                new_deadline = str(date.fromisoformat(old_deadline) + timedelta(weeks=1))

            repeat_end = task["repeat_end"]
            if not repeat_end or new_deadline <= repeat_end:
                await db.execute(
                    """INSERT INTO tasks (title, type, subject, node_id, target_count,
                       deadline, repeat_frequency, repeat_end, note)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (task["title"], task["type"], task["subject"], task["node_id"],
                     task["target_count"], new_deadline, freq, repeat_end, task["note"])
                )
                await db.commit()

        return {"ok": True}
    finally:
        await db.close()


@router.delete("/{task_id}")
async def delete_task(task_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        await db.commit()
        return {"ok": True}
    finally:
        await db.close()
