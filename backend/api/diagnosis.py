"""学情诊断API"""
import json
from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_db
from core.mastery import calc_mastery, get_status, find_weak_prerequisites

router = APIRouter()


class DiagnosisResult(BaseModel):
    node_id: str
    correct: int
    question_id: str
    time_spent_sec: int | None = None
    error_type: str | None = None


@router.get("/overview")
async def get_overview():
    """获取全科掌握度概览"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            "SELECT node_id, mastery, status FROM mastery_summary ORDER BY mastery ASC"
        )
        subjects = {"math": [], "physics": [], "english": []}
        for r in rows:
            node = await db.execute_fetchall(
                "SELECT subject, name, grade FROM knowledge_nodes WHERE node_id=?", (r[0],)
            )
            if node:
                subjects.setdefault(node[0][0], []).append({
                    "node_id": r[0], "name": node[0][1], "mastery": r[1], "status": r[2]
                })
        return subjects
    finally:
        await db.close()


@router.get("/weak-points/{subject}")
async def get_weak_points(subject: str):
    """获取某科的薄弱知识点（掌握度<0.6）"""
    db = await get_db()
    try:
        rows = await db.execute_fetchall(
            """SELECT ms.node_id, ms.mastery, kn.name, kn.prerequisites
               FROM mastery_summary ms
               JOIN knowledge_nodes kn ON ms.node_id = kn.node_id
               WHERE kn.subject=? AND ms.mastery < 0.6
               ORDER BY ms.mastery ASC""",
            (subject,)
        )
        return [{"node_id": r[0], "mastery": r[1], "name": r[2], "prerequisites": json.loads(r[3] or "[]")} for r in rows]
    finally:
        await db.close()


@router.post("/submit")
async def submit_diagnosis(results: list[DiagnosisResult]):
    """提交诊断/做题结果，更新掌握度"""
    db = await get_db()
    try:
        for r in results:
            await db.execute(
                """INSERT INTO mastery_records (node_id, question_id, correct, time_spent_sec, error_type)
                   VALUES (?, ?, ?, ?, ?)""",
                (r.node_id, r.question_id, r.correct, r.time_spent_sec, r.error_type)
            )
        await db.commit()

        # 重算涉及的知识点掌握度
        updated_nodes = set(r.node_id for r in results)
        for node_id in updated_nodes:
            records = await db.execute_fetchall(
                "SELECT correct, question_id FROM mastery_records WHERE node_id=? ORDER BY timestamp",
                (node_id,)
            )
            # 获取题目难度
            record_dicts = []
            for rec in records:
                q = await db.execute_fetchall("SELECT difficulty FROM questions WHERE id=?", (rec[1],))
                record_dicts.append({"correct": rec[0], "difficulty": q[0][0] if q else 1})

            mastery = calc_mastery(record_dicts)
            status = get_status(mastery)
            total = len(records)
            correct_count = sum(1 for rec in records if rec[0] == 1)

            await db.execute(
                """INSERT OR REPLACE INTO mastery_summary (node_id, mastery, status, last_practice, total_attempts, correct_rate)
                   VALUES (?, ?, ?, datetime('now'), ?, ?)""",
                (node_id, mastery, status, total, correct_count / total if total else 0)
            )
        await db.commit()

        # 对低分知识点追溯前置
        nodes_data = await db.execute_fetchall("SELECT node_id, prerequisites FROM knowledge_nodes")
        nodes_map = {r[0]: {"prerequisites": r[1]} for r in nodes_data}
        mastery_rows = await db.execute_fetchall("SELECT node_id, mastery FROM mastery_summary")
        mastery_map = {r[0]: r[1] for r in mastery_rows}

        weak_prereqs = []
        for node_id in updated_nodes:
            if mastery_map.get(node_id, 0) < 0.5:
                weak_prereqs.extend(find_weak_prerequisites(node_id, nodes_map, mastery_map))

        return {"updated": list(updated_nodes), "weak_prerequisites": weak_prereqs}
    finally:
        await db.close()
