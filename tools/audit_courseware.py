"""课件质量自动审查 — AI 检查互动逻辑、数据一致性、显示与判定匹配。

用法: python3 tools/audit_courseware.py [--subject SUBJECT] [--limit N] [--fix]

审查维度：
1. 交互逻辑：canvas/quiz/模拟的JS是否自洽（输入→显示→判定一致）
2. 内容匹配：课件title/h1/h2与实际内容是否对应（防止模板复用残留）
3. 数据正确：数学公式、物理常数、化学方程式等基础事实
4. 选项正确：选择题的answer是否在options中，解析是否对应

输出: data/audit-report.json
"""
import json, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import httpx

API_KEY = os.environ.get("MINIMAX_API_KEY", "")
API_BASE = os.environ.get("TUTOR_UPSTREAM_BASE", "https://api.minimaxi.com/v1")
MODEL = os.environ.get("TUTOR_MODEL", "MiniMax-Text-01")

AUDIT_PROMPT = """你是一位有30年教学经验的课件质量审查专家。请审查以下互动课件的源代码，找出所有逻辑错误和内容问题。

课件标题: {title}
学科: {subject}
知识点: {node_name}

重点检查：
1. **交互一致性**: canvas/转盘/滑块等互动元素的显示值是否和代码逻辑中的判定值一致
2. **内容匹配**: 标题说的是"{node_name}"，但正文/交互内容是否真的在讲这个知识点（防止模板复用没改内容）
3. **选择题逻辑**: 正确答案是否确实正确，错误选项的错因解释是否合理
4. **数据正确性**: 数学计算、物理公式、化学方程是否有错误
5. **显示bug**: innerHTML/textContent设置的内容是否和变量值对应

课件源代码（关键部分）:
```html
{code}
```

请输出严格JSON格式（不要markdown代码块）:
{{
  "has_issues": true/false,
  "severity": "none|low|medium|high|critical",
  "issues": [
    {{
      "type": "logic_mismatch|content_wrong|data_error|template_residual|display_bug",
      "location": "描述位置（函数名/行号附近/section标题）",
      "description": "问题描述",
      "fix_suggestion": "修复建议（含代码片段）"
    }}
  ],
  "summary": "一句话概括课件质量"
}}

如果没有问题，issues为空数组，severity为"none"。只报告确实存在的问题，不要编造。"""


def extract_interactive_code(html: str, max_chars: int = 8000) -> str:
    """提取课件中的交互逻辑代码（内联script + quiz + canvas相关）"""
    parts = []
    
    # 提取标题
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if title_match:
        parts.append(f"<!-- 标题: {re.sub(r'<[^>]+>', '', title_match.group(1)).strip()} -->")
    
    # 提取内联script（排除共享脚本引用）
    for m in re.finditer(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.DOTALL):
        code = m.group(1).strip()
        if code and len(code) > 50 and 'self-check' not in code:
            parts.append(code)
    
    # 提取quiz/选择题区域
    for m in re.finditer(r'<(?:section|div)[^>]*(?:quiz|pretest|posttest)[^>]*>.*?</(?:section|div)>', html, re.DOTALL):
        parts.append(m.group(0)[:1500])
    
    # 提取canvas相关的section
    for m in re.finditer(r'<(?:section|div)[^>]*(?:interactive|lab|simulation|canvas)[^>]*>.*?</(?:section|div)>', html, re.DOTALL):
        parts.append(m.group(0)[:2000])
    
    combined = '\n\n'.join(parts)
    if len(combined) > max_chars:
        combined = combined[:max_chars] + '\n... (截断)'
    return combined


def audit_one(html_path: Path, subject: str, node_name: str, client: httpx.Client) -> dict:
    html = html_path.read_text(encoding='utf-8')
    code = extract_interactive_code(html)
    
    if len(code) < 100:
        return {"has_issues": False, "severity": "none", "issues": [], "summary": "无交互代码，跳过"}
    
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else node_name
    
    prompt = AUDIT_PROMPT.format(title=title, subject=subject, node_name=node_name, code=code)
    
    resp = client.post(
        f"{API_BASE}/chat/completions",
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 2000, "temperature": 0.3},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=120,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return json.loads(content.strip())


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=str, default=None)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--fix", action="store_true", help="自动应用修复（暂未实现）")
    args = parser.parse_args()

    if not API_KEY:
        print("✗ MINIMAX_API_KEY 未设置"); return

    # 加载节点元数据
    node_meta = {}
    for tf in sorted((ROOT / "data").rglob("tree.json")):
        for n in json.loads(tf.read_text()):
            node_meta[n["node_id"]] = n

    # 扫描课件
    courseware_dir = ROOT / "courseware"
    tasks = []
    for idx_file in sorted(courseware_dir.rglob("index.html")):
        if "_assets" in str(idx_file):
            continue
        parts = idx_file.relative_to(courseware_dir).parts
        if len(parts) < 2:
            continue
        subject = parts[0]
        node_id = parts[1]
        if args.subject and subject != args.subject:
            continue
        meta = node_meta.get(node_id, {})
        tasks.append({
            "path": idx_file,
            "subject": subject,
            "node_id": node_id,
            "node_name": meta.get("name", node_id),
            "exam_weight": meta.get("exam_weight", "medium"),
        })

    # 按考频排序（高频优先审查）
    weight_rank = {"high": 0, "medium": 1, "low": 2}
    tasks.sort(key=lambda t: weight_rank.get(t["exam_weight"], 1))

    total = len(tasks)
    limit = args.limit or total
    print(f"🔍 课件质量审查: {total}个课件 (本次{limit}个, 高频优先)")

    client = httpx.Client()
    report = []
    issues_found = 0

    for i, task in enumerate(tasks[:limit]):
        print(f"[{i+1}/{min(limit,total)}] [{task['exam_weight']}] {task['subject']}/{task['node_name']}...", end=" ", flush=True)
        try:
            result = audit_one(task["path"], task["subject"], task["node_name"], client)
            result["node_id"] = task["node_id"]
            result["subject"] = task["subject"]
            result["node_name"] = task["node_name"]
            report.append(result)
            if result.get("has_issues"):
                issues_found += 1
                n_issues = len(result.get("issues", []))
                print(f"⚠️ {result['severity']} ({n_issues}个问题)")
            else:
                print("✅")
        except Exception as e:
            print(f"✗ {e}")
            report.append({"node_id": task["node_id"], "error": str(e)})
        time.sleep(1)

    client.close()

    # 保存报告
    out = ROOT / "data" / "audit-report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"\n{'='*50}")
    print(f"审查完成: {len(report)}个课件")
    print(f"发现问题: {issues_found}个课件有issue")
    print(f"报告: {out}")
    
    # 摘要
    by_severity = {}
    for r in report:
        s = r.get("severity", "error")
        by_severity[s] = by_severity.get(s, 0) + 1
    print(f"严重度分布: {by_severity}")


if __name__ == "__main__":
    main()
