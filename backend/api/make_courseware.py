"""课件生成 API — 家长端输入知识点，AI 生成互动课件"""
import os, json, re
from pathlib import Path
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

ROOT = Path(__file__).parent.parent
CW_DIR = ROOT / "courseware"

API_KEY = lambda: os.environ.get("MINIMAX_API_KEY", "")
API_BASE = lambda: os.environ.get("TUTOR_UPSTREAM_BASE", "https://api.minimaxi.com/v1")
MODEL = lambda: os.environ.get("TUTOR_MODEL", "MiniMax-Text-01")

GENERATE_PROMPT = """你是一位有30年经验的初中教师+课件设计师。请为以下知识点生成一个完整的互动课件HTML页面。

学科: {subject}
知识点: {topic}
年级: {grade}
教学重点: {focus}

课件要求:
1. 完整的HTML页面（含CSS），暗色主题(#0f172a背景)
2. 结构: 开场问题→核心概念→互动实验(canvas)→练习题(4道选择题)→总结
3. 选择题有正确判定和错因提示
4. canvas互动：能拖动/输入参数看变化
5. 适合初中生，语言通俗易懂
6. 不要引用任何外部脚本或CDN(除了可选的GeoGebra/PhET iframe)

直接输出完整HTML，不要markdown代码块。从<!DOCTYPE html>开始。"""


@router.post("/generate")
async def generate_courseware(req: Request):
    """AI生成课件"""
    body = await req.json()
    subject = body.get("subject", "math")
    topic = body.get("topic", "")
    grade = body.get("grade", "初二")
    focus = body.get("focus", "")
    node_id = body.get("node_id", "")

    if not topic:
        return JSONResponse(status_code=400, content={"error": "需要topic参数"})
    if not API_KEY():
        return JSONResponse(status_code=503, content={"error": "AI未配置"})

    # 生成node_id
    if not node_id:
        slug = topic.replace(" ", "-").replace("：", "").replace(":", "")[:30]
        node_id = f"{subject}-custom-{slug}"

    prompt = GENERATE_PROMPT.format(subject=subject, topic=topic, grade=grade, focus=focus or topic)

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(
                f"{API_BASE()}/chat/completions",
                json={"model": MODEL(), "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 8000, "temperature": 0.7},
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
        out_dir = CW_DIR / subject / node_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(content, encoding="utf-8")

        return {
            "ok": True,
            "node_id": node_id,
            "subject": subject,
            "path": f"/courseware/{subject}/{node_id}/index.html",
            "learn_url": f"/learn/{node_id}",
            "size": len(content),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/list-custom")
async def list_custom():
    """列出自制课件"""
    customs = []
    for d in sorted(CW_DIR.rglob("index.html")):
        if "custom" in d.parent.name:
            customs.append({
                "node_id": d.parent.name,
                "subject": d.parent.parent.name,
                "path": f"/learn/{d.parent.name}",
            })
    return {"total": len(customs), "items": customs}
