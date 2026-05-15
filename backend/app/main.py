"""
Enterprise AI Knowledge OS — FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_v1_router
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from app.db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — startup and shutdown."""
    logger.info("🚀 Starting %s [%s]", settings.APP_NAME, settings.APP_ENV)

    from pathlib import Path
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Auto-create tables only in SQLite dev mode
    # For PostgreSQL production: run `alembic upgrade head` manually
    if settings.IS_SQLITE:
        from app.db.base import Base
        from app.db.models import User, Workspace, Document, Chunk, Conversation, Message  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ SQLite tables created/verified")

    yield

    logger.info("🛑 Shutting down %s", settings.APP_NAME)
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Enterprise AI Knowledge Management Platform.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — add your Vercel URL to CORS_ORIGINS env var in production:
    # CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    register_exception_handlers(app)
    
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        logger.error("Validation error: %s", exc.errors())
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["System"])
    async def root():
        return {
            "message": "Enterprise AI Knowledge OS API is running",
            "docs": "/docs",
            "health": "/health"
        }

    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": "0.1.0",
            "environment": settings.APP_ENV,
        }

    return app


app = create_app()