"""
User profile endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get the authenticated user's full profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's profile."""
    service = UserService(db)
    updated = await service.update_user(current_user.id, data)
    return updated
