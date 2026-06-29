"""model.py — the deployed support-ticket classifier (the thing being monitored).

TF-IDF + LogisticRegression trained ONLY on the 4 known categories. Kept tiny
and deterministic so it trains in well under a second at app startup.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

import config


def train_model(reference_df):
    """Fit TF-IDF + LogisticRegression on the 4 trained classes.

    Returns (vectorizer, clf).
    """
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    X = vectorizer.fit_transform(reference_df["text"])
    y = reference_df["label"]

    clf = LogisticRegression(max_iter=1000, random_state=config.SEED)
    clf.fit(X, y)
    return vectorizer, clf


def score(vectorizer, clf, texts):
    """Predict label + confidence (max predict_proba) for each text.

    Returns a DataFrame with columns: text, predicted_label, confidence.
    """
    texts = list(texts)
    X = vectorizer.transform(texts)
    proba = clf.predict_proba(X)
    idx = proba.argmax(axis=1)
    labels = clf.classes_[idx]
    confidence = proba.max(axis=1)
    return pd.DataFrame(
        {
            "text": texts,
            "predicted_label": labels,
            "confidence": confidence,
        }
    )


def mean_confidence(scored_df):
    """Average top-class confidence across a scored batch."""
    if len(scored_df) == 0:
        return 0.0
    return float(scored_df["confidence"].mean())


def class_distribution(labels, categories=None):
    """Normalized predicted-class distribution as a dict {category: fraction}."""
    if categories is None:
        categories = config.CATEGORIES
    counts = pd.Series(list(labels)).value_counts()
    total = counts.sum()
    if total == 0:
        return {c: 0.0 for c in categories}
    return {c: float(counts.get(c, 0)) / float(total) for c in categories}
