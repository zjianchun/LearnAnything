"""AI批量生成题库 — 按知识点+考频+难度梯度生成。

用法: python3 tools/gen_questions.py [--subject SUBJECT] [--limit N] [--skip-existing]

每节点生成6-10道题(高频10道,中频8道,低频6道)，含选择/填空/解答混合。
输出: data/<subject>/questions-<node_id_suffix>.json
"""
import json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import httpx

API_KEY = os.environ.get("MINIMAX_API_KEY", "")
API_BASE = os.environ.get("TUTOR_UPSTREAM_BASE", "https://api.minimaxi.com/v1")
MODEL = os.environ.get("TUTOR_MODEL", "MiniMax-Text-01")

SUBJECT_ZH = {
    "math": "数学", "physics": "物理", "chemistry": "化学", "english": "英语",
    "chinese": "语文", "biology": "生物", "geography": "地理", "history": "历史",
    "politics": "道德与法治",
}

PROMPT_TEMPLATE = """你是一位资深初中{subject_zh}教师，正在为武汉市中考备考出题。

请为知识点「{node_name}」生成{count}道练习题，要求：
1. 难度梯度：{count}道中包含基础题{basic}道、中等题{medium}道、拔高题{hard}道
2. 题型混合：选择题(choice)、填空题(fill)、解答题(short_answer)都要有
3. 贴近武汉中考真题风格，注重考频考点
4. 每道题包含详细解题步骤和常见错误

输出严格JSON数组格式（不要markdown代码块），每道题结构：
{{
  "id": "{node_id}-q-{{}}", 
  "node_id": "{node_id}",
  "source": "AI生成-武汉中考风格",
  "type": "choice|fill|short_answer",
  "difficulty": 1-3,
  "question": "题目文本",
  "options": ["A选项","B选项","C选项","D选项"],  // 选择题必须有，其他类型省略此字段
  "answer": "正确答案",
  "steps": ["步骤1","步骤2","步骤3"],
  "common_errors": [{{"error":"常见错误","hint":"纠正提示"}}],
  "exam_frequency": {exam_freq}
}}

id中序号用3位数字如001,002...。选择题answer填完整选项文本。填空题answer填答案。解答题answer填完整解答过程。
只输出JSON数组，不要其他文字。"""


def gen_for_node(node: dict, client: httpx.Client) -> list:
    ew = node.get("exam_weight", "medium")
    count = {"high": 10, "medium": 8, "low": 6}.get(ew, 8)
    basic = count // 3
    hard = count // 4
    medium = count - basic - hard
    exam_freq = {"high": 4, "medium": 3, "low": 2}.get(ew, 3)

    prompt = PROMPT_TEMPLATE.format(
        subject_zh=SUBJECT_ZH.get(node["subject"], node["subject"]),
        node_name=node["name"],
        count=count, basic=basic, medium=medium, hard=hard,
        node_id=node["node_id"], exam_freq=exam_freq,
    )

    resp = client.post(
        f"{API_BASE}/chat/completions",
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 4000, "temperature": 0.7},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=120,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    # 清理可能的markdown代码块
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    return json.loads(content)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=str, default=None)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--skip-existing", action="store_true", default=True)
    args = parser.parse_args()

    if not API_KEY:
        print("✗ MINIMAX_API_KEY 未设置"); return

    # 加载全科节点
    nodes = []
    for tf in sorted((ROOT / "data").rglob("tree.json")):
        for n in json.loads(tf.read_text()):
            if args.subject and n["subject"] != args.subject:
                continue
            nodes.append(n)

    # 按考频排序
    weight_rank = {"high": 0, "medium": 1, "low": 2}
    nodes.sort(key=lambda n: (weight_rank.get(n.get("exam_weight", "medium"), 1), n.get("grade", 8)))

    total = len(nodes)
    limit = args.limit or total
    print(f"📝 题库生成: {total}个节点 (本次最多{limit}个)")

    client = httpx.Client()
    ok = 0
    fail = 0
    for i, node in enumerate(nodes[:limit]):
        nid = node["node_id"]
        subject = node["subject"]
        # 输出文件
        suffix = nid.replace(f"{subject}-", "").replace(f"{subject[0]}-", "")
        out_file = ROOT / "data" / subject / f"questions-{suffix}.json"

        if args.skip_existing and out_file.exists():
            existing = json.loads(out_file.read_text())
            if len(existing) >= 5:
                print(f"[{i+1}/{min(limit,total)}] ⏭ {subject}/{node['name']} (已有{len(existing)}题)")
                continue

        print(f"[{i+1}/{min(limit,total)}] [{node.get('exam_weight','?')}] {subject}/{node['name']}...", end=" ", flush=True)
        try:
            questions = gen_for_node(node, client)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"✅ {len(questions)}题")
            ok += 1
        except Exception as e:
            print(f"✗ {e}")
            fail += 1
        time.sleep(1)  # rate limit

    client.close()
    print(f"\n{'='*40}")
    print(f"完成: {ok}成功 {fail}失败")


if __name__ == "__main__":
    main()
