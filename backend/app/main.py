from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import experiment, literature, projects


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create local storage directories on startup."""
    Path(settings.STORAGE_BASE_PATH).mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="ResearchForge API",
    description="Research Operating System – Backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(literature.router)
app.include_router(experiment.router)


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok", "version": "0.1.0"}
