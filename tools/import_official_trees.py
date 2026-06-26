"""从 TeachAny 官方拉取初中全科课标树，转换为本系统 tree.json 格式。

- 数据源：teachany.cn / jsDelivr / raw.githubusercontent（按序回退）
- 保留各学科 tree.json 已有的 exam_weight / exam_points（武汉考频校准，不被覆盖）
- 输出：data/<subject>/tree.json
"""
import json
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# 远程 data/ 根（按序回退）
REMOTE_BASES = [
    "https://www.teachany.cn/data/",
    "https://cdn.jsdelivr.net/gh/weponusa/teachany-courseware@main/data/",
    "https://raw.githubusercontent.com/weponusa/teachany-courseware/main/data/",
]

# 初中全科：subject_key -> 官方树相对路径
SUBJECTS = {
    "chinese":    "trees/cn/middle/chinese.json",
    "math":       "trees/cn/middle/math.json",
    "english":    "trees/cn/middle/english.json",
    "physics":    "trees/cn/middle/physics.json",
    "chemistry":  "trees/cn/middle/chemistry.json",
    "biology":    "trees/cn/middle/biology.json",
    "geography":  "trees/cn/middle/geography.json",
    "history":    "trees/cn/middle/history.json",
    "politics":   "trees/cn/middle/politics.json",
    "psychology": "trees/cn/middle/psychology.json",
}

SEM = {"上": 1, "下": 2, "七上": 1, "八上": 1, "八下": 2, "九上": 1, "九下": 2, "七上/八上": 1, "": 1}


def fetch_json(rel_path: str):
    last_err = None
    for base in REMOTE_BASES:
        url = base + rel_path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last_err = e
            continue
    print(f"  ⚠️ 拉取失败 {rel_path}: {last_err}")
    return None


def load_existing_weights(subject: str) -> dict:
    """读取已有 tree.json 的 exam_weight/exam_points（保留武汉校准）"""
    f = DATA_DIR / subject / "tree.json"
    weights = {}
    if f.exists():
        try:
            for n in json.loads(f.read_text(encoding="utf-8")):
                weights[n["node_id"]] = (n.get("exam_weight", "medium"), n.get("exam_points", ""))
        except Exception:
            pass
    return weights


def convert(subject: str, tree: dict, weights: dict) -> list:
    nodes_out = []
    for dom in tree.get("domains", []):
        for n in dom.get("nodes", []):
            nid = n["id"]
            ew, ep = weights.get(nid, ("medium", ""))
            sem_raw = (n.get("textbook_semester") or "").strip()
            nodes_out.append({
                "node_id": nid,
                "subject": subject,
                "name": n["name"],
                "grade": n.get("grade"),
                "semester": SEM.get(sem_raw, 1),
                "chapter": n.get("textbook_chapter", ""),
                "prerequisites": n.get("prerequisites", []),
                "exam_weight": ew,
                "exam_points": ep,
                "estimated_minutes": 40,
                "teachany_node": nid,
                "domain": dom.get("id", ""),
                "curriculum_points": n.get("curriculum_points", []),
            })
    nodes_out.sort(key=lambda x: (x["grade"] or 0, x["semester"], x["domain"], x["node_id"]))
    return nodes_out


def main():
    only = sys.argv[1:] or list(SUBJECTS.keys())
    total = 0
    for subject in only:
        rel = SUBJECTS.get(subject)
        if not rel:
            print(f"  跳过未知学科: {subject}")
            continue
        tree = fetch_json(rel)
        if not tree:
            continue
        weights = load_existing_weights(subject)
        nodes = convert(subject, tree, weights)
        out_dir = DATA_DIR / subject
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "tree.json").write_text(
            json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        kept = sum(1 for n in nodes if n["exam_weight"] != "medium" or n["exam_points"])
        print(f"  ✅ {subject:<11} {len(nodes):>3} 节点  (保留考频校准 {kept})")
        total += len(nodes)
    print(f"\n全科合计 {total} 节点，已写入 data/<subject>/tree.json")


if __name__ == "__main__":
    main()
