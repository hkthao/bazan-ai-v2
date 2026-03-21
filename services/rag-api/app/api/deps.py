"""Dependency injection for FastAPI routes."""

from functools import lru_cache
from app.core.embedder import Embedder
from app.core.retriever import QdrantRetriever
from app.config import settings


@lru_cache
def get_embedder() -> Embedder:
    return Embedder(model_name=settings.embedding_model, device=settings.embedding_device)


@lru_cache
def get_retriever() -> QdrantRetriever:
    return QdrantRetriever(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
    )
