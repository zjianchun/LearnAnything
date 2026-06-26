from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 加载根目录 .env（本地直跑uvicorn时；docker由compose注入env）
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from db.database import init_db
from api import diagnosis, questions, stats, study_plan, tts, graph, tutor, courseware, pbl


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="LearnAnything", version="0.2.0", lifespan=lifespan)

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
app.include_router(graph.router, prefix="/api/graph", tags=["知识图谱"])
app.include_router(tutor.router, prefix="/api/tutor", tags=["AI学伴"])
app.include_router(courseware.router, prefix="/api/courseware-api", tags=["课件库"])
app.include_router(pbl.router, prefix="/api/pbl", tags=["PBL探究"])

# 静态课件目录
courseware_dir = Path(__file__).parent.parent / "courseware"
courseware_dir.mkdir(exist_ok=True)
app.mount("/courseware", StaticFiles(directory=str(courseware_dir), html=True), name="courseware")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
