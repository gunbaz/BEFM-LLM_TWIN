"""ZenML pipeline orchestrating ingestion, embedding, and vector storage."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from bson import ObjectId
from zenml import pipeline, step

from src.config import MONGO_DB, QDRANT_COLLECTION, get_mongo_client
from src.rag.embedder import get_embedding
from src.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _normalise_identifier(identifier: Any) -> str:
    """Convert Mongo identifiers into string form for downstream use."""

    if isinstance(identifier, ObjectId):
        return str(identifier)
    return str(identifier) if identifier is not None else ""


@step
def crawl_step() -> List[Dict[str, Any]]:
    """Load raw documents from MongoDB for further processing."""

    client = get_mongo_client()
    collection = client[MONGO_DB]["raw_documents"]
    documents = list(collection.find())
    logger.info("Fetched %d documents from MongoDB raw_documents collection.", len(documents))
    for document in documents:
        document["_id"] = _normalise_identifier(document.get("_id"))
    return documents


@step
def embed_step(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate embeddings for each raw document."""

    logger.info("Generating embeddings for %d documents.", len(documents))
    embedded_documents: List[Dict[str, Any]] = []
    for document in documents:
        text = document.get("text", "") or ""
        embedding = get_embedding(text)
        embedded_documents.append(
            {
                "document_id": document.get("_id") or document.get("id"),
                "url": document.get("url"),
                "text": text,
                "status": document.get("status", "processed"),
                "embedding": embedding,
            }
        )
    logger.info("Created embeddings for %d documents.", len(embedded_documents))
    return embedded_documents


@step
def store_step(documents: List[Dict[str, Any]]) -> None:
    """Persist embedding vectors and metadata into Qdrant."""

    store = VectorStore()
    upserted = 0
    for document in documents:
        document_id = document.get("document_id")
        if not document_id:
            logger.warning("Skipping document without identifier: %s", document)
            continue
        store.upsert(
            document_id=str(document_id),
            embedding=document.get("embedding", []),
            metadata={
                "url": document.get("url"),
                "text": document.get("text"),
                "status": document.get("status", "processed"),
            },
        )
        upserted += 1
    logger.info(
        "Upserted %d documents into Qdrant collection '%s'.",
        upserted,
        QDRANT_COLLECTION,
    )


@pipeline
def rag_data_pipeline() -> None:
    """Run the RAG data processing pipeline."""

    documents = crawl_step()
    embedded_documents = embed_step(documents)
    store_step(embedded_documents)


if __name__ == "__main__":
    logger.info("Starting ZenML RAG data pipeline run.")
    pipeline_run = rag_data_pipeline()
    pipeline_run.run()
    logger.info("ZenML RAG data pipeline completed.")
