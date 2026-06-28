"""错题/典型题 AI 讲解生成 API — 首次生成+缓存"""
import os, re, json
from pathlib import Path
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

ROOT = Path(__file__).parent.parent.parent
CW_DIR = ROOT / "courseware"

API_KEY = lambda: os.environ.get("MINIMAX_API_KEY", "")
API_BASE = lambda: os.environ.get("TUTOR_UPSTREAM_BASE", "https://api.minimaxi.com/v1")
MODEL = lambda: os.environ.get("TUTOR_MODEL", "MiniMax-Text-01")

EXPLAIN_PROMPT = """你是一位有30年经验的初中{subject}教师，擅长用最简单易懂的方式讲解难题。

学生做错了这道题，请生成一个完整的互动讲解页面(HTML)。

题目: {question}
正确答案: {answer}
学生的错误答案: {user_answer}
知识点: {node_name}

讲解页面要求:
1. 完整HTML页面，暗色主题(背景#0f172a，文字#e2e8f0)
2. 结构:
   - 错因分析(为什么会选错/算错)
   - 关键知识回顾(一句话点明核心概念)
   - 解题过程(分步骤，每步有解释，关键步骤用canvas/SVG图解)
   - 举一反三(1-2道同类型变式题+答案)
3. 语言通俗，像老师面对面讲解
4. 重点用颜色高亮(正确的绿色#22c55e，错误的红色#ef4444)
5. 如果涉及几何/函数，用SVG画图说明

直接输出完整HTML，不要markdown代码块。从<!DOCTYPE html>开始。"""


@router.post("/generate")
async def generate_explain(req: Request):
    """生成错题讲解（有缓存则直接返回）"""
    body = await req.json()
    question_id = body.get("question_id", "")
    question = body.get("question", "")
    answer = body.get("answer", "")
    user_answer = body.get("user_answer", "")
    node_name = body.get("node_name", "")
    subject = body.get("subject", "math")

    if not question:
        return JSONResponse(status_code=400, content={"error": "需要question参数"})

    # 缓存路径
    safe_id = re.sub(r'[^\w-]', '', question_id or "q")[:50]
    cache_dir = CW_DIR / subject / f"explain-{safe_id}"
    cache_file = cache_dir / "index.html"

    # 有缓存直接返回
    if cache_file.exists():
        return {
            "ok": True, "cached": True,
            "path": f"/courseware/{subject}/explain-{safe_id}/index.html",
            "learn_url": f"/learn/explain-{safe_id}",
        }

    # 生成
    if not API_KEY():
        return JSONResponse(status_code=503, content={"error": "AI未配置"})

    prompt = EXPLAIN_PROMPT.format(
        subject=subject, question=question, answer=answer,
        user_answer=user_answer, node_name=node_name,
    )

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{API_BASE()}/chat/completions",
                json={"model": MODEL(), "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 6000, "temperature": 0.5},
                headers={"Authorization": f"Bearer {API_KEY()}"},
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"].strip()

        # 清理
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # 保存
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(content, encoding="utf-8")

        return {
            "ok": True, "cached": False,
            "path": f"/courseware/{subject}/explain-{safe_id}/index.html",
            "learn_url": f"/learn/explain-{safe_id}",
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/check/{question_id}")
async def check_explain(question_id: str):
    """检查某题是否已有讲解缓存"""
    safe_id = re.sub(r'[^\w-]', '', question_id)[:50]
    for subject_dir in CW_DIR.iterdir():
        if not subject_dir.is_dir() or subject_dir.name.startswith("_"):
            continue
        cache_file = subject_dir / f"explain-{safe_id}" / "index.html"
        if cache_file.exists():
            return {"exists": True, "learn_url": f"/learn/explain-{safe_id}"}
    return {"exists": False}
