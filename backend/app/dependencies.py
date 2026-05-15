"""
FastAPI dependency injection providers.

Reusable dependencies for database sessions, authentication, and pagination.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.core.security import decode_access_token
from app.db.models.user import User
from sqlalchemy import select

# ── Security Scheme ──────────────────────────────────────────
security_scheme = HTTPBearer(auto_error=False)


# ── Database Session ─────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, auto-closing on completion."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Current User ─────────────────────────────────────────────
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate the current user from the JWT bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


# ── Optional Current User ───────────────────────────────────
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Return the current user if authenticated, else None."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ── Pagination ───────────────────────────────────────────────
class PaginationParams:
    """Common pagination parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
