"""
Workspace CRUD service.
"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, PermissionDeniedError
from app.db.models.workspace import Workspace
from app.db.models.document import Document
from app.schemas.workspace import WorkspaceCreateRequest, WorkspaceUpdateRequest


class WorkspaceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workspace(self, data: WorkspaceCreateRequest, owner_id: str) -> Workspace:
        workspace = Workspace(
            name=data.name,
            description=data.description,
            owner_id=owner_id,
        )
        self.db.add(workspace)
        await self.db.flush()
        return workspace

    async def get_workspace(self, workspace_id: str, user_id: str) -> Workspace:
        result = await self.db.execute(
            select(Workspace).where(Workspace.id == workspace_id)
        )
        workspace = result.scalar_one_or_none()
        if workspace is None:
            raise EntityNotFoundError("Workspace", workspace_id)
        if workspace.owner_id != user_id:
            raise PermissionDeniedError("You do not own this workspace")
        return workspace

    async def list_workspaces(
        self, user_id: str, offset: int = 0, limit: int = 20
    ) -> tuple[list[Workspace], int]:
        # Count
        count_result = await self.db.execute(
            select(func.count()).select_from(Workspace).where(Workspace.owner_id == user_id)
        )
        total = count_result.scalar() or 0

        # Fetch
        result = await self.db.execute(
            select(Workspace)
            .where(Workspace.owner_id == user_id)
            .order_by(Workspace.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        workspaces = list(result.scalars().all())
        return workspaces, total

    async def update_workspace(
        self, workspace_id: str, data: WorkspaceUpdateRequest, user_id: str
    ) -> Workspace:
        workspace = await self.get_workspace(workspace_id, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workspace, field, value)
        await self.db.flush()
        return workspace

    async def delete_workspace(self, workspace_id: str, user_id: str) -> None:
        workspace = await self.get_workspace(workspace_id, user_id)
        
        # 1. Cleanup Vector Store
        try:
            from app.vectorstore.chroma_client import delete_collection
            delete_collection(workspace_id)
        except Exception as e:
            from app.services.workspace_service import logger
            logger.warning("Failed to delete chroma collection for workspace %s: %s", workspace_id, e)

        # 2. Cleanup Filesystem
        try:
            import shutil
            from pathlib import Path
            from app.config import settings
            workspace_dir = Path(settings.UPLOAD_DIR).resolve() / workspace_id
            if workspace_dir.exists():
                shutil.rmtree(workspace_dir)
        except Exception as e:
            from app.services.workspace_service import logger
            logger.warning("Failed to delete workspace directory %s: %s", workspace_id, e)

        # 3. Delete from DB (CASCADES will handle documents/chunks in DB)
        await self.db.delete(workspace)
        await self.db.commit()
