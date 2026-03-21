# Bazan AI

Bazan AI là một chatbot tra cứu kiến thức cà phê Tây Nguyên, giúp người dân và doanh nghiệp dễ dàng tiếp cận các thông tin về kỹ thuật canh tác, giá cả thị trường và quản lý vườn cây.

## Quick Start

### Yêu cầu

- Docker >= 24.0
- Docker Compose >= 2.0
- 8GB RAM (cho model llama3.2:3b), 16GB+ (cho llama3.1:8b)

### Chạy lần đầu

1. Copy file env:
```bash
cp .env.example .env
```

2. Khởi động services:
```bash
make dev
```

3. Kéo model (lần đầu mất vài phút tùy tốc độ mạng):
```bash
make pull-model
```

4. Mở trình duyệt: http://localhost:3000
- Lần đầu truy cập: tạo tài khoản admin
- Chọn model `llama3.2` trong dropdown

### Các lệnh hay dùng
```bash
make dev          # Khởi động tất cả services
make stop         # Dừng tất cả services
make logs         # Xem log real-time
make status       # Kiểm tra trạng thái containers
make list-models  # Xem các model đã cài
make pull-model   # Kéo model mặc định (llama3.2)
```

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
