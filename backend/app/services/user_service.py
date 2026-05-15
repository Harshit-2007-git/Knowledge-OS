"""
User profile service.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.db.models.user import User
from app.schemas.user import UserUpdateRequest


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise EntityNotFoundError("User", user_id)
        return user

    async def update_user(self, user_id: str, data: UserUpdateRequest) -> User:
        user = await self.get_user_by_id(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.flush()
        return user
