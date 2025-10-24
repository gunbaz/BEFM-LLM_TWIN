"""Dummy embedding utilities for the RAG pipeline."""

from __future__ import annotations

from typing import List


def get_embedding(text: str) -> List[float]:
    """Return a placeholder embedding vector for the provided text."""
    _ = text
    return [0.0, 0.1, 0.2]
