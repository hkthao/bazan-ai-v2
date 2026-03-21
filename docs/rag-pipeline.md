# RAG Pipeline

## Ingestion Flow
1. Load document (PDF/Markdown).
2. Chunk text using specific strategies.
3. Generate embeddings using BAAI/bge-m3.
4. Upsert to Qdrant.

## Search Strategy
- Vector search with cosine similarity.
- Metadata filtering support.
