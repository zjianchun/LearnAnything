"""将知识树和题库JSON导入SQLite数据库"""
import json
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from db.database import init_db, get_db

# Docker 中 data 挂载在 /app/data，本地则在项目根目录
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data"))


async def load_tree(db, filepath: Path):
    nodes = json.loads(filepath.read_text(encoding="utf-8"))
    for n in nodes:
        await db.execute(
            """INSERT OR REPLACE INTO knowledge_nodes
               (node_id, subject, name, grade, semester, chapter, prerequisites, exam_weight, exam_points, estimated_minutes, teachany_node, curriculum_points)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (n["node_id"], n["subject"], n["name"], n["grade"], n["semester"],
             n["chapter"], json.dumps(n["prerequisites"], ensure_ascii=False),
             n["exam_weight"], n["exam_points"], n["estimated_minutes"],
             n.get("teachany_node"), json.dumps(n.get("curriculum_points", []), ensure_ascii=False))
        )
    print(f"  loaded {len(nodes)} nodes from {filepath.name}")


async def load_questions(db, filepath: Path):
    questions = json.loads(filepath.read_text(encoding="utf-8"))
    for q in questions:
        await db.execute(
            """INSERT OR REPLACE INTO questions
               (id, node_id, source, type, difficulty, question, options, answer, steps, common_errors, tags, exam_frequency)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (q["id"], q["node_id"], q.get("source"), q["type"], q["difficulty"],
             q["question"], json.dumps(q.get("options", []), ensure_ascii=False),
             q["answer"], json.dumps(q.get("steps", []), ensure_ascii=False),
             json.dumps(q.get("common_errors", []), ensure_ascii=False),
             json.dumps(q.get("tags", []), ensure_ascii=False), q.get("exam_frequency", 0))
        )
    print(f"  loaded {len(questions)} questions from {filepath.name}")


async def main():
    await init_db()
    db = await get_db()
    try:
        for tree_file in DATA_DIR.rglob("tree.json"):
            await load_tree(db, tree_file)
        for q_file in DATA_DIR.rglob("questions-*.json"):
            await load_questions(db, q_file)
        await db.commit()
        print("✅ Data loaded successfully!")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
