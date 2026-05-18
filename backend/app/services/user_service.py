"""
User profile service.
"""

from sqlalchemy import select, text
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

    async def delete_user(self, user_id: str) -> None:
        uid = user_id

        # Step 1: chunks in user's workspaces
        await self.db.execute(text(
            "DELETE FROM chunks WHERE document_id IN "
            "(SELECT d.id FROM documents d "
            " INNER JOIN workspaces w ON d.workspace_id = w.id "
            " WHERE w.owner_id = :uid)"
        ), {"uid": uid})

        # Step 2: documents in user's workspaces
        await self.db.execute(text(
            "DELETE FROM documents WHERE workspace_id IN "
            "(SELECT id FROM workspaces WHERE owner_id = :uid)"
        ), {"uid": uid})

        # Step 3: nullify uploaded_by on any remaining docs
        await self.db.execute(text(
            "UPDATE documents SET uploaded_by = NULL WHERE uploaded_by = :uid"
        ), {"uid": uid})

        # Step 4: messages in user's conversations
        await self.db.execute(text(
            "DELETE FROM messages WHERE conversation_id IN "
            "(SELECT id FROM conversations WHERE user_id = :uid)"
        ), {"uid": uid})

        # Step 5: conversations
        await self.db.execute(text(
            "DELETE FROM conversations WHERE user_id = :uid"
        ), {"uid": uid})

        # Step 6: workspaces
        await self.db.execute(text(
            "DELETE FROM workspaces WHERE owner_id = :uid"
        ), {"uid": uid})

        # Step 7: user
        await self.db.execute(text(
            "DELETE FROM users WHERE id = :uid"
        ), {"uid": uid})

        await self.db.commit()

    async def update_user(self, user_id: str, data: UserUpdateRequest) -> User:
        user = await self.get_user_by_id(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user