"""
Workspace CRUD endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, PaginationParams
from app.db.models.user import User
from app.schemas.workspace import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
    WorkspaceResponse,
    WorkspaceListResponse,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.post("/", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    data: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workspace."""
    service = WorkspaceService(db)
    workspace = await service.create_workspace(data, current_user.id)
    return workspace


@router.get("/", response_model=WorkspaceListResponse)
async def list_workspaces(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all workspaces owned by the current user."""
    service = WorkspaceService(db)
    workspaces, total = await service.list_workspaces(
        current_user.id, pagination.offset, pagination.page_size
    )
    return WorkspaceListResponse(
        workspaces=workspaces,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workspace details."""
    service = WorkspaceService(db)
    return await service.get_workspace(workspace_id, current_user.id)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update workspace details."""
    service = WorkspaceService(db)
    return await service.update_workspace(workspace_id, data, current_user.id)


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a workspace and all its contents."""
    service = WorkspaceService(db)
    await service.delete_workspace(workspace_id, current_user.id)
