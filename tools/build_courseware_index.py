"""从 teachany.cn 的 node-index.json 提取各节点课件清单，生成精简索引。

输出 data/courseware-index.json:
  { node_id: [ {id, name, download_url}, ... ], ... }

供课件库浏览与缺口报告使用（自包含，运行时不依赖 teachany.cn）。
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "courseware-index.json"
SUBJECTS = {"math", "physics", "chemistry", "english", "chinese",
            "biology", "geography", "history", "politics"}
URLS = [
    "https://www.teachany.cn/data/node-index.json",
    "https://cdn.jsdelivr.net/gh/weponusa/teachany-courseware@main/data/node-index.json",
]


def fetch():
    for u in URLS:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"  ✗ {u}: {e}")
    return None


def main():
    d = fetch()
    if not d:
        print("无法获取 node-index.json"); return
    nodes = d.get("nodes", {})
    index = {}
    for nid, n in nodes.items():
        if n.get("stage") != "middle" or n.get("subject") not in SUBJECTS:
            continue
        courses = n.get("courses") or []
        if courses:
            index[nid] = [
                {"id": c.get("id"), "name": c.get("name_zh") or c.get("name"),
                 "download_url": c.get("download_url")}
                for c in courses
            ]
    OUT.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    total_courses = sum(len(v) for v in index.values())
    print(f"✅ 课件索引: {len(index)} 个节点有课件，共 {total_courses} 个课件 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
