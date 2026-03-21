"""Semantic search endpoint."""

from fastapi import APIRouter, Depends
from app.models.schemas import SearchRequest, SearchResponse
from app.core.embedder import Embedder
from app.core.retriever import QdrantRetriever
from app.api.deps import get_embedder, get_retriever

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(
    req: SearchRequest,
    embedder: Embedder = Depends(get_embedder),
    retriever: QdrantRetriever = Depends(get_retriever),
):
    vector = embedder.embed(req.query)
    results = retriever.search(vector, top_k=req.top_k, doc_type=req.doc_type)
    return SearchResponse(results=results, query=req.query)
