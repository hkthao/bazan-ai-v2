"""Qdrant vector store client — upsert and search."""

import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)
from app.config import settings


class QdrantRetriever:
    def __init__(self, host: str, port: int, collection: str, vector_size: int = 1024):
        self.client = QdrantClient(host=host, port=port)
        self.collection = collection
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def upsert(self, docs: list[dict]) -> None:
        """docs: [{"content": str, "embedding": list[float], "metadata": dict}]"""
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=doc["embedding"],
                payload={"content": doc["content"], **doc["metadata"]},
            )
            for doc in docs
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        doc_type: str | None = None,
    ) -> list[dict]:
        query_filter = None
        if doc_type:
            query_filter = Filter(
                must=[FieldCondition(key="doc_type", match=MatchValue(value=doc_type))]
            )
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [
            {
                "content": r.payload["content"],
                "source": r.payload.get("source", ""),
                "score": r.score,
                "metadata": {k: v for k, v in r.payload.items() if k != "content"},
            }
            for r in results
        ]
