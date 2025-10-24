"""Configuration helpers for the LLM Twin data infrastructure."""

from pymongo import MongoClient

MONGO_URI = "mongodb://root:rootpass@localhost:27017"
MONGO_DB = "llm_twin"

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "llm_documents"


def get_mongo_client() -> MongoClient:
    """Return a MongoDB client configured for the project."""
    return MongoClient(MONGO_URI)
