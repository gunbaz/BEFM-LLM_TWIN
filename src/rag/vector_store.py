"""Qdrant-backed vector store implementation for RAG components."""

from __future__ import annotations

from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from src.config import QDRANT_COLLECTION, QDRANT_HOST, QDRANT_PORT


class VectorStore:
    """Interact with a Qdrant collection to manage document embeddings."""

    def __init__(
        self,
        *,
        host: str = QDRANT_HOST,
        port: int = QDRANT_PORT,
        collection_name: str = QDRANT_COLLECTION,
        vector_size: int = 384,
    ) -> None:
        """Initialise the client and ensure the collection exists."""

        self.collection_name = collection_name
        self._client = QdrantClient(host=host, port=port)
        self._vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the target collection if it has not been provisioned yet."""

        if self._client.collection_exists(self.collection_name):
            return

        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=rest.VectorParams(
                size=self._vector_size,
                distance=rest.Distance.COSINE,
            ),
        )

    def upsert(self, document_id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        """Persist the embedding and metadata for a document identifier."""

        payload = {
            "url": metadata.get("url"),
            "text": metadata.get("text"),
            "status": metadata.get("status", "processed"),
        }

        self._client.upsert(
            collection_name=self.collection_name,
            points=[
                rest.PointStruct(
                    id=document_id,
                    vector=list(embedding),
                    payload=payload,
                )
            ],
        )

    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Return the closest matches for the provided query embedding."""

        results = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k,
        )

        return [
            {
                "document_id": str(match.id),
                "score": match.score,
                "metadata": match.payload or {},
            }
            for match in results
        ]
