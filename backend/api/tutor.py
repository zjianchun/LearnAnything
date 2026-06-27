"""AI学伴代理：OpenAI兼容的流式转发，API Key 留在服务端(.env)。

课件内 ai-tutor.js 用 custom provider 指向 /api/tutor/v1，
本代理注入 MINIMAX_API_KEY 转发到上游，前端不暴露 key。

上游可通过环境变量配置（默认 MiniMax OpenAI 兼容端点）：
  TUTOR_UPSTREAM_BASE  默认 https://api.minimaxi.com/v1
  TUTOR_MODEL          默认 MiniMax-Text-01
  MINIMAX_API_KEY      密钥（.env）
"""
import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse

router = APIRouter()

# 运行时可动态修改的配置（初始值来自环境变量）
_runtime_config = {
    "upstream_base": os.environ.get("TUTOR_UPSTREAM_BASE", "https://api.minimaxi.com/v1"),
    "model": os.environ.get("TUTOR_MODEL", "MiniMax-Text-01"),
    "api_key": os.environ.get("MINIMAX_API_KEY", ""),
}


def _key() -> str:
    return _runtime_config["api_key"]


@router.get("/config")
async def config():
    """前端探测：是否已配置 key、用什么模型"""
    return {
        "configured": bool(_key()),
        "model": _runtime_config["model"],
        "upstream": _runtime_config["upstream_base"],
        "key_preview": _key()[:8] + "..." if _key() else "",
    }


@router.put("/config")
async def update_config(req: Request):
    """家长页面动态更新 AI 配置（运行时生效，重启后回退到.env）"""
    body = await req.json()
    if "upstream_base" in body and body["upstream_base"].strip():
        _runtime_config["upstream_base"] = body["upstream_base"].strip().rstrip("/")
    if "model" in body and body["model"].strip():
        _runtime_config["model"] = body["model"].strip()
    if "api_key" in body and body["api_key"].strip():
        _runtime_config["api_key"] = body["api_key"].strip()
    return {"ok": True, **await config()}


@router.post("/v1/chat/completions")
async def chat_completions(req: Request):
    """OpenAI 兼容转发（支持流式 SSE）"""
    key = _key()
    if not key:
        return JSONResponse(status_code=503, content={"error": "AI学伴未配置：缺少 MINIMAX_API_KEY"})

    body = await req.json()
    if not body.get("model"):
        body["model"] = _runtime_config["model"]
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    url = _runtime_config["upstream_base"].rstrip("/") + "/chat/completions"
    is_stream = bool(body.get("stream"))

    if is_stream:
        async def gen():
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream("POST", url, json=body, headers=headers) as r:
                        async for chunk in r.aiter_bytes():
                            yield chunk
            except Exception as e:
                yield f'data: {{"error": "{e}"}}\n\n'.encode()
        return StreamingResponse(gen(), media_type="text/event-stream")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=body, headers=headers)
            return JSONResponse(status_code=r.status_code, content=r.json())
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": str(e)})
