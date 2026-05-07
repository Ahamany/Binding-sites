"""FastAPI entry point.

Запуск:
    cd backend
    uvicorn app.main:app --reload --port 8000

Layout:
    /api/jobs           — create / list / status / structure / results
    /api/health         — liveness probe
    /                   — статика frontend/index.html
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes.jobs import router as jobs_router

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title="Binding Sites Detection",
    description="P2Rank + fpocket comparison tool with 3D visualization",
    version="0.1.0",
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(jobs_router, prefix="/api")

# Статика последней — иначе StaticFiles перехватит /api/* пути.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
