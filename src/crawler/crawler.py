"""Placeholder crawler that stores dummy documents into MongoDB."""

from __future__ import annotations

import argparse
from typing import Iterable, List

from pymongo.collection import Collection

from src.config import MONGO_DB, get_mongo_client


class PlaceholderCrawler:
    """Generate placeholder documents for the provided URLs."""

    def __init__(self) -> None:
        client = get_mongo_client()
        database = client[MONGO_DB]
        self.collection: Collection = database["raw_documents"]

    def crawl(self, urls: Iterable[str]) -> List[dict]:
        """Insert placeholder documents for the given URLs and return them."""
        documents = []
        for url in urls:
            documents.append({"url": url, "text": "placeholder", "status": "raw"})

        if not documents:
            return []

        result = self.collection.insert_many(documents)
        inserted_documents: List[dict] = []
        for doc, inserted_id in zip(documents, result.inserted_ids):
            enriched = {**doc, "_id": inserted_id}
            inserted_documents.append(enriched)
        return inserted_documents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Placeholder crawler for LLM Twin")
    parser.add_argument(
        "urls",
        metavar="URL",
        nargs="+",
        help="List of URLs to crawl.",
    )
    return parser.parse_args()


def main(urls: Iterable[str]) -> None:
    crawler = PlaceholderCrawler()
    inserted_documents = crawler.crawl(urls)
    print(f"Inserted {len(inserted_documents)} documents into raw_documents collection.")


if __name__ == "__main__":
    arguments = parse_args()
    main(arguments.urls)
