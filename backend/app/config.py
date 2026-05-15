"""
Application configuration via pydantic-settings.

All values are read from environment variables or a .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Knowledge OS backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    APP_NAME: str = "Knowledge OS"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # ── Server ───────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ── Database ─────────────────────────────────────────────
    # Set DATABASE_URL directly (Supabase gives you a pooler URL)
    # e.g. postgresql+asyncpg://postgres.<ref>:<password>@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
    DATABASE_URL: str = "sqlite+aiosqlite:///./knowledge_os.db"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync URL for Alembic migrations (replace asyncpg with psycopg2)."""
        url = self.DATABASE_URL
        if "asyncpg" in url:
            return url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        if "aiosqlite" in url:
            return url.replace("sqlite+aiosqlite", "sqlite")
        return url

    @property
    def IS_SQLITE(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE_THIS_TO_A_RANDOM_64_CHAR_STRING"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── ChromaDB ─────────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # ── Supabase Storage ─────────────────────────────────────
    USE_SUPABASE_STORAGE: bool = False
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "documents"

    # ── Local File Uploads (fallback / dev) ──────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = ".pdf,.txt,.md,.docx"

    @property
    def ALLOWED_EXTENSIONS_SET(self) -> set[str]:
        return {ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")}

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Ollama (kept for local dev fallback) ─────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 120

    # ── OpenAI-Compatible (optional) ─────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Groq ─────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── LLM Provider selection ────────────────────────────────
    # Options: "groq" | "openai" | "ollama"
    LLM_PROVIDER: str = "groq"

    # ── Embeddings ───────────────────────────────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32

    # ── Rate Limiting ────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 200
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Singleton instance
settings = Settings()