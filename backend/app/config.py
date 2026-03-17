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

    model_config = {"env_file": ".env"}


settings = Settings()
