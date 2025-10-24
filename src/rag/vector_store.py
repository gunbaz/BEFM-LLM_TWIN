"""Vector store interface skeleton for RAG components."""

from __future__ import annotations

from typing import Any, Dict, List


class VectorStore:
    """Interface-like skeleton that mimics a Qdrant-style vector store."""

    def upsert(self, document_id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        """Persist the embedding and metadata for a document identifier."""
        # TODO: Implement persistence with a vector database such as Qdrant.
        pass

    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Return the closest matches for the provided query embedding."""
        # TODO: Implement similarity search against the vector database.
        pass
