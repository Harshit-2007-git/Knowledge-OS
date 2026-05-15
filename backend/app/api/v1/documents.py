"""
Document upload and management endpoints.

BUGS FIXED (Phase 1):
  1. BackgroundTasks was self-instantiated as a default parameter value:
       background_tasks: BackgroundTasks = BackgroundTasks()
     This means FastAPI never manages the instance — it's created once at
     import time and shared across all requests, so tasks can silently drop
     or run against a closed event loop.
     FIX: Remove the default value so FastAPI injects a fresh instance per request.

  2. The ingestion worker was loading SentenceTransformer on every upload,
     causing a 10-30s freeze on the first upload after server start
     (model download + load). Fixed by using the module-level cached model
     from app.ml.embeddings instead.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.dependencies import get_db, get_current_user, PaginationParams
from app.db.models.user import User
from app.db.models.document import Document
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.storage_service import save_file, delete_file

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,               # ← FIX: FastAPI auto-injects this, no default needed
    workspace_id: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document. Returns immediately — processing runs in background.
    Poll GET /documents/?workspace_id=... to check status (pending → processing → completed/failed).
    """
    # Validate extension
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS_SET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # Read and size-check
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save file (disk or Supabase Storage)
    unique_filename, file_path = await save_file(content, workspace_id, ext)

    # Create DB record with status=pending
    document = Document(
        filename=unique_filename,
        original_filename=file.filename or "unnamed",
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        file_extension=ext,
        status="pending",
        workspace_id=workspace_id,
        uploaded_by=current_user.id,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Queue background ingestion with a FRESH session (request session will close)
    from app.db.session import async_session_factory
    from app.workers.ingestion_worker import process_document

    async def run_worker(doc_id: str, file_content: bytes) -> None:
        async with async_session_factory() as session:
            await process_document(doc_id, session, file_content=file_content)

    background_tasks.add_task(run_worker, document.id, content)

    logger.info("Document %s queued for ingestion by user %s", document.id, current_user.id)
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    workspace_id: str,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents in a workspace."""
    count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.workspace_id == workspace_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Document)
        .where(Document.workspace_id == workspace_id)
        .order_by(Document.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    documents = list(result.scalars().all())
    return DocumentListResponse(documents=documents, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document details and processing status."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document, its file, and its embeddings."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        await delete_file(document.file_path)
    except Exception as e:
        logger.warning("Could not delete file %s: %s", document.file_path, e)

    try:
        from app.vectorstore.chroma_client import get_or_create_collection
        from app.db.models.chunk import Chunk
        collection = get_or_create_collection(document.workspace_id)
        chunk_res = await db.execute(select(Chunk.id).where(Chunk.document_id == document.id))
        chunk_ids = [str(cid) for cid in chunk_res.scalars().all()]
        if chunk_ids:
            collection.delete(ids=chunk_ids)
    except Exception as e:
        logger.warning("Could not delete ChromaDB chunks for %s: %s", document_id, e)

    await db.delete(document)
    await db.commit()
    return None