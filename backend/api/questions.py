"""题库与做题API"""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_db
from core.question_selector import select_questions
from core.mastery import next_review_date, calc_mastery, get_status

router = APIRouter()


async def _recompute_daily_stats(db):
    """根据当日 mastery_records 重算 daily_stats（家长看板数据源）。
    按学科聚合做题数/正确数/时长；math/physics/english 单列存正确率与时长，
    其余学科计入总数。单用户、每次答题重算，开销可忽略。"""
    cursor = await db.execute(
        """SELECT kn.subject AS subject, mr.correct AS correct,
                  COALESCE(mr.time_spent_sec, 0) AS secs
           FROM mastery_records mr
           JOIN knowledge_nodes kn ON mr.node_id = kn.node_id
           WHERE date(mr.timestamp) = date('now')"""
    )
    rows = await cursor.fetchall()
    total = len(rows)
    correct = sum(1 for r in rows if r["correct"] == 1)
    # 按学科聚合
    agg: dict[str, dict] = {}
    for r in rows:
        s = agg.setdefault(r["subject"], {"t": 0, "c": 0, "secs": 0})
        s["t"] += 1
        s["c"] += r["correct"]
        s["secs"] += r["secs"]

    def rate(s):
        d = agg.get(s)
        return (d["c"] / d["t"]) if d and d["t"] else None

    def mins(s):
        d = agg.get(s)
        return round((d["secs"] / 60)) if d else 0

    await db.execute(
        """INSERT OR REPLACE INTO daily_stats
           (date, math_minutes, physics_minutes, english_minutes,
            math_correct_rate, physics_correct_rate, english_correct_rate,
            questions_total, questions_correct, nodes_learned)
           VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?, ?, '[]')""",
        (mins("math"), mins("physics"), mins("english"),
         rate("math"), rate("physics"), rate("english"),
         total, correct)
    )


@router.get("/practice/{node_id}")
async def get_practice_questions(node_id: str, count: int = 5):
    """获取某知识点的练习题（智能选题）"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT mastery FROM mastery_summary WHERE node_id=?", (node_id,))
        row = await cursor.fetchone()
        mastery = row["mastery"] if row else 0.0

        cursor = await db.execute(
            "SELECT question_id FROM error_book WHERE node_id=? AND next_review <= date('now')",
            (node_id,)
        )
        error_rows = await cursor.fetchall()
        error_ids = [r["question_id"] for r in error_rows]

        cursor = await db.execute(
            "SELECT id, node_id, type, difficulty, question, options, answer, steps, common_errors, figure_url, figure_description FROM questions WHERE node_id=?",
            (node_id,)
        )
        q_rows = await cursor.fetchall()
        available = [
            {"id": r["id"], "node_id": r["node_id"], "type": r["type"], "difficulty": r["difficulty"],
             "question": r["question"], "options": json.loads(r["options"] or "[]"),
             "answer": r["answer"], "steps": json.loads(r["steps"] or "[]"),
             "common_errors": json.loads(r["common_errors"] or "[]"),
             "figure_url": r["figure_url"] or "", "figure_description": r["figure_description"] or ""}
            for r in q_rows
        ]

        selected = select_questions(available, mastery, count, error_ids)
        # 返回时不暴露答案
        for q in selected:
            q.pop("answer", None)
            q.pop("steps", None)
            q.pop("common_errors", None)
        return {"node_id": node_id, "mastery": mastery, "questions": selected}
    finally:
        await db.close()


@router.get("/nodes/{subject}")
async def get_available_nodes(subject: str):
    """获取有题目的知识点列表（供前端选题）"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT kn.node_id, kn.name, kn.chapter, COUNT(q.id) as q_count,
                      COALESCE(ms.mastery, 0) as mastery, COALESCE(ms.status, 'not_started') as status
               FROM knowledge_nodes kn
               LEFT JOIN questions q ON kn.node_id = q.node_id
               LEFT JOIN mastery_summary ms ON kn.node_id = ms.node_id
               WHERE kn.subject=?
               GROUP BY kn.node_id
               HAVING q_count > 0
               ORDER BY kn.semester, kn.node_id""",
            (subject,)
        )
        rows = await cursor.fetchall()
        return [{"node_id": r["node_id"], "name": r["name"], "chapter": r["chapter"],
                 "question_count": r["q_count"], "mastery": r["mastery"], "status": r["status"]}
                for r in rows]
    finally:
        await db.close()


class AnswerSubmit(BaseModel):
    question_id: str
    node_id: str
    user_answer: str
    time_spent_sec: int | None = None


@router.post("/check")
async def check_answer(submit: AnswerSubmit):
    """检查答案，返回对错+错因分析"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT answer, steps, common_errors, difficulty FROM questions WHERE id=?", (submit.question_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return {"error": "question not found"}

        correct_answer = row["answer"]
        steps = json.loads(row["steps"] or "[]")
        common_errors = json.loads(row["common_errors"] or "[]")

        # 简单匹配（去空格后比较）
        is_correct = submit.user_answer.strip().replace(" ", "") == correct_answer.strip().replace(" ", "")

        error_type = None
        hint = None
        if not is_correct:
            # 尝试匹配错因
            for err in common_errors:
                if isinstance(err, dict):
                    error_type = err.get("error")
                    hint = err.get("hint")
                    break

            # 加入错题本
            cursor = await db.execute(
                "SELECT id, error_count, review_stage FROM error_book WHERE question_id=?",
                (submit.question_id,)
            )
            existing = await cursor.fetchone()
            if existing:
                await db.execute(
                    "UPDATE error_book SET error_count=error_count+1, review_stage=0, next_review=? WHERE question_id=?",
                    (next_review_date(0), submit.question_id)
                )
            else:
                await db.execute(
                    "INSERT INTO error_book (question_id, node_id, error_type, next_review) VALUES (?,?,?,?)",
                    (submit.question_id, submit.node_id, error_type, next_review_date(0))
                )
        else:
            # 答对：推进错题本复习阶段
            cursor = await db.execute(
                "SELECT id, review_stage FROM error_book WHERE question_id=?", (submit.question_id,)
            )
            existing = await cursor.fetchone()
            if existing:
                new_stage = min(existing["review_stage"] + 1, 4)
                if new_stage >= 4:
                    await db.execute("DELETE FROM error_book WHERE question_id=?", (submit.question_id,))
                else:
                    await db.execute(
                        "UPDATE error_book SET review_stage=?, next_review=? WHERE question_id=?",
                        (new_stage, next_review_date(new_stage), submit.question_id)
                    )

        # 记录到mastery_records
        await db.execute(
            """INSERT INTO mastery_records (node_id, question_id, correct, time_spent_sec, error_type)
               VALUES (?, ?, ?, ?, ?)""",
            (submit.node_id, submit.question_id, 1 if is_correct else 0, submit.time_spent_sec, error_type)
        )

        # 重算该知识点掌握度汇总
        cursor = await db.execute(
            "SELECT correct, question_id FROM mastery_records WHERE node_id=? ORDER BY timestamp",
            (submit.node_id,)
        )
        records = await cursor.fetchall()
        record_dicts = []
        for rec in records:
            cur2 = await db.execute("SELECT difficulty FROM questions WHERE id=?", (rec["question_id"],))
            q = await cur2.fetchone()
            record_dicts.append({"correct": rec["correct"], "difficulty": q["difficulty"] if q else 1})

        mastery = calc_mastery(record_dicts)
        status = get_status(mastery)
        total = len(records)
        correct_count = sum(1 for rec in records if rec["correct"] == 1)
        await db.execute(
            """INSERT OR REPLACE INTO mastery_summary (node_id, mastery, status, last_practice, total_attempts, correct_rate)
               VALUES (?, ?, ?, datetime('now'), ?, ?)""",
            (submit.node_id, mastery, status, total, correct_count / total if total else 0)
        )
        await db.commit()

        # 更新当日学习统计（家长看板数据源）
        await _recompute_daily_stats(db)
        await db.commit()

        return {
            "correct": is_correct,
            "correct_answer": correct_answer,
            "steps": steps,
            "error_type": error_type,
            "hint": hint,
            "mastery": mastery,
        }
    finally:
        await db.close()


@router.get("/error-book")
async def get_error_book(node_id: str | None = None):
    """获取错题本"""
    db = await get_db()
    try:
        if node_id:
            query = """SELECT eb.*, q.question, q.node_id, kn.name as node_name
                       FROM error_book eb
                       JOIN questions q ON eb.question_id = q.id
                       JOIN knowledge_nodes kn ON q.node_id = kn.node_id
                       WHERE eb.node_id=? ORDER BY eb.next_review"""
            cursor = await db.execute(query, (node_id,))
        else:
            query = """SELECT eb.*, q.question, q.node_id, kn.name as node_name
                       FROM error_book eb
                       JOIN questions q ON eb.question_id = q.id
                       JOIN knowledge_nodes kn ON q.node_id = kn.node_id
                       ORDER BY eb.next_review"""
            cursor = await db.execute(query)
        rows = await cursor.fetchall()
        return [{"question_id": r["question_id"], "node_id": r["node_id"],
                 "node_name": r["node_name"], "question": r["question"],
                 "error_type": r["error_type"], "error_count": r["error_count"],
                 "review_stage": r["review_stage"], "next_review": r["next_review"]}
                for r in rows]
    finally:
        await db.close()
