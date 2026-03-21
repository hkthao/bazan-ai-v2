# Deployment Guide

## Setup Development
1. Install `uv`.
2. `make dev` to start Docker containers.
3. `make ingest` to index initial data.

## Production Checklist
- Change `WEBUI_SECRET_KEY`.
- Configure persistent volumes.
- Use GPU for embeddings if available.
