"""
Document schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_serializer


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None
    page_count: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    chunk_count: int = 0
    workspace_id: str
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, dt: datetime, _info):
        return dt.isoformat() if dt.tzinfo else f"{dt.isoformat()}Z"

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class ChunkResponse(BaseModel):
    id: str
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    document_id: str

    model_config = {"from_attributes": True}
