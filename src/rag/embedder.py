"""Embedding utilities for the RAG pipeline."""

from __future__ import annotations

from typing import List

from sentence_transformers import SentenceTransformer

_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def get_embedding(text: str) -> List[float]:
    """Return an embedding vector for the provided text using SentenceTransformers."""

    embedding = _MODEL.encode(text)
    return embedding.tolist()
