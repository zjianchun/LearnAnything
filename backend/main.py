from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from db.database import init_db
from api import diagnosis, questions, stats, study_plan, tts


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="LearnAnything", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["诊断"])
app.include_router(questions.router, prefix="/api/questions", tags=["做题"])
app.include_router(stats.router, prefix="/api/stats", tags=["统计"])
app.include_router(study_plan.router, prefix="/api/plan", tags=["学习计划"])
app.include_router(tts.router, prefix="/api/tts", tags=["语音"])

# 静态课件目录
courseware_dir = Path(__file__).parent.parent / "courseware"
courseware_dir.mkdir(exist_ok=True)
app.mount("/courseware", StaticFiles(directory=str(courseware_dir), html=True), name="courseware")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
