"""TTS语音生成API"""
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
import edge_tts

router = APIRouter()

COURSEWARE_DIR = Path(__file__).parent.parent.parent / "courseware"

VOICES = {
    "zh": "zh-CN-XiaoxiaoNeural",
    "en": "en-US-JennyNeural",
}


class TTSRequest(BaseModel):
    text: str
    lang: str = "zh"
    rate: str = "-5%"
    output_name: str | None = None


@router.post("/generate")
async def generate_tts(req: TTSRequest):
    """生成TTS音频文件"""
    voice = VOICES.get(req.lang, VOICES["zh"])
    output_dir = COURSEWARE_DIR / "_tts"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = req.output_name or f"{hash(req.text) & 0xFFFFFFFF:08x}.mp3"
    output_path = output_dir / filename

    if not output_path.exists():
        communicate = edge_tts.Communicate(req.text, voice, rate=req.rate)
        await communicate.save(str(output_path))

    return {"path": f"/courseware/_tts/{filename}", "filename": filename}


@router.get("/file/{filename}")
async def get_tts_file(filename: str):
    """获取已生成的TTS音频"""
    path = COURSEWARE_DIR / "_tts" / filename
    if path.exists():
        return FileResponse(path, media_type="audio/mpeg")
    return {"error": "not found"}
