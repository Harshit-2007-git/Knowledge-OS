"""
Authentication endpoints — register, login, refresh, me.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    service = AuthService(db)
    _user, tokens = await service.register(data)
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive access + refresh tokens."""
    service = AuthService(db)
    _user, tokens = await service.login(data)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for new tokens."""
    service = AuthService(db)
    return await service.refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user
