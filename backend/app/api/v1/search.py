"""
Semantic search endpoint — searches document chunks stored in Supabase/PostgreSQL.
Uses full-text ILIKE search across chunk content (no ChromaDB required).
"""

import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.db.models.workspace import Workspace
from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def semantic_search(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    start_time = time.time()
    top_k = data.top_k or 10

    # Get workspace IDs belonging to this user
    if data.workspace_id:
        workspace_ids = [data.workspace_id]
    else:
        res = await db.execute(
            select(Workspace.id).where(Workspace.owner_id == current_user.id)
        )
        workspace_ids = res.scalars().all()

    if not workspace_ids:
        return SearchResponse(
            query=data.query,
            results=[],
            total_results=0,
            search_time_ms=0.0,
        )

    # Split query into keywords
    keywords = [kw.strip() for kw in data.query.split() if len(kw.strip()) > 2]
    if not keywords:
        keywords = [data.query.strip()]

    ilike_conditions = [Chunk.content.ilike(f"%{kw}%") for kw in keywords]

    stmt = (
        select(Chunk, Document.filename, Document.id.label("doc_id"))
        .join(Document, Chunk.document_id == Document.id)
        .where(
            Document.workspace_id.in_(workspace_ids),
            Document.status == "completed",
            or_(*ilike_conditions),
        )
        .limit(top_k * 3)
    )

    result = await db.execute(stmt)
    rows = result.all()

    def score_chunk(content: str) -> float:
        content_lower = content.lower()
        query_lower = data.query.lower()
        if query_lower in content_lower:
            return 1.0
        matched = sum(1 for kw in keywords if kw.lower() in content_lower)
        return round(matched / len(keywords), 3) if keywords else 0.0

    scored = []
    for chunk, filename, doc_id in rows:
        score = score_chunk(chunk.content)
        if score > 0:
            scored.append((chunk, filename, doc_id, score))

    scored.sort(key=lambda x: x[3], reverse=True)
    top_results = scored[:top_k]

    results = [
        SearchResultItem(
            chunk_id=chunk.id,
            document_id=doc_id,
            document_name=filename,
            content=chunk.content[:500],
            page_number=chunk.page_number,
            relevance_score=score,
            metadata=chunk.metadata_json,
        )
        for chunk, filename, doc_id, score in top_results
    ]

    search_time_ms = (time.time() - start_time) * 1000

    return SearchResponse(
        query=data.query,
        results=results,
        total_results=len(results),
        search_time_ms=search_time_ms,
    )