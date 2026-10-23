"""Application Configuration.

Centralized configuration managed using Pydantic Settings.
Reads environment variables with sensible defaults for local development.
"""

from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "Intelligent Link Integrity Management Framework"
    API_V1_PREFIX: str = "/api"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    CANDIDATE_PAGES_DIR: Path = DATA_DIR / "candidate_pages"
    EXPERIMENTS_DIR: Path = DATA_DIR / "experiments"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'link_integrity.db'}"

    # Validation Engine Settings
    VALIDATION_TIMEOUT_SECONDS: float = 10.0
    VALIDATION_MAX_RETRIES: int = 2
    VALIDATION_BACKOFF_FACTOR: float = 1.5
    VALIDATION_MAX_CONCURRENCY: int = 10
    VALIDATION_RATE_LIMIT_PER_DOMAIN: int = 3
    VALIDATION_CACHE_TTL_SECONDS: int = 3600
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (LinkIntegrityBot/1.0 Research)"
    )

    # Security & SSRF
    SSRF_PROTECTION_ENABLED: bool = True
    ALLOWED_SCHEMES: Union[List[str], str] = ["http", "https"]

    # Maximum file upload size: 50MB
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS: Union[List[str], str] = [".pdf", ".docx"]
    ALLOWED_MIME_TYPES: Union[List[str], str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "application/octet-stream",
    ]

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", "ALLOWED_SCHEMES", "ALLOWED_EXTENSIONS", "ALLOWED_MIME_TYPES", mode="before")
    @classmethod
    def parse_comma_separated_list(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
settings.CANDIDATE_PAGES_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
