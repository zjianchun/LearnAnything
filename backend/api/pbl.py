"""PBL 探究路径 API

- /list      ：缓存的 PBL 探究课题（data/pbl-index.json，自包含）
- /analyze   ：保留 teachany.cn PBL analyze API 代理（按兴趣匹配，需要时从API拉）

用户约定：保留 API，需要更新时从 teachany.cn 拉取。
"""
import json
from pathlib import Path
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from db.database import get_db

router = APIRouter()

ROOT = Path(__file__).parent.parent.parent
PBL_INDEX = ROOT / "data" / "pbl-index.json"
CW_DIR = ROOT / "courseware"
TEACHANY_PBL_API = "https://www.teachany.cn/api/pbl/analyze"

SUBJECT_NAME = {
    "math": "数学", "physics": "物理", "chemistry": "化学", "english": "英语",
    "chinese": "语文", "biology": "生物", "geography": "地理", "history": "历史",
    "politics": "道法",
}


def _load() -> list:
    try:
        return json.loads(PBL_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []


@router.get("/list")
async def pbl_list():
    """PBL 探究课题列表（标记是否已自托管可直接学）"""
    items = _load()
    out = []
    for p in items:
        subject = p.get("subject")
        node_id = p.get("course_id")
        hosted = (CW_DIR / subject / node_id / "index.html").exists() if subject else False
        out.append({
            **p,
            "subject_name": SUBJECT_NAME.get(subject, subject),
            "self_hosted": hosted,
        })
    return {"total": len(out), "projects": out}


@router.post("/analyze")
async def pbl_analyze(req: Request):
    """转发到 teachany.cn PBL analyze（按学生兴趣匹配探究课题）。
    保留官方 API；参数原样透传。"""
    try:
        body = await req.json()
    except Exception:
        body = {}
    try:
        async with httpx.AsyncClient(timeout=40) as client:
            r = await client.post(TEACHANY_PBL_API, json=body,
                                  headers={"Content-Type": "application/json"})
            try:
                return JSONResponse(status_code=r.status_code, content=r.json())
            except Exception:
                return JSONResponse(status_code=r.status_code, content={"raw": r.text})
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})
