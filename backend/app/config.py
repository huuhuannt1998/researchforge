from __future__ import annotations

import json
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/researchforge"
    STORAGE_BASE_PATH: str = str(BASE_DIR.parent / "storage" / "projects")
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # LM Studio (OpenAI-compatible local API)
    LLM_BASE_URL: str = "http://localhost:1234/v1"
    LLM_MODEL: str = "default"
    LLM_TIMEOUT: int = 300  # seconds — local models can be slow

    # Semantic Scholar
    SEMANTIC_SCHOLAR_API_URL: str = "https://api.semanticscholar.org/graph/v1"
    PAPER_SEARCH_LIMIT: int = 15

    model_config = {"env_file": ".env"}


settings = Settings()
