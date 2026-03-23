"""Bazan AI — RAG API entry point."""

from fastapi import FastAPI

from app.api.routes import health, ingest, search

app = FastAPI(title="Bazan AI RAG API", version="0.1.0")

app.include_router(health.router, tags=["health"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
