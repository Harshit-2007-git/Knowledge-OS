"""
Document clustering using scikit-learn.

Supports K-Means and DBSCAN clustering with TF-IDF features.
"""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class DocumentClusterer:
    """
    Cluster documents using TF-IDF + clustering algorithms.

    Supports:
    - K-Means clustering
    - DBSCAN (density-based)
    """

    def __init__(self, method: str = "kmeans", n_clusters: int = 5):
        self.method = method
        self.n_clusters = n_clusters
        self._vectorizer = None
        self._model = None

    def fit_predict(
        self,
        texts: list[str],
        document_ids: list[str],
    ) -> list[dict]:
        """
        Cluster documents and return cluster assignments.

        Args:
            texts: Document texts to cluster.
            document_ids: Corresponding document IDs.

        Returns:
            List of cluster results with IDs and keywords.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans, DBSCAN

        self._vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words="english",
        )
        X = self._vectorizer.fit_transform(texts)

        if self.method == "kmeans":
            self._model = KMeans(
                n_clusters=min(self.n_clusters, len(texts)),
                random_state=42,
                n_init=10,
            )
        elif self.method == "dbscan":
            self._model = DBSCAN(eps=0.5, min_samples=2)
        else:
            raise ValueError(f"Unknown clustering method: {self.method}")

        labels = self._model.fit_predict(X)

        # Extract top keywords per cluster
        feature_names = self._vectorizer.get_feature_names_out()
        clusters = {}
        for doc_idx, cluster_id in enumerate(labels):
            cluster_id = int(cluster_id)
            if cluster_id not in clusters:
                clusters[cluster_id] = {"document_ids": [], "tfidf_sum": np.zeros(X.shape[1])}
            clusters[cluster_id]["document_ids"].append(document_ids[doc_idx])
            clusters[cluster_id]["tfidf_sum"] += X[doc_idx].toarray().flatten()

        results = []
        for cluster_id, data in sorted(clusters.items()):
            top_indices = data["tfidf_sum"].argsort()[-5:][::-1]
            keywords = [feature_names[i] for i in top_indices]
            results.append({
                "cluster_id": cluster_id,
                "label": f"Cluster {cluster_id}",
                "document_ids": data["document_ids"],
                "keywords": keywords,
            })

        logger.info("Clustered %d documents into %d clusters", len(texts), len(results))
        return results
