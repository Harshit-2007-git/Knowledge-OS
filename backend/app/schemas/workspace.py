"""
Workspace schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    settings: Optional[dict] = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    settings: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    model_config = {"from_attributes": True}


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceResponse]
    total: int
    page: int
    page_size: int
