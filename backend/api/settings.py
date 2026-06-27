"""系统设置 API — 学科启用/隐藏等"""
import json
from pathlib import Path
from fastapi import APIRouter, Request

router = APIRouter()

SETTINGS_FILE = Path(__file__).parent.parent.parent / "data" / "settings.json"

ALL_SUBJECTS = ["math", "physics", "chemistry", "english", "chinese",
                "biology", "geography", "history", "politics"]

_cache = None


def _load() -> dict:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            _cache = {"enabled_subjects": list(ALL_SUBJECTS)}
    return _cache


def _save(data: dict):
    global _cache
    _cache = data
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_enabled_subjects() -> set:
    return set(_load().get("enabled_subjects", ALL_SUBJECTS))


@router.get("/subjects")
async def get_subjects():
    return {"enabled": _load().get("enabled_subjects", ALL_SUBJECTS), "all": ALL_SUBJECTS}


@router.put("/subjects")
async def set_subjects(req: Request):
    body = await req.json()
    enabled = [s for s in body.get("enabled", []) if s in ALL_SUBJECTS]
    if not enabled:
        enabled = list(ALL_SUBJECTS)
    data = _load()
    data["enabled_subjects"] = enabled
    _save(data)
    return {"enabled": enabled}
