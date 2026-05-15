"""
ChromaDB vector store abstraction.

Provides a clean interface for storing and querying document embeddings.
"""

import logging
from typing import Optional
import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level client singleton
_client: Optional[chromadb.HttpClient] = None


def get_chroma_client() -> chromadb.HttpClient:
    """Get or create a ChromaDB HTTP client."""
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        logger.info("Connected to ChromaDB at %s:%s", settings.CHROMA_HOST, settings.CHROMA_PORT)
    return _client


def get_or_create_collection(
    workspace_id: str,
    client: Optional[chromadb.HttpClient] = None,
) -> chromadb.Collection:
    """
    Get or create a ChromaDB collection for a workspace.

    Each workspace gets its own collection for tenant isolation.
    """
    if client is None:
        client = get_chroma_client()

    collection_name = f"workspace_{workspace_id.replace('-', '_')}"
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"workspace_id": workspace_id, "hnsw:space": "cosine"},
    )
    return collection


def add_embeddings(
    workspace_id: str,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: Optional[list[dict]] = None,
) -> None:
    """
    Add document chunk embeddings to the workspace collection.

    Args:
        workspace_id: Target workspace.
        ids: Unique IDs for each embedding (typically chunk IDs).
        embeddings: Embedding vectors.
        documents: Original text for each embedding.
        metadatas: Optional metadata dicts for filtering.
    """
    collection = get_or_create_collection(workspace_id)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas or [{}] * len(ids),
    )
    logger.info("Added %d embeddings to workspace %s", len(ids), workspace_id)


def query_embeddings(
    workspace_id: str,
    query_embedding: list[float],
    top_k: int = 10,
    filter_metadata: Optional[dict] = None,
) -> dict:
    """
    Query the workspace collection for similar chunks.

    Args:
        workspace_id: Target workspace.
        query_embedding: Query vector.
        top_k: Number of results.
        filter_metadata: Optional ChromaDB where filter.

    Returns:
        ChromaDB query results dict with ids, distances, documents, metadatas.
    """
    collection = get_or_create_collection(workspace_id)

    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if filter_metadata:
        query_params["where"] = filter_metadata

    results = collection.query(**query_params)
    return results


def delete_embeddings(workspace_id: str, ids: list[str]) -> None:
    """Delete specific embeddings from a workspace collection."""
    collection = get_or_create_collection(workspace_id)
    collection.delete(ids=ids)
    logger.info("Deleted %d embeddings from workspace %s", len(ids), workspace_id)


def delete_collection(workspace_id: str) -> None:
    """Delete an entire workspace collection."""
    client = get_chroma_client()
    collection_name = f"workspace_{workspace_id.replace('-', '_')}"
    try:
        client.delete_collection(collection_name)
        logger.info("Deleted collection for workspace %s", workspace_id)
    except Exception as e:
        logger.warning("Failed to delete collection %s: %s", collection_name, e)
