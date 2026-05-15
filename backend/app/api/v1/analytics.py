"""
Analytics endpoints — document classification, clustering, and insights.

Full implementation will be added in Phase 6.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.db.models.user import User

router = APIRouter()


class ClassificationResult(BaseModel):
    document_id: str
    predicted_class: str
    confidence: float
    classes: dict[str, float]


class ClusterResult(BaseModel):
    cluster_id: int
    label: str
    document_ids: list[str]
    keywords: list[str]


@router.get("/summary")
async def get_system_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.db.models.workspace import Workspace
    from app.db.models.document import Document
    from app.db.models.chunk import Chunk
    
    ws_count_res = await db.execute(select(func.count()).select_from(Workspace).where(Workspace.owner_id == current_user.id))
    ws_count = ws_count_res.scalar() or 0
    
    doc_count_res = await db.execute(select(func.count()).select_from(Document).where(Document.uploaded_by == current_user.id))
    doc_count = doc_count_res.scalar() or 0
    
    # We join Chunk -> Document to filter by user. For simplicity, since the MVP doesn't have a direct owner on Chunk,
    # we can just sum up chunks over documents owned by the user
    # Or just sum document.chunk_count
    chunk_count_res = await db.execute(select(func.sum(Document.chunk_count)).where(Document.uploaded_by == current_user.id))
    chunk_count = chunk_count_res.scalar() or 0
    
    return {
        "total_workspaces": ws_count,
        "total_documents": doc_count,
        "total_chunks": chunk_count
    }

@router.get("/recent-activity")
async def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.db.models.document import Document
    
    res = await db.execute(
        select(Document)
        .where(Document.uploaded_by == current_user.id)
        .order_by(Document.created_at.desc())
        .limit(5)
    )
    docs = res.scalars().all()
    
    activity = []
    for d in docs:
        activity.append({
            "id": d.id,
            "type": "document_upload",
            "name": d.filename,
            "status": d.status,
            "date": d.created_at.isoformat() if d.created_at else None
        })
        
    return activity


@router.get("/{workspace_id}/clusters")
async def get_workspace_clusters(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cluster documents in a workspace using TF-IDF and KMeans."""
    from sqlalchemy import select
    from app.db.models.document import Document
    from app.db.models.chunk import Chunk
    from app.ml.clusterer import DocumentClusterer
    
    # 1. Fetch documents
    doc_res = await db.execute(select(Document).where(Document.workspace_id == workspace_id, Document.uploaded_by == current_user.id))
    documents = doc_res.scalars().all()
    
    if not documents or len(documents) < 2:
        return {"clusters": []}
        
    doc_ids = [d.id for d in documents]
    doc_map = {d.id: d.filename for d in documents}
    
    # 2. Fetch chunks to reconstruct document text (for clustering)
    chunk_res = await db.execute(select(Chunk).where(Chunk.document_id.in_(doc_ids)))
    chunks = chunk_res.scalars().all()
    
    # Group chunks by document
    doc_texts = {did: [] for did in doc_ids}
    for c in chunks:
        doc_texts[c.document_id].append(c.content)
        
    texts = []
    valid_doc_ids = []
    
    for did, contents in doc_texts.items():
        full_text = " ".join(contents)
        if len(full_text.strip()) > 50: # Only cluster documents with meaningful text
            texts.append(full_text)
            valid_doc_ids.append(did)
            
    if len(texts) < 2:
        return {"clusters": []}
        
    # 3. Cluster
    # If we have very few docs, cluster count must be smaller
    n_clusters = min(5, len(texts))
    clusterer = DocumentClusterer(method="kmeans", n_clusters=n_clusters)
    results = clusterer.fit_predict(texts, valid_doc_ids)
    
    # Map document IDs back to filenames
    for c in results:
        c["document_names"] = [doc_map.get(did, "Unknown") for did in c["document_ids"]]
        
    return {"clusters": results}
