# TODO: replace with actual @step and @pipeline from zenml
"""ZenML-style pipeline skeleton orchestrating the data flow."""

from __future__ import annotations

import argparse
from typing import Iterable, List

from src.crawler.crawler import PlaceholderCrawler
from src.rag.embedder import get_embedding
from src.rag.vector_store import VectorStore


def crawl_step(urls: Iterable[str]) -> List[dict]:
    """Run the crawler and return raw documents."""
    crawler = PlaceholderCrawler()
    return crawler.crawl(urls)


def embed_step(documents: List[dict]) -> List[dict]:
    """Produce embeddings for each document."""
    embedded = []
    for document in documents:
        embedding = get_embedding(document.get("text", ""))
        embedded.append({**document, "embedding": embedding})
    return embedded


def store_step(documents: List[dict]) -> None:
    """Persist embedding records via the vector store interface."""
    store = VectorStore()
    for document in documents:
        store.upsert(
            document_id=str(document.get("_id")),
            embedding=document.get("embedding", []),
            metadata={"url": document.get("url")},
        )
    print(f"Stored {len(documents)} embedded documents via vector store stub.")


def run_pipeline(urls: Iterable[str]) -> None:
    """Execute the dummy ZenML pipeline."""
    raw_documents = crawl_step(urls)
    embedded_documents = embed_step(raw_documents)
    store_step(embedded_documents)
    print("Pipeline execution completed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the dummy ZenML pipeline")
    parser.add_argument(
        "urls",
        metavar="URL",
        nargs="+",
        help="List of URLs to process through the pipeline.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.urls)
