"""Initialize database with schema and load question data."""
import sqlite3, json, os
from pathlib import Path

DB_DIR = Path("/app/db")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "learn.db"
DATA_DIR = Path("/app/data")
SCHEMA_PATH = Path("/app/db/schema.sql")

def main():
    conn = sqlite3.connect(str(DB_PATH))
    # Apply schema
    if SCHEMA_PATH.exists():
        conn.executescript(SCHEMA_PATH.read_text())
        print(f"  ✅ Schema applied")

    # Load questions
    total = 0
    for qfile in sorted(DATA_DIR.rglob("questions-*.json")):
        questions = json.loads(qfile.read_text())
        for q in questions:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO questions (id, node_id, type, difficulty, question, options, correct_answer, hint, steps)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (q.get("id"), q.get("node_id"), q.get("type", "choice"),
                     q.get("difficulty", 1), q.get("question", ""),
                     json.dumps(q.get("options", []), ensure_ascii=False),
                     q.get("correct_answer", ""), q.get("hint", ""),
                     json.dumps(q.get("steps", []), ensure_ascii=False))
                )
                total += 1
            except Exception:
                pass
    conn.commit()
    conn.close()
    print(f"  ✅ Loaded {total} questions")

if __name__ == "__main__":
    main()
