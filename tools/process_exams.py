"""试卷PDF处理 — 提取题目+标注知识点+入库。

用法: python3 tools/process_exams.py [--subject SUBJECT] [--limit N] [--concurrency 3]

流程:
1. PyMuPDF提取PDF全文
2. 按题号切割(正则匹配"一、""1."等)
3. AI标注每道题的知识点/难度/题型
4. 去重+存入data/<subject>/exam-questions.json

优先处理解析版(含答案)，跳过原卷版(答案从解析版获取)。
"""
import json, os, re, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import fitz  # PyMuPDF
import httpx

API_KEY = os.environ.get("MINIMAX_API_KEY", "")
API_BASE = os.environ.get("TUTOR_UPSTREAM_BASE", "https://api.minimaxi.com/v1")
MODEL = os.environ.get("TUTOR_MODEL", "MiniMax-Text-01")

EXAMS_DIR = ROOT / "data" / "exams"
OUTPUT_DIR = ROOT / "data"

SUBJECT_MAP = {
    "数学": "math", "物理": "physics", "化学": "chemistry",
    "英语": "english", "语文": "chinese", "历史": "history",
    "道法": "politics", "道德与法治": "politics", "政治": "politics",
    "生物": "biology", "地理": "geography",
}

ANNOTATE_PROMPT = """你是武汉中考命题研究专家。以下是从一份试卷中提取的题目，请为每道题标注信息。

试卷信息: {exam_info}
学科: {subject_zh}

题目文本:
{questions_text}

请输出严格JSON数组(不要markdown代码块)，每道题:
{{
  "question_num": "原始题号",
  "question": "完整题目文本(含选项)",
  "answer": "正确答案(从解析版提取，无则填null)",
  "type": "choice|fill|short_answer|proof|experiment|reading",
  "difficulty": 1-3,
  "node_keywords": ["关联的知识点关键词1", "关键词2"],
  "exam_frequency": 3-5,
  "has_figure": true/false
}}

注意:
- node_keywords填2-3个最相关的知识点关键词(如"全等三角形""一次函数""欧姆定律")
- difficulty: 1基础 2中等 3拔高
- exam_frequency: 3普通 4常考 5必考
- has_figure: 如果题目提到"如图""图示"则为true
- 只输出JSON数组，不要其他文字"""


def extract_text(pdf_path: Path) -> str:
    """从PDF提取全文"""
    doc = fitz.open(str(pdf_path))
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text


def split_questions(text: str) -> list:
    """按题号切割文本"""
    # 匹配常见题号格式
    parts = re.split(r'\n\s*(?=(?:\d{1,2})[.．、\)]|\（\d{1,2}\）|第\d+题)', text)
    questions = [p.strip() for p in parts if p.strip() and len(p.strip()) > 15]
    return questions


def detect_subject(filename: str, path: str) -> str:
    """从文件名/路径检测学科"""
    for zh, en in SUBJECT_MAP.items():
        if zh in filename or zh in path:
            return en
    return "unknown"


def detect_subject_zh(subject: str) -> str:
    for zh, en in SUBJECT_MAP.items():
        if en == subject:
            return zh
    return subject


def call_ai(prompt: str, max_retries: int = 3) -> str:
    """调MiniMax，带重试和rate limit处理"""
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    f"{API_BASE}/chat/completions",
                    json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                          "max_tokens": 4000, "temperature": 0.2},
                    headers={"Authorization": f"Bearer {API_KEY}"},
                )
                if resp.status_code == 429:
                    wait = 30 * (attempt + 1)
                    print(f"  ⏳ rate limit, 等{wait}秒...", flush=True)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"].strip()
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            wait = 20 * (attempt + 1)
            print(f"  ⏳ 超时, 重试({attempt+1}/{max_retries}), 等{wait}秒...", flush=True)
            time.sleep(wait)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(10)
            else:
                raise e
    return ""


def process_one_pdf(pdf_path: Path) -> dict:
    """处理一个PDF文件"""
    filename = pdf_path.name
    subject = detect_subject(filename, str(pdf_path))
    if subject == "unknown":
        return {"file": filename, "status": "skip", "reason": "无法识别学科"}

    # 提取文本
    text = extract_text(pdf_path)
    if len(text) < 100:
        return {"file": filename, "status": "skip", "reason": "文本过短(可能是扫描件)"}

    # 截取前8000字符发给AI（避免超长）
    text_for_ai = text[:8000] if len(text) > 8000 else text

    # AI标注
    exam_info = filename.replace(".pdf", "")
    prompt = ANNOTATE_PROMPT.format(
        exam_info=exam_info,
        subject_zh=detect_subject_zh(subject),
        questions_text=text_for_ai
    )

    try:
        result = call_ai(prompt)
        if not result:
            return {"file": filename, "status": "fail", "reason": "AI无返回"}

        # 清理
        if result.startswith("```"):
            result = result.split("\n", 1)[1] if "\n" in result else result[3:]
        if result.endswith("```"):
            result = result[:-3]

        questions = json.loads(result.strip())
        return {
            "file": filename, "status": "ok", "subject": subject,
            "questions": questions, "count": len(questions)
        }
    except json.JSONDecodeError:
        return {"file": filename, "status": "fail", "reason": "JSON解析失败"}
    except Exception as e:
        return {"file": filename, "status": "fail", "reason": str(e)[:80]}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=str, default=None, help="只处理指定学科")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--prefer-analysis", action="store_true", default=True,
                        help="优先处理解析版")
    args = parser.parse_args()

    if not API_KEY:
        print("✗ MINIMAX_API_KEY 未设置"); return

    # 收集PDF文件
    pdfs = sorted(EXAMS_DIR.rglob("*.pdf"))
    print(f"📄 找到 {len(pdfs)} 个PDF")

    # 优先解析版，跳过纯答案版
    analysis_pdfs = [p for p in pdfs if "解析" in p.name or "全解" in p.name]
    # 原卷/考试版（有完整题目但无答案）
    exam_pdfs = [p for p in pdfs if "原卷" in p.name or "考试版" in p.name or "考试" in p.name]
    # 其他（专题/真题/模拟等）
    other_pdfs = [p for p in pdfs if p not in analysis_pdfs and p not in exam_pdfs
                  and "答案版" not in p.name and "答案" not in p.name]
    # 跳过纯答案版
    skipped = [p for p in pdfs if "答案版" in p.name or ("答案" in p.name and "解析" not in p.name and "全解" not in p.name)]
    ordered = analysis_pdfs + other_pdfs + exam_pdfs
    print(f"  解析版: {len(analysis_pdfs)}, 其他: {len(other_pdfs)}, 原卷: {len(exam_pdfs)}, 跳过答案版: {len(skipped)}")

    if args.subject:
        ordered = [p for p in ordered if detect_subject(p.name, str(p)) == args.subject]

    total = len(ordered)
    limit = args.limit or total
    print(f"📝 处理: {total}个PDF (本次{limit}个, 解析版优先)")

    # 按学科汇总结果
    all_questions = {}  # subject -> list of questions
    ok = 0
    fail = 0

    for i, pdf_path in enumerate(ordered[:limit]):
        print(f"[{i+1}/{min(limit,total)}] {pdf_path.name[:50]}...", end=" ", flush=True)
        result = process_one_pdf(pdf_path)

        if result["status"] == "ok":
            subject = result["subject"]
            if subject not in all_questions:
                all_questions[subject] = []
            for q in result["questions"]:
                q["source_file"] = result["file"]
            all_questions[subject].extend(result["questions"])
            ok += 1
            print(f"✅ {result['count']}题")
        elif result["status"] == "skip":
            print(f"⏭ {result['reason']}")
        else:
            fail += 1
            print(f"✗ {result['reason']}")

        time.sleep(2)  # rate limit 缓冲

    # 保存结果
    total_q = 0
    for subject, questions in all_questions.items():
        out_file = OUTPUT_DIR / subject / "exam-questions.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        # 追加模式：如果已有文件则合并
        existing = []
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text())
            except:
                pass
        merged = existing + questions
        out_file.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        total_q += len(questions)
        print(f"  💾 {subject}: {len(questions)}题 → {out_file.name}")

    print(f"\n{'='*50}")
    print(f"完成: {ok}个PDF处理成功, {fail}个失败")
    print(f"提取: {total_q}道真题")
    print(f"结果: data/<subject>/exam-questions.json")


if __name__ == "__main__":
    main()
