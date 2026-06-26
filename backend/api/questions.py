"""题库与做题API"""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_db
from core.question_selector import select_questions
from core.mastery import next_review_date

router = APIRouter()


@router.get("/practice/{node_id}")
async def get_practice_questions(node_id: str, count: int = 5):
    """获取某知识点的练习题（智能选题）"""
    db = await get_db()
    try:
        # 当前掌握度
        row = await db.execute_fetchall("SELECT mastery FROM mastery_summary WHERE node_id=?", (node_id,))
        mastery = row[0][0] if row else 0.0

        # 错题本中到期的题
        error_rows = await db.execute_fetchall(
            "SELECT question_id FROM error_book WHERE node_id=? AND next_review <= date('now')",
            (node_id,)
        )
        error_ids = [r[0] for r in error_rows]

        # 可用题目
        q_rows = await db.execute_fetchall(
            "SELECT id, node_id, type, difficulty, question, options, answer, steps, common_errors FROM questions WHERE node_id=?",
            (node_id,)
        )
        available = [
            {"id": r[0], "node_id": r[1], "type": r[2], "difficulty": r[3],
             "question": r[4], "options": json.loads(r[5] or "[]"),
             "answer": r[6], "steps": json.loads(r[7] or "[]"),
             "common_errors": json.loads(r[8] or "[]")}
            for r in q_rows
        ]

        selected = select_questions(available, mastery, count, error_ids)
        # 返回时不暴露答案
        for q in selected:
            q.pop("answer", None)
            q.pop("steps", None)
        return {"node_id": node_id, "mastery": mastery, "questions": selected}
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
        row = await db.execute_fetchall(
            "SELECT answer, steps, common_errors FROM questions WHERE id=?", (submit.question_id,)
        )
        if not row:
            return {"error": "question not found"}

        correct_answer = row[0][0]
        steps = json.loads(row[0][1] or "[]")
        common_errors = json.loads(row[0][2] or "[]")

        is_correct = submit.user_answer.strip() == correct_answer.strip()

        # 错因匹配
        error_type = None
        hint = None
        if not is_correct:
            for err in common_errors:
                if isinstance(err, dict):
                    error_type = err.get("error")
                    hint = err.get("hint")
                    break

            # 加入错题本
            existing = await db.execute_fetchall(
                "SELECT id, error_count, review_stage FROM error_book WHERE question_id=?",
                (submit.question_id,)
            )
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
            # 答对了，推进错题本复习阶段
            existing = await db.execute_fetchall(
                "SELECT id, review_stage FROM error_book WHERE question_id=?", (submit.question_id,)
            )
            if existing:
                new_stage = min(existing[0][1] + 1, 4)
                if new_stage >= 4:
                    await db.execute("DELETE FROM error_book WHERE question_id=?", (submit.question_id,))
                else:
                    await db.execute(
                        "UPDATE error_book SET review_stage=?, next_review=? WHERE question_id=?",
                        (new_stage, next_review_date(new_stage), submit.question_id)
                    )

        await db.commit()

        return {
            "correct": is_correct,
            "correct_answer": correct_answer,
            "steps": steps,
            "error_type": error_type,
            "hint": hint,
        }
    finally:
        await db.close()
