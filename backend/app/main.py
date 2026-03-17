from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import experiment, literature, pipeline, projects


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create local storage directories on startup; clean up on shutdown."""
    Path(settings.STORAGE_BASE_PATH).mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown: close shared HTTP clients
    from app.services import llm_service, search_service
    await llm_service.close()
    await search_service.close()


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
app.include_router(pipeline.router)


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok", "version": "0.1.0"}
