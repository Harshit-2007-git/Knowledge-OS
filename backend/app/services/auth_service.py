"""
Authentication service — registration, login, and token management.
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.core.exceptions import DuplicateEntityError
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user authentication lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> tuple[User, TokenResponse]:
        """Register a new user and return tokens."""
        # Check for existing user
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise DuplicateEntityError("User", "email", data.email)

        # Create user
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        self.db.add(user)
        await self.db.flush()  # Get the generated ID

        # Create default personal workspace
        workspace = Workspace(
            name="Personal Workspace",
            description="Your default workspace for documents and chat.",
            owner_id=user.id,
        )
        self.db.add(workspace)
        
        # COMMIT everything
        await self.db.commit()
        await self.db.refresh(user)

        # Generate tokens
        tokens = self._create_tokens(user.id)
        logger.info("User registered and personal workspace created: %s", user.email)

        return user, tokens

    async def login(self, data: LoginRequest) -> tuple[User, TokenResponse]:
        """Authenticate user credentials and return tokens."""
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()

        if user is None or not verify_password(data.password, user.hashed_password):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        tokens = self._create_tokens(user.id)
        logger.info("User logged in: %s", user.email)

        return user, tokens

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Exchange a refresh token for new access + refresh tokens."""
        payload = decode_refresh_token(refresh_token)
        if payload is None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        user_id = payload.get("sub")
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated",
            )

        return self._create_tokens(user.id)

    @staticmethod
    def _create_tokens(user_id: str) -> TokenResponse:
        """Generate access and refresh tokens for a user."""
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
