# Bazan AI

Bazan AI là một chatbot tra cứu kiến thức cà phê Tây Nguyên, giúp người dân và doanh nghiệp dễ dàng tiếp cận các thông tin về kỹ thuật canh tác, giá cả thị trường và quản lý vườn cây.

## Architecture

Project bao gồm các service chính:
- `open-webui`: Chat UI cho người dùng cuối.
- `pipelines`: Chế biến và điều phối (orchestration) giữa LLM và RAG.
- `rag-api`: FastAPI service quản lý việc ingest và tìm kiếm tài liệu (vector search).
- `qdrant`: Vector database lưu trữ tri thức.
- `ollama`: Chạy LLM (Local).
- `data-collector`: Thu thập dữ liệu giá cả thị trường.

## Quick Start

1. Sao chép file cấu hình:
   ```bash
   cp .env.example .env
   ```
2. Chạy ứng dụng bằng Docker Compose:
   ```bash
   make dev
   ```
3. Truy cập Web UI tại `http://localhost:3000`.

## Services

| Service | Port | Description |
|---|---|---|
| Open WebUI | 3000 | Frontend chat |
| RAG API | 8001 | FastAPI search & ingest |
| Qdrant | 6333 | Vector DB |
| Ollama | 11434 | LLM API |

## Development

Sử dụng `uv` để quản lý dependencies và `ruff` để lint/format code.
Chi tiết xem tại `docs/deployment.md`.
