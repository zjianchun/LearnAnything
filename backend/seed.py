"""Initialize database with schema, knowledge trees, questions, and memory cards."""
import sqlite3, json
from pathlib import Path

DB_DIR = Path("/app/db")
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "learn.db"
DATA_DIR = Path("/app/data")
SCHEMA_PATH = Path("/app/db/schema.sql")


def main():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")

    # 1. Apply schema
    if SCHEMA_PATH.exists():
        conn.executescript(SCHEMA_PATH.read_text())
        print("  ✅ Schema applied")
    else:
        print("  ❌ schema.sql not found!")
        return

    # 2. Load knowledge trees
    tree_total = 0
    for tree_file in sorted(DATA_DIR.rglob("tree.json")):
        nodes = json.loads(tree_file.read_text())
        for node in nodes:
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO knowledge_nodes
                       (node_id, subject, name, grade, semester, chapter, prerequisites,
                        exam_weight, exam_points, estimated_minutes, teachany_node, domain, curriculum_points)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (node.get("node_id"), node.get("subject"), node.get("name"),
                     node.get("grade"), node.get("semester"), node.get("chapter", ""),
                     json.dumps(node.get("prerequisites", []), ensure_ascii=False),
                     node.get("exam_weight", ""), node.get("exam_points", ""),
                     node.get("estimated_minutes", 40), node.get("teachany_node", ""),
                     node.get("domain", ""),
                     json.dumps(node.get("curriculum_points", []), ensure_ascii=False))
                )
                tree_total += 1
            except Exception as e:
                pass
    conn.commit()
    print(f"  ✅ Loaded {tree_total} knowledge nodes")

    # 3. Load questions
    q_total = 0
    for qfile in sorted(DATA_DIR.rglob("questions-*.json")):
        questions = json.loads(qfile.read_text())
        for q in questions:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO questions (id, node_id, source, type, difficulty, question, options, answer, steps, common_errors, figure_url, figure_description)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (q.get("id"), q.get("node_id"), q.get("source", ""),
                     q.get("type", "choice"), q.get("difficulty", 1),
                     q.get("question", ""),
                     json.dumps(q.get("options", []), ensure_ascii=False),
                     q.get("answer") or q.get("correct_answer", ""),
                     json.dumps(q.get("steps", []), ensure_ascii=False),
                     json.dumps(q.get("common_errors", []), ensure_ascii=False),
                     q.get("figure_url", ""),
                     q.get("figure_description", ""))
                )
                q_total += 1
            except Exception:
                pass
    conn.commit()
    print(f"  ✅ Loaded {q_total} questions")

    # 4. Load memory cards
    cards_file = DATA_DIR / "memory-cards.json"
    mc_total = 0
    if cards_file.exists():
        cards = json.loads(cards_file.read_text())
        for c in cards:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO memory_cards (id, front, back, subject, category, difficulty, audio_url)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (c.get("id"), c.get("front"), c.get("back"),
                     c.get("subject"), c.get("category"),
                     c.get("difficulty", 1), c.get("audio_url"))
                )
                mc_total += 1
            except Exception:
                pass
        conn.commit()
    print(f"  ✅ Loaded {mc_total} memory cards")

    conn.close()
    print(f"\n  🎉 Seed complete: {tree_total} nodes, {q_total} questions, {mc_total} cards")


if __name__ == "__main__":
    main()
