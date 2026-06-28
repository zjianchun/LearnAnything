"""多模态试卷处理工具 v2
逐页渲染PDF为图片 → 发给MiniMax视觉模型提取题目 → 保存页面PNG + JSON
"""
import json, os, re, sys, time, base64, hashlib
from pathlib import Path

import fitz  # PyMuPDF
import httpx

ROOT = Path(__file__).resolve().parent.parent
EXAM_DIR = ROOT / "data" / "exams"
OUTPUT_DIR = ROOT / "data"
PAGE_IMG_DIR = ROOT / "data" / "exam-pages"  # 保存每页PNG

# 从.env读配置
env = {}
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

API_KEY = env.get("MINIMAX_API_KEY", "")
API_BASE = env.get("OPENAI_API_BASE", "https://api.minimax.chat/v1")
MODEL = "MiniMax-M3"

SUBJECT_MAP = {
    "数学": "math", "物理": "physics", "化学": "chemistry",
    "英语": "english", "语文": "chinese", "生物": "biology",
    "历史": "history", "道法": "politics", "政治": "politics",
    "地理": "geography",
}

EXTRACT_PROMPT = """你是武汉中考命题研究专家。请仔细看这张试卷图片，提取所有题目。

试卷信息: {exam_info}
学科: {subject_zh}

输出严格JSON数组(不要外层包装，不要markdown代码块)，每道题:
{{
  "question_num": "题号",
  "question": "完整题目文本(含选项，公式用LaTeX如$\\\\triangle ABC$、$x^2+2x=0$)",
  "answer": null,
  "type": "choice|fill|short_answer|proof|experiment|reading",
  "difficulty": 1-3,
  "node_keywords": ["知识点1", "知识点2"],
  "exam_frequency": 3-5,
  "figure_description": "精确描述图中几何关系/实验装置/表格数据，使不看图也能做题。无图填null"
}}

重点：
- 公式必须用LaTeX: $\\angle A=90°$, $\\frac{{a}}{{b}}$, $\\sqrt{{3}}$
- 有图的题，figure_description必须包含所有标注的点、线段、角度、长度数值
- 表格数据用文字列出每行每列
- difficulty: 1基础 2中等 3拔高
- exam_frequency: 3普通 4常考 5必考
- 如果这页只有答案/标题/空白，返回空数组 []
- 只输出JSON数组"""


def detect_subject(filename: str, path: str) -> tuple:
    """返回 (english_name, chinese_name)"""
    for zh, en in SUBJECT_MAP.items():
        if zh in filename or zh in path:
            return en, zh
    return "unknown", "未知"


def render_page(page, dpi=150) -> bytes:
    """渲染PDF页为PNG bytes (用于发AI)"""
    pix = page.get_pixmap(dpi=dpi)
    return pix.tobytes("png")


def call_ai_vision(img_b64: str, prompt: str, max_retries: int = 3) -> str:
    """调MiniMax视觉模型"""
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(
                    f"{API_BASE}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": MODEL,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                                {"type": "text", "text": prompt}
                            ]
                        }],
                        "max_tokens": 4096
                    }
                )
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                elif resp.status_code == 429:
                    time.sleep(10 * (attempt + 1))
                else:
                    print(f"    HTTP {resp.status_code}: {resp.text[:100]}")
                    time.sleep(5)
        except Exception as e:
            print(f"    请求异常: {e}")
            time.sleep(5)
    return ""


def process_page(pdf_path: Path, page_num: int, subject: str, subject_zh: str, exam_info: str) -> dict:
    """处理单页PDF"""
    doc = fitz.open(str(pdf_path))
    page = doc[page_num]
    img_bytes = render_page(page)
    doc.close()

    # 调AI提取
    img_b64 = base64.b64encode(img_bytes).decode()
    prompt = EXTRACT_PROMPT.format(exam_info=exam_info, subject_zh=subject_zh)
    result = call_ai_vision(img_b64, prompt)

    if not result:
        return {"page": page_num, "status": "fail", "reason": "AI无返回", "questions": []}

    # 剥离<think>...</think>思考链
    if "<think>" in result:
        result = re.sub(r'<think>[\s\S]*?</think>', '', result).strip()

    # 清理markdown代码块
    if result.startswith("```"):
        result = re.sub(r'^```\w*\n?', '', result)
    if result.endswith("```"):
        result = result[:-3]

    try:
        questions = json.loads(result.strip())
        if not isinstance(questions, list):
            questions = questions.get("questions", []) if isinstance(questions, dict) else []

        # 判断本页是否有题需要图片（figure_description非null）
        has_figure = any(
            isinstance(q, dict) and q.get("figure_description") not in (None, "null", "")
            for q in questions
        )

        figure_url = None
        if has_figure:
            # 只有有图才保存WebP
            page_id = hashlib.md5(f"{pdf_path.name}_{page_num}".encode()).hexdigest()[:12]
            img_dir = PAGE_IMG_DIR / subject
            img_dir.mkdir(parents=True, exist_ok=True)
            img_path = img_dir / f"{page_id}.webp"
            # 转WebP保存
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(img_bytes))
            img.save(str(img_path), format="WEBP", quality=80)
            figure_url = f"/exam-pages/{subject}/{page_id}.webp"

        # 给有图的题加figure_url
        for q in questions:
            if not isinstance(q, dict):
                continue
            q["source_pdf"] = pdf_path.name
            q["source_page"] = page_num
            if figure_url and q.get("figure_description") not in (None, "null", ""):
                q["figure_url"] = figure_url
            else:
                q.pop("figure_url", None)
        questions = [q for q in questions if isinstance(q, dict)]
        return {"page": page_num, "status": "ok", "questions": questions, "count": len(questions)}
    except json.JSONDecodeError:
        return {"page": page_num, "status": "fail", "reason": "JSON解析失败", "questions": []}


def process_pdf(pdf_path: Path) -> dict:
    """处理整份PDF"""
    filename = pdf_path.name
    subject, subject_zh = detect_subject(filename, str(pdf_path))
    if subject == "unknown":
        return {"file": filename, "status": "skip", "reason": "无法识别学科", "questions": []}

    # 跳过解析版/答案版
    if any(k in filename for k in ["解析", "答案版", "解答"]):
        return {"file": filename, "status": "skip", "reason": "解析版跳过", "questions": []}

    doc = fitz.open(str(pdf_path))
    num_pages = len(doc)
    doc.close()

    exam_info = filename.replace(".pdf", "")
    all_questions = []
    ok_pages = 0

    for p in range(num_pages):
        result = process_page(pdf_path, p, subject, subject_zh, exam_info)
        if result["status"] == "ok" and result["count"] > 0:
            all_questions.extend(result["questions"])
            ok_pages += 1
            print(f"    p{p+1}: {result['count']}题", end=" ", flush=True)
        elif result["status"] == "fail":
            print(f"    p{p+1}: ✗{result['reason']}", end=" ", flush=True)
        time.sleep(3)  # rate limit

    print()
    return {
        "file": filename, "status": "ok", "subject": subject,
        "pages": num_pages, "ok_pages": ok_pages,
        "questions": all_questions, "count": len(all_questions)
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=str, default=None)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true", help="跳过已处理的PDF")
    args = parser.parse_args()

    # 收集所有PDF
    pdfs = sorted(EXAM_DIR.rglob("*.pdf"))
    if args.subject:
        pdfs = [p for p in pdfs if args.subject in str(p)]

    # 过滤解析版
    pdfs = [p for p in pdfs if not any(k in p.name for k in ["解析", "答案版", "解答"])]

    # 断点续传: 跳过已有结果的
    done_files = set()
    if args.resume:
        for jf in OUTPUT_DIR.rglob("exam-questions-v2.json"):
            try:
                for q in json.loads(jf.read_text()):
                    done_files.add(q.get("source_pdf", ""))
            except:
                pass
        pdfs = [p for p in pdfs if p.name not in done_files]

    if args.limit > 0:
        pdfs = pdfs[:args.limit]

    print(f"多模态试卷处理 v2")
    print(f"PDF数量: {len(pdfs)} (已跳过解析版)")
    print(f"API: {API_BASE}")
    print(f"模型: {MODEL}")
    print(f"图片保存: {PAGE_IMG_DIR}")
    print("=" * 50)

    all_questions = {}  # subject -> [questions]
    ok, fail, skip = 0, 0, 0

    for i, pdf in enumerate(pdfs):
        print(f"[{i+1}/{len(pdfs)}] {pdf.name}... ", end="", flush=True)
        result = process_pdf(pdf)

        if result["status"] == "ok":
            ok += 1
            subject = result["subject"]
            all_questions.setdefault(subject, []).extend(result["questions"])
            print(f"✅ {result['count']}题({result['ok_pages']}/{result['pages']}页)")
        elif result["status"] == "skip":
            skip += 1
            print(f"⏭️ {result['reason']}")
        else:
            fail += 1
            print(f"✗ {result.get('reason', '未知错误')}")

        # 每10个PDF保存一次(防丢失)
        if (i + 1) % 10 == 0:
            save_results(all_questions)
            print(f"  💾 中间保存 ({sum(len(v) for v in all_questions.values())}题)")

    # 最终保存
    save_results(all_questions)
    total_q = sum(len(v) for v in all_questions.values())

    print(f"\n{'=' * 50}")
    print(f"完成: {ok}成功, {fail}失败, {skip}跳过")
    print(f"提取: {total_q}道真题")
    print(f"图片: {PAGE_IMG_DIR}")
    for s, qs in sorted(all_questions.items()):
        print(f"  {s}: {len(qs)}题")


def save_results(all_questions: dict):
    """保存结果到data/<subject>/exam-questions-v2.json"""
    for subject, questions in all_questions.items():
        out_file = OUTPUT_DIR / subject / "exam-questions-v2.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        # 追加模式
        existing = []
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text())
            except:
                pass
        # 去重(按source_pdf + question_num)
        seen = {(q.get("source_pdf"), q.get("question_num")) for q in existing}
        new_qs = [q for q in questions if (q.get("source_pdf"), q.get("question_num")) not in seen]
        merged = existing + new_qs
        out_file.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
