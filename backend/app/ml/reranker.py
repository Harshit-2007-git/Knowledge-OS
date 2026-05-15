"""
Reranker module — PyTorch-based reranking for search results.

Implements cross-encoder style reranking for improved retrieval quality.
Future: integrate with a fine-tuned cross-encoder model.
"""

import logging
import torch
import torch.nn.functional as F
import numpy as np

logger = logging.getLogger(__name__)


def rerank_by_similarity(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    candidate_ids: list[str],
    top_k: int = 10,
) -> list[tuple[str, float]]:
    """
    Rerank candidates by cosine similarity to the query.

    Args:
        query_embedding: Query vector, shape (dim,).
        candidate_embeddings: Candidate vectors, shape (n, dim).
        candidate_ids: Corresponding IDs for each candidate.
        top_k: Number of top results to return.

    Returns:
        List of (candidate_id, score) tuples, sorted descending.
    """
    q = torch.tensor(query_embedding, dtype=torch.float32).unsqueeze(0)
    c = torch.tensor(candidate_embeddings, dtype=torch.float32)

    scores = F.cosine_similarity(q, c).numpy()

    ranked_indices = np.argsort(scores)[::-1][:top_k]
    return [
        (candidate_ids[idx], float(scores[idx]))
        for idx in ranked_indices
    ]


# TODO: Phase 4 — implement cross-encoder reranking
# class CrossEncoderReranker:
#     def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
#         ...
#     def rerank(self, query: str, documents: list[str], top_k: int = 10):
#         ...
