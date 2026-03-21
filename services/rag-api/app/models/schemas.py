"""Pydantic schemas for API request and response models."""

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    doc_type: str | None = None


class SearchResult(BaseModel):
    content: str
    source: str
    score: float
    metadata: dict


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str


class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int
    source: str
