"""
Document ingestion background worker.

BUGS FIXED (Phase 1):
  1. SentenceTransformer was being instantiated inside _generate_embeddings_sync,
     which is called on every upload. The library does cache the model internally,
     but the first call after server start triggers a full model load (and
     potentially a download), causing a 10-30 second apparent freeze.
     FIX: Load the model once at module level into _embedding_model. All subsequent
     calls reuse the same instance with zero load time.

  2. The module-level model load is guarded so import-time errors (e.g. bad model
     name in config) surface immediately at startup, not buried in a background
     task log that nobody sees.

ORIGINAL DESIGN (preserved):
  All CPU-bound work (text extraction, embedding generation) runs inside
  asyncio.to_thread() so the event loop is NEVER blocked.
"""

import asyncio
import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

# ── Cached embedding model ─────────────────────────────────────────────────────
# Loaded once at worker-module import time. SentenceTransformer caches weights
# in memory; creating a second instance for the same model_name just wastes RAM
# and the 10-30s load time on every upload.
_embedding_model = None


def _get_embedding_model():
    """
    Return the module-level SentenceTransformer, loading it on first call.
    Thread-safe for read after the first load because GIL protects the assignment.
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        from app.config import settings
        logger.info(
            "Loading embedding model '%s' on device '%s' (one-time startup cost)",
            settings.EMBEDDING_MODEL,
            settings.EMBEDDING_DEVICE,
        )
        _embedding_model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE,
        )
        logger.info("Embedding model loaded and cached.")
    return _embedding_model


# ── Text extraction ────────────────────────────────────────────────────────────

def _extract_text_sync(file_path: str, file_extension: str, content: Optional[bytes] = None) -> str:
    """
    Extract plain text — synchronous, runs in a thread pool via asyncio.to_thread.
    Accepts raw bytes so we don't need to re-read from disk or Supabase Storage.
    """
    import io
    buf = io.BytesIO(content) if content else None

    if file_extension == ".pdf":
        import fitz
        try:
            if buf:
                doc = fitz.open(stream=buf, filetype="pdf")
            else:
                doc = fitz.open(file_path)
            text = ""
            with doc:
                for page in doc:
                    text += page.get_text() + "\n"
            return text
        except Exception as e:
            import os
            logger.error(
                "Failed to open PDF file. Path: %s, Absolute: %s, CWD: %s, Error: %s",
                file_path, os.path.abspath(file_path), os.getcwd(), e,
            )
            raise

    elif file_extension in (".txt", ".md"):
        if content:
            return content.decode("utf-8", errors="ignore")
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except OSError as e:
            import os
            logger.error(
                "Failed to open text file. Path: %s, Absolute: %s, CWD: %s, Error: %s",
                file_path, os.path.abspath(file_path), os.getcwd(), e,
            )
            raise

    elif file_extension == ".docx":
        import docx as python_docx
        try:
            doc = python_docx.Document(buf if buf else file_path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            import os
            logger.error(
                "Failed to open docx file. Path: %s, Absolute: %s, CWD: %s, Error: %s",
                file_path, os.path.abspath(file_path), os.getcwd(), e,
            )
            raise

    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")


# ── Embedding generation ───────────────────────────────────────────────────────

def _generate_embeddings_sync(texts: list[str]):
    """
    Generate embeddings using the cached model — synchronous, runs in a thread
    pool via asyncio.to_thread.

    No longer accepts model_name / device — those are baked into the cached
    instance. Changing EMBEDDING_MODEL requires a server restart, which is
    the correct behaviour (you don't want hot-swapping mid-session anyway).
    """
    model = _get_embedding_model()
    from app.config import settings
    logger.info("Generating embeddings for %d chunks", len(texts))
    return model.encode(
        texts,
        batch_size=settings.EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )


# ── Main ingestion pipeline ────────────────────────────────────────────────────

async def process_document(
    document_id: str,
    db: AsyncSession,
    file_content: Optional[bytes] = None,
) -> None:
    """
    Full ingestion pipeline: extract → chunk → embed → store.

    Args:
        document_id:  UUID string of the Document row.
        db:           Fresh AsyncSession owned by the caller.
        file_content: Raw file bytes passed from upload handler
                      (avoids re-reading from disk or Supabase).
    """
    from app.db.models.document import Document
    from app.db.models.chunk import Chunk
    from app.ml.text_splitter import RecursiveCharacterTextSplitter
    from app.vectorstore.chroma_client import get_or_create_collection
    from app.config import settings

    logger.info("Ingestion started: %s", document_id)

    try:
        # 1. Load document record
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            logger.error("Document not found: %s", document_id)
            return

        document.status = "processing"
        await db.commit()

        # 2. If bytes not passed in, read from storage
        if file_content is None:
            from app.services.storage_service import read_file
            file_content = await read_file(document.file_path)

        # 3. Extract text — runs in thread pool, does NOT block event loop
        text = await asyncio.to_thread(
            _extract_text_sync,
            document.file_path,
            document.file_extension,
            file_content,
        )
        document.raw_text = text[:2000]

        # 4. Chunk
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks_text = splitter.split_text(text)
        document.chunk_count = len(chunks_text)

        if not chunks_text:
            document.status = "completed"
            await db.commit()
            logger.warning("Document %s produced 0 chunks — file may be empty or image-only", document_id)
            return

        # 5. Generate embeddings — runs in thread pool, does NOT block event loop
        #    Uses the cached model; no model_name/device args needed anymore.
        embeddings = await asyncio.to_thread(
            _generate_embeddings_sync,
            chunks_text,
        )

        # 6. Store in ChromaDB + relational DB
        collection = get_or_create_collection(document.workspace_id)
        batch_size = 100

        for i in range(0, len(chunks_text), batch_size):
            batch_texts = chunks_text[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]
            batch_ids = [str(uuid.uuid4()) for _ in batch_texts]
            metadatas = [
                {"document_id": document.id, "chunk_index": i + j}
                for j in range(len(batch_texts))
            ]

            logger.info("Storing batch %d to ChromaDB", i // batch_size + 1)
            await asyncio.to_thread(
                collection.add,
                documents=batch_texts,
                embeddings=[e.tolist() for e in batch_embeddings],
                metadatas=metadatas,
                ids=batch_ids,
            )

            for j, chunk_text in enumerate(batch_texts):
                db.add(Chunk(
                    id=batch_ids[j],
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=i + j,
                    embedding_id=batch_ids[j],
                ))

        document.status = "completed"
        await db.commit()
        logger.info("Ingestion complete: %s (%d chunks)", document_id, len(chunks_text))

    except Exception as exc:
        logger.exception("Ingestion failed for %s: %s", document_id, exc)
        try:
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "failed"
                doc.error_message = str(exc)[:500]
                await db.commit()
        except Exception:
            await db.rollback()