"""
Async SQLAlchemy engine and session factory.

Supports PostgreSQL (asyncpg) for production and SQLite (aiosqlite) for dev.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ── Async Engine ─────────────────────────────────────────────────────────────
_engine_kwargs: dict = {
    "echo": settings.DEBUG,
}

if settings.IS_SQLITE:
    # SQLite doesn't support pool_size / pool_recycle
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL (Supabase) — NullPool is required when using
    # Supabase's pgbouncer in transaction mode (port 6543)
    from sqlalchemy.pool import NullPool
    _engine_kwargs.update({
        "poolclass": NullPool,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

# ── Session Factory ───────────────────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)