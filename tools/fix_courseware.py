"""课件自动修复 — 根据审查报告让AI生成修复版本，修复后再审查验证。

用法: python3 tools/fix_courseware.py [--limit N] [--severity high,medium]

流程: 读audit-report.json → 对每个有问题的课件让AI修复 → 覆盖 → 再审查验证
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

FIX_PROMPT = """你是一位有30年经验的初中{subject}教师+前端开发专家。下面的课件有质量问题需要修复。

知识点: {node_name}
学科: {subject}

发现的问题:
{issues_text}

课件源代码:
```html
{code}
```

请修复所有问题，输出修复后的完整HTML源代码。要求:
1. 修复所有报告的逻辑错误、数据错误、显示不一致
2. 确保canvas互动的坐标/角度/数值计算100%精确
3. 确保选择题答案正确，错因解释合理
4. 确保内容和标题"{node_name}"完全匹配，没有模板残留
5. 保持课件原有结构和样式不变，只修bug
6. 所有数学公式、物理定律、化学方程必须正确无误

直接输出完整HTML，从<!DOCTYPE html>或<html>或第一行开始，不要markdown代码块。"""

VERIFY_PROMPT = """你是课件质量终审专家。请验证这个修复后的课件是否还有任何错误。

知识点: {node_name}  学科: {subject}

严格检查:
1. canvas/交互的数学计算是否100%正确
2. 选择题的正确答案是否确实正确
3. 内容是否完全对应"{node_name}"这个知识点
4. 有无任何事实性错误

课件代码(关键部分):
```
{code}
```

输出JSON(不要markdown代码块):
{{"pass": true/false, "remaining_issues": ["问题1", "问题2"]}}
如果没有任何问题，pass为true，remaining_issues为空数组。"""


def call_ai(prompt: str, client: httpx.Client, max_tokens: int = 8000) -> str:
    resp = client.post(
        f"{API_BASE}/chat/completions",
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": max_tokens, "temperature": 0.2},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def extract_code_for_verify(html: str) -> str:
    """提取关键交互代码用于验证"""
    parts = []
    title = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if title:
        parts.append(f"标题: {re.sub(r'<[^>]+>', '', title.group(1)).strip()}")
    for m in re.finditer(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', html, re.DOTALL):
        code = m.group(1).strip()
        if code and len(code) > 50:
            parts.append(code[:3000])
    for m in re.finditer(r'<(?:section|div)[^>]*(?:quiz|test)[^>]*>.*?</(?:section|div)>', html, re.DOTALL):
        parts.append(m.group(0)[:1500])
    return '\n'.join(parts)[:6000]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--severity", type=str, default="high,medium")
    parser.add_argument("--max-retries", type=int, default=2)
    args = parser.parse_args()

    if not API_KEY:
        print("✗ MINIMAX_API_KEY 未设置"); return

    report_file = ROOT / "data" / "audit-report.json"
    if not report_file.exists():
        print("✗ 先运行 audit_courseware.py 生成报告"); return

    report = json.loads(report_file.read_text())
    severities = set(args.severity.split(","))

    # 筛选需要修复的
    to_fix = [r for r in report if r.get("has_issues") and r.get("severity") in severities]
    to_fix.sort(key=lambda x: 0 if x.get("severity") == "high" else 1)

    total = len(to_fix)
    limit = args.limit or total
    print(f"🔧 课件修复: {total}个待修 (本次{limit}个, {args.severity})")

    client = httpx.Client()
    fixed = 0
    verified = 0
    failed = 0

    for i, item in enumerate(to_fix[:limit]):
        node_id = item["node_id"]
        subject = item["subject"]
        node_name = item.get("node_name", node_id)
        issues = item.get("issues", [])

        # 找课件文件
        html_path = ROOT / "courseware" / subject / node_id / "index.html"
        if not html_path.exists():
            print(f"[{i+1}/{limit}] ⏭ {subject}/{node_name} (文件不存在)")
            continue

        issues_text = "\n".join(
            f"- [{iss['type']}] {iss['description']}\n  建议: {iss.get('fix_suggestion', '')}"
            for iss in issues
        )

        print(f"[{i+1}/{limit}] [{item['severity']}] {subject}/{node_name} ({len(issues)}个问题)...", end=" ", flush=True)

        html = html_path.read_text(encoding="utf-8")

        # 如果课件太大(>20KB)，只发关键部分让AI修
        if len(html) > 20000:
            code_to_send = html[:18000] + "\n... (截断，后续保持不变)"
        else:
            code_to_send = html

        try:
            # 修复
            prompt = FIX_PROMPT.format(
                subject=subject, node_name=node_name,
                issues_text=issues_text, code=code_to_send
            )
            result = call_ai(prompt, client)

            # 清理
            if result.startswith("```"):
                result = result.split("\n", 1)[1] if "\n" in result else result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()

            # 基本验证：必须是HTML
            if not ("<html" in result.lower() or "<!doctype" in result.lower() or "<head" in result.lower()):
                print("✗ AI返回非HTML")
                failed += 1
                continue

            # 写入
            html_path.write_text(result, encoding="utf-8")
            fixed += 1

            # 验证
            verify_code = extract_code_for_verify(result)
            verify_prompt = VERIFY_PROMPT.format(
                node_name=node_name, subject=subject, code=verify_code
            )
            verify_result = call_ai(verify_prompt, client, max_tokens=1000)
            if verify_result.startswith("```"):
                verify_result = verify_result.split("\n", 1)[1]
            if verify_result.endswith("```"):
                verify_result = verify_result[:-3]

            try:
                vr = json.loads(verify_result.strip())
                if vr.get("pass"):
                    verified += 1
                    print("✅ 修复+验证通过")
                else:
                    remaining = vr.get("remaining_issues", [])
                    print(f"⚠️ 修复完成，验证有{len(remaining)}个残留问题")
            except:
                print("✅ 修复完成(验证JSON解析失败)")

        except Exception as e:
            print(f"✗ {str(e)[:60]}")
            failed += 1

        time.sleep(1.5)

    client.close()

    print(f"\n{'='*50}")
    print(f"修复完成: {fixed}个修复, {verified}个验证通过, {failed}个失败")
    print(f"建议: 再跑一次 audit_courseware.py 全面复检")


if __name__ == "__main__":
    main()
