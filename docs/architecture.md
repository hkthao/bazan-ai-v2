# System Architecture

## Overview
Bazan AI is built on a microservices architecture to ensure scalability and maintainability.

## Component Interaction
- **Open WebUI**: User interface for chatting.
- **Pipelines**: Acts as an intermediary, injecting RAG context.
- **RAG API**: Handles document ingestion and vector search.
- **Qdrant**: Stores document embeddings.
- **Ollama**: Provides local LLM capabilities.
