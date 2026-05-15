"""
Semantic search schemas.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    workspace_id: str
    top_k: int = Field(10, ge=1, le=50)
    filter_document_ids: Optional[list[str]] = None


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    page_number: Optional[int] = None
    relevance_score: float
    metadata: Optional[dict] = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    total_results: int
    search_time_ms: float
