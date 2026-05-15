"""
Chat and conversation schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    workspace_id: str
    model_name: Optional[str] = None
    top_k: int = Field(5, ge=1, le=20)
    temperature: float = Field(0.7, ge=0.0, le=2.0)


class CitationSchema(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    page_number: Optional[int] = None
    relevance_score: float


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    message_index: int
    citations: Optional[list[CitationSchema]] = None
    model_name: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    title: str
    model_name: Optional[str] = None
    workspace_id: str
    user_id: str
    messages: list[MessageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int
    page: int
    page_size: int
