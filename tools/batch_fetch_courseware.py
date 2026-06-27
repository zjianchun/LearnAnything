"""批量拉取全科课件 — 按考频缺口优先。

用法: python3 tools/batch_fetch_courseware.py [--limit N] [--subject SUBJECT]

按 exam_weight(high>medium>low) + grade 排序，跳过已自托管的。
"""
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
CW_DIR = ROOT / "courseware"
CW_INDEX = json.loads((ROOT / "data" / "courseware-index.json").read_text())

# 加载节点元数据
node_meta = {}
for tf in (ROOT / "data").rglob("tree.json"):
    for n in json.loads(tf.read_text()):
        node_meta[n["node_id"]] = n

WEIGHT_RANK = {"high": 0, "medium": 1, "low": 2}


def is_hosted(subject, course_id):
    return (CW_DIR / subject / course_id / "index.html").exists()


def build_queue(subject_filter=None):
    queue = []
    for nid, courses in CW_INDEX.items():
        meta = node_meta.get(nid, {})
        sub = meta.get("subject")
        if not sub:
            continue
        if subject_filter and sub != subject_filter:
            continue
        for c in courses:
            cid = c["id"]
            if is_hosted(sub, cid):
                continue
            queue.append({
                "node_id": nid,
                "subject": sub,
                "course_id": cid,
                "name": c.get("name", ""),
                "exam_weight": meta.get("exam_weight", "medium"),
                "grade": meta.get("grade", 8),
            })
    queue.sort(key=lambda x: (WEIGHT_RANK.get(x["exam_weight"], 1), x["grade"]))
    return queue


def fetch_one(course_id, subject, node_id):
    """调用已有的fetch_courseware.py"""
    cmd = [sys.executable, str(ROOT / "tools" / "fetch_courseware.py"),
           course_id, subject, node_id]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0, r.stdout + r.stderr


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="最多拉取数，0=全部")
    parser.add_argument("--subject", type=str, default=None)
    args = parser.parse_args()

    queue = build_queue(args.subject)
    total = len(queue)
    limit = args.limit or total
    print(f"📦 待拉取课件: {total} 个 (本次最多 {limit})")
    print(f"   优先级: 考频高→年级低\n")

    ok = 0
    fail = 0
    for i, item in enumerate(queue[:limit]):
        print(f"[{i+1}/{min(limit,total)}] [{item['exam_weight']}] {item['subject']}/{item['course_id']}  {item['name']}")
        success, output = fetch_one(item["course_id"], item["subject"], item["node_id"])
        if success:
            ok += 1
            print(f"  ✅")
        else:
            fail += 1
            # 提取错误摘要
            err_line = [l for l in output.split("\n") if "error" in l.lower() or "✗" in l]
            print(f"  ✗ {err_line[0] if err_line else 'failed'}")
        # 礼貌延迟
        if i < limit - 1:
            time.sleep(0.5)

    print(f"\n{'='*40}")
    print(f"完成: {ok} 成功, {fail} 失败, 共 {ok+fail}/{min(limit,total)}")


if __name__ == "__main__":
    main()
