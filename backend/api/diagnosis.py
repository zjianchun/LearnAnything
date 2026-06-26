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
        cursor = await db.execute(
            "SELECT node_id, mastery, status FROM mastery_summary ORDER BY mastery ASC"
        )
        rows = await cursor.fetchall()
        subjects: dict[str, list] = {"math": [], "physics": [], "english": []}
        for r in rows:
            cur2 = await db.execute(
                "SELECT subject, name, grade FROM knowledge_nodes WHERE node_id=?", (r["node_id"],)
            )
            node = await cur2.fetchone()
            if node:
                subjects.setdefault(node["subject"], []).append({
                    "node_id": r["node_id"], "name": node["name"],
                    "mastery": r["mastery"], "status": r["status"]
                })
        return subjects
    finally:
        await db.close()


@router.get("/weak-points/{subject}")
async def get_weak_points(subject: str):
    """获取某科的薄弱知识点（掌握度<0.6）"""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT ms.node_id, ms.mastery, kn.name, kn.prerequisites
               FROM mastery_summary ms
               JOIN knowledge_nodes kn ON ms.node_id = kn.node_id
               WHERE kn.subject=? AND ms.mastery < 0.6
               ORDER BY ms.mastery ASC""",
            (subject,)
        )
        rows = await cursor.fetchall()
        return [{"node_id": r["node_id"], "mastery": r["mastery"],
                 "name": r["name"], "prerequisites": json.loads(r["prerequisites"] or "[]")}
                for r in rows]
    finally:
        await db.close()


@router.get("/generate/{subject}")
async def generate_diagnosis(subject: str, count_per_node: int = 2):
    """生成入学诊断卷：每个知识点出count_per_node题"""
    db = await get_db()
    try:
        # 获取该学科所有8年级知识点
        cursor = await db.execute(
            "SELECT node_id, name, chapter FROM knowledge_nodes WHERE subject=? AND grade=8 ORDER BY semester, node_id",
            (subject,)
        )
        nodes = await cursor.fetchall()

        diagnosis_questions = []
        for node in nodes:
            cur2 = await db.execute(
                "SELECT id, node_id, type, difficulty, question, options FROM questions WHERE node_id=? ORDER BY difficulty LIMIT ?",
                (node["node_id"], count_per_node)
            )
            qs = await cur2.fetchall()
            for q in qs:
                diagnosis_questions.append({
                    "id": q["id"], "node_id": q["node_id"], "node_name": node["name"],
                    "chapter": node["chapter"], "type": q["type"], "difficulty": q["difficulty"],
                    "question": q["question"], "options": json.loads(q["options"] or "[]")
                })

        return {"subject": subject, "total": len(diagnosis_questions),
                "questions": diagnosis_questions}
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
        mastery_results = []
        for node_id in updated_nodes:
            cursor = await db.execute(
                "SELECT correct, question_id FROM mastery_records WHERE node_id=? ORDER BY timestamp",
                (node_id,)
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
                (node_id, mastery, status, total, correct_count / total if total else 0)
            )
            mastery_results.append({"node_id": node_id, "mastery": mastery, "status": status})
        await db.commit()

        # 对低分知识点追溯前置
        cursor = await db.execute("SELECT node_id, prerequisites FROM knowledge_nodes")
        nodes_data = await cursor.fetchall()
        nodes_map = {r["node_id"]: {"prerequisites": r["prerequisites"]} for r in nodes_data}

        cursor = await db.execute("SELECT node_id, mastery FROM mastery_summary")
        mastery_rows = await cursor.fetchall()
        mastery_map = {r["node_id"]: r["mastery"] for r in mastery_rows}

        weak_prereqs = []
        for node_id in updated_nodes:
            if mastery_map.get(node_id, 0) < 0.5:
                weak_prereqs.extend(find_weak_prerequisites(node_id, nodes_map, mastery_map))

        return {"updated": mastery_results, "weak_prerequisites": weak_prereqs}
    finally:
        await db.close()
