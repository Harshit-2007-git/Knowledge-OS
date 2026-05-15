"""
Embedding generation using sentence-transformers.

Wraps the HuggingFace sentence-transformers library with
batch processing and caching support.
"""

import logging
from typing import Optional

import torch
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_model = None


def get_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
    """Load and cache the embedding model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s on %s", model_name, device)
        _model = SentenceTransformer(model_name, device=device)
        logger.info("Embedding model loaded. Dimension: %d", _model.get_sentence_embedding_dimension())
    return _model


def generate_embeddings(
    texts: list[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    device: str = "cpu",
    batch_size: int = 32,
    normalize: bool = True,
) -> np.ndarray:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.
        model_name: HuggingFace model identifier.
        device: Compute device ('cpu' or 'cuda').
        batch_size: Batch size for encoding.
        normalize: Whether to L2-normalize embeddings.

    Returns:
        np.ndarray of shape (len(texts), embedding_dim).
    """
    model = get_embedding_model(model_name, device)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
        normalize_embeddings=normalize,
        convert_to_numpy=True,
    )
    return embeddings


def compute_similarity(
    query_embedding: np.ndarray,
    document_embeddings: np.ndarray,
) -> np.ndarray:
    """
    Compute cosine similarity between a query and document embeddings using PyTorch.

    Args:
        query_embedding: Shape (embedding_dim,) or (1, embedding_dim).
        document_embeddings: Shape (n_docs, embedding_dim).

    Returns:
        np.ndarray of similarity scores, shape (n_docs,).
    """
    q = torch.tensor(query_embedding, dtype=torch.float32)
    d = torch.tensor(document_embeddings, dtype=torch.float32)

    if q.dim() == 1:
        q = q.unsqueeze(0)

    similarity = torch.nn.functional.cosine_similarity(q, d)
    return similarity.numpy()
