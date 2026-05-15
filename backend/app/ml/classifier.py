"""
Document classifier using scikit-learn.

Supports TF-IDF + various classifiers for document categorization.
"""

import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """
    TF-IDF based document classifier.

    Supports multiple backend classifiers:
    - Logistic Regression (default)
    - SVM
    - Random Forest
    """

    def __init__(self, classifier_type: str = "logistic_regression"):
        self.classifier_type = classifier_type
        self._vectorizer = None
        self._classifier = None
        self._is_fitted = False

    def fit(self, texts: list[str], labels: list[str]) -> None:
        """Train the classifier on labeled documents."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.svm import LinearSVC
        from sklearn.ensemble import RandomForestClassifier

        self._vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words="english",
        )
        X = self._vectorizer.fit_transform(texts)

        classifiers = {
            "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
            "svm": LinearSVC(max_iter=1000, random_state=42),
            "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
        }
        self._classifier = classifiers.get(self.classifier_type, classifiers["logistic_regression"])
        self._classifier.fit(X, labels)
        self._is_fitted = True
        logger.info("Classifier trained with %d samples, %d classes", len(texts), len(set(labels)))

    def predict(self, texts: list[str]) -> list[dict]:
        """Predict classes for new documents."""
        if not self._is_fitted:
            raise RuntimeError("Classifier has not been trained. Call fit() first.")

        X = self._vectorizer.transform(texts)
        predictions = self._classifier.predict(X)

        # Get confidence scores if available
        results = []
        if hasattr(self._classifier, "predict_proba"):
            probas = self._classifier.predict_proba(X)
            classes = self._classifier.classes_
            for pred, proba in zip(predictions, probas):
                results.append({
                    "predicted_class": pred,
                    "confidence": float(max(proba)),
                    "classes": {cls: float(p) for cls, p in zip(classes, proba)},
                })
        else:
            for pred in predictions:
                results.append({
                    "predicted_class": pred,
                    "confidence": 1.0,
                    "classes": {pred: 1.0},
                })

        return results
