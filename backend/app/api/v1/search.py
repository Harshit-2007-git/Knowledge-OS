"""
Semantic search endpoints.

Full vector search implementation will be added in Phase 3–4.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def semantic_search(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Perform semantic search across workspace documents.

    Pipeline (Phase 3–4):
    1. Encode query using sentence-transformers
    2. Query ChromaDB for top-k similar chunks
    3. Optionally rerank results
    4. Return ranked results with citations
    """
    from app.services.rag_service import RAGService
    import time
    
    start_time = time.time()
    service = RAGService(db)
    
    # Optional filtering by workspace if provided in the schema, 
    # but the frontend might not pass it if it's global search.
    # We'll need a workspace_id. If not passed, we can't search ChromaDB directly unless we loop over all user workspaces.
    # Let's assume SearchRequest has workspace_id, or we search across all workspaces of the user.
    from sqlalchemy import select
    from app.db.models.workspace import Workspace
    from app.db.models.document import Document
    
    workspace_ids = []
    if hasattr(data, 'workspace_id') and data.workspace_id:
        workspace_ids = [data.workspace_id]
    else:
        # Fetch all user workspaces
        res = await db.execute(select(Workspace.id).where(Workspace.owner_id == current_user.id))
        workspace_ids = res.scalars().all()
        
    all_contexts = []
    for wid in workspace_ids:
        contexts = await service.retrieve_context(wid, data.query, top_k=data.top_k if hasattr(data, 'top_k') else 5)
        all_contexts.extend(contexts)
        
    # Sort by distance (lower is better for cosine distance in Chroma)
    all_contexts.sort(key=lambda x: x["distance"])
    top_contexts = all_contexts[:(data.top_k if hasattr(data, 'top_k') else 10)]
    
    # Map document IDs to names
    doc_ids = list(set([c["metadata"].get("document_id") for c in top_contexts if c["metadata"].get("document_id")]))
    doc_map = {}
    if doc_ids:
        res = await db.execute(select(Document.id, Document.filename).where(Document.id.in_(doc_ids)))
        doc_map = {row.id: row.filename for row in res}
        
    from app.schemas.search import SearchResult
    results = []
    for c in top_contexts:
        doc_id = c["metadata"].get("document_id")
        results.append(
            SearchResult(
                document_id=doc_id or "unknown",
                filename=doc_map.get(doc_id, "Unknown Document"),
                content=c["text"],
                score=1.0 - c["distance"], # Convert distance to similarity
                chunk_index=c["metadata"].get("chunk_index", 0)
            )
        )
        
    search_time_ms = (time.time() - start_time) * 1000
    
    return SearchResponse(
        query=data.query,
        results=results,
        total_results=len(results),
        search_time_ms=search_time_ms,
    )
