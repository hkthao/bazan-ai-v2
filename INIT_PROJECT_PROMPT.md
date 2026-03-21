Khởi tạo project **Bazan AI** theo đúng cấu trúc và cấu hình dưới đây. Thực hiện từng bước, xác nhận từng bước trước khi chuyển sang bước tiếp theo.

---

## Yêu cầu tổng quát

- Package manager: `uv`
- Python: 3.12
- Lint/format: `ruff`
- Test runner: `pytest`
- Tất cả file Python phải có docstring ngắn ở đầu mô tả mục đích
- Tất cả biến môi trường đọc qua `config.py` (pydantic-settings), không đọc `os.environ` trực tiếp trong code logic
- Không tạo file thừa ngoài danh sách dưới đây

---

## Bước 1 — Tạo cấu trúc thư mục gốc

Tạo toàn bộ thư mục sau (chưa tạo file):

```
bazan-ai/
├── services/
│   ├── rag-api/
│   │   ├── app/
│   │   │   ├── api/routes/
│   │   │   ├── core/
│   │   │   ├── ingest/
│   │   │   └── models/
│   │   └── tests/fixtures/
│   ├── pipelines/
│   │   ├── pipelines/
│   │   └── tools/
│   └── data-collector/
├── data/
│   ├── raw/pdf/
│   ├── raw/markdown/
│   ├── processed/chunks/
│   └── seeds/
├── infra/
│   ├── nginx/
│   └── scripts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/
```

---

## Bước 2 — Root level files

### `.gitignore`

```
.env
.env.local
*.env
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
.DS_Store
Thumbs.db
*.log
logs/
infra/nginx/ssl/
data/raw/
data/processed/
chromadb/
.mypy_cache/
.ruff_cache/
.pytest_cache/
htmlcov/
.coverage
```

### `.env.example`

```env
# LLM
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://ollama:11434

# Open WebUI
WEBUI_SECRET_KEY=change-this-in-production
WEBUI_PORT=3000

# RAG
RAG_API_URL=http://rag-api:8001
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=bazan_knowledge
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32

# External APIs
OPENWEATHER_API_KEY=
PRICE_GOOGLE_SHEET_ID=

# Auth (optional)
ENABLE_OAUTH=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### `Makefile`

```makefile
.PHONY: dev stop logs ingest ingest-pdf ingest-md backup \
        test test-unit test-int coverage lint format typecheck \
        shell-rag pull-model

# Docker
dev:
	docker compose -f infra/docker-compose.yml up -d

stop:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

# Data
ingest:
	bash infra/scripts/ingest_all.sh

ingest-pdf:
	bash infra/scripts/ingest_all.sh --type pdf

ingest-md:
	bash infra/scripts/ingest_all.sh --type markdown

backup:
	bash infra/scripts/backup_db.sh

# Testing
test:
	pytest tests/

test-unit:
	pytest tests/unit/

test-int:
	pytest tests/integration/

coverage:
	pytest --cov=services --cov-report=html tests/

# Code quality
lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy services/

# Utils
shell-rag:
	docker compose -f infra/docker-compose.yml exec rag-api bash

pull-model:
	docker compose -f infra/docker-compose.yml exec ollama ollama pull llama3.2
```

### `README.md`

Tạo README ngắn gọn với các mục: Project Overview, Architecture, Quick Start, Services, Development.

---

## Bước 3 — `services/rag-api/`

### `pyproject.toml`

```toml
[project]
name = "bazan-rag-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "qdrant-client>=1.9.0",
    "sentence-transformers>=3.0.0",
    "pdfplumber>=0.11.0",
    "surya-ocr>=0.4.0",
    "python-multipart>=0.0.9",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### `app/config.py`

```python
"""Application configuration — all settings read from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "bazan_knowledge"

    # Embedding
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 32

    # App
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    log_level: str = "info"


settings = Settings()
```

### `app/main.py`

```python
"""Bazan AI — RAG API entry point."""

from fastapi import FastAPI
from app.api.routes import search, ingest, health

app = FastAPI(title="Bazan AI RAG API", version="0.1.0")

app.include_router(health.router, tags=["health"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
```

### `app/models/schemas.py`

```python
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
```

### `app/models/document.py`

```python
"""Internal document model used during ingestion pipeline."""

from dataclasses import dataclass, field


@dataclass
class Document:
    content: str
    metadata: dict = field(default_factory=dict)
```

### `app/api/routes/health.py`

```python
"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}
```

### `app/api/routes/search.py`

```python
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
```

### `app/api/routes/ingest.py`

```python
"""Document ingest endpoint."""

from fastapi import APIRouter, UploadFile, File
from app.models.schemas import IngestResponse
from app.ingest.pipeline import IngestPipeline

router = APIRouter()
pipeline = IngestPipeline()


@router.post("", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    result = await pipeline.run_from_upload(file)
    return result
```

### `app/api/deps.py`

```python
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
```

### `app/core/embedder.py`

```python
"""Embedding model wrapper using sentence-transformers (BAAI/bge-m3)."""

from sentence_transformers import SentenceTransformer
from app.config import settings


class Embedder:
    def __init__(self, model_name: str = settings.embedding_model, device: str = settings.embedding_device):
        self.model = SentenceTransformer(model_name, device=device)
        self.vector_size = self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(
            texts,
            batch_size=settings.embedding_batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).tolist()
```

### `app/core/retriever.py`

```python
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
```

### `app/core/chunker.py`

```python
"""Text chunking strategies for RAG pipeline."""


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return [c for c in chunks if c.strip()]
```

### `app/ingest/base_loader.py`

```python
"""Abstract base class for document loaders."""

from abc import ABC, abstractmethod
from pathlib import Path
from app.models.document import Document


class BaseLoader(ABC):
    @abstractmethod
    def load(self, path: Path) -> list[Document]:
        """Load a file and return a list of Documents."""
        ...

    def supports(self, path: Path) -> bool:
        """Return True if this loader handles the given file extension."""
        return path.suffix.lower() in self.extensions

    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        ...
```

### `app/ingest/pdf_loader.py`

```python
"""PDF loader — extracts text and tables using pdfplumber, falls back to OCR."""

from pathlib import Path
import pdfplumber
from app.ingest.base_loader import BaseLoader
from app.models.document import Document


class PDFLoader(BaseLoader):
    extensions = [".pdf"]

    def load(self, path: Path) -> list[Document]:
        docs = []
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                # Tables first — preserve structure
                for table in page.extract_tables():
                    table_text = self._table_to_markdown(table)
                    if table_text.strip():
                        docs.append(Document(
                            content=table_text,
                            metadata={"source": path.name, "page": i + 1, "type": "table", "doc_type": "pdf"},
                        ))

                # Plain text
                text = page.extract_text() or ""
                if text.strip():
                    docs.append(Document(
                        content=text,
                        metadata={"source": path.name, "page": i + 1, "type": "text", "doc_type": "pdf"},
                    ))
        return docs

    def _table_to_markdown(self, table: list) -> str:
        rows = [" | ".join(str(c or "").strip() for c in row) for row in table if row]
        return "\n".join(rows)
```

### `app/ingest/md_loader.py`

```python
"""Markdown loader — splits document by headers (H1-H3) preserving context."""

import re
from pathlib import Path
from app.ingest.base_loader import BaseLoader
from app.models.document import Document


class MarkdownLoader(BaseLoader):
    extensions = [".md", ".markdown"]

    def load(self, path: Path) -> list[Document]:
        text = path.read_text(encoding="utf-8")
        sections = self._split_by_headers(text)
        return [
            Document(
                content=section["content"],
                metadata={
                    "source": path.name,
                    "heading": section["heading"],
                    "level": section["level"],
                    "doc_type": "markdown",
                },
            )
            for section in sections
            if section["content"].strip()
        ]

    def _split_by_headers(self, text: str) -> list[dict]:
        pattern = r"^(#{1,3})\s+(.+)$"
        sections = []
        current = {"heading": "intro", "level": 0, "content": ""}

        for line in text.splitlines():
            match = re.match(pattern, line)
            if match:
                if current["content"].strip():
                    sections.append(current)
                current = {
                    "heading": match.group(2).strip(),
                    "level": len(match.group(1)),
                    "content": line + "\n",
                }
            else:
                current["content"] += line + "\n"

        if current["content"].strip():
            sections.append(current)
        return sections
```

### `app/ingest/pipeline.py`

```python
"""Ingest pipeline — orchestrates load → chunk → embed → upsert to Qdrant."""

from pathlib import Path
from fastapi import UploadFile
import tempfile

from app.ingest.base_loader import BaseLoader
from app.ingest.pdf_loader import PDFLoader
from app.ingest.md_loader import MarkdownLoader
from app.core.embedder import Embedder
from app.core.retriever import QdrantRetriever
from app.core.chunker import chunk_text
from app.models.schemas import IngestResponse
from app.api.deps import get_embedder, get_retriever


class IngestPipeline:
    def __init__(self):
        self.loaders: list[BaseLoader] = [PDFLoader(), MarkdownLoader()]
        self.embedder: Embedder = get_embedder()
        self.retriever: QdrantRetriever = get_retriever()

    def _get_loader(self, path: Path) -> BaseLoader | None:
        for loader in self.loaders:
            if loader.supports(path):
                return loader
        return None

    def run(self, path: Path) -> IngestResponse:
        loader = self._get_loader(path)
        if not loader:
            raise ValueError(f"No loader found for file: {path.suffix}")

        docs = loader.load(path)
        all_chunks = []
        for doc in docs:
            for chunk_text_content in chunk_text(doc.content):
                all_chunks.append({"content": chunk_text_content, "metadata": doc.metadata})

        embeddings = self.embedder.embed_batch([c["content"] for c in all_chunks])
        upsert_docs = [
            {"content": c["content"], "embedding": e, "metadata": c["metadata"]}
            for c, e in zip(all_chunks, embeddings)
        ]
        self.retriever.upsert(upsert_docs)

        return IngestResponse(
            status="ok",
            chunks_indexed=len(upsert_docs),
            source=path.name,
        )

    async def run_from_upload(self, file: UploadFile) -> IngestResponse:
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = Path(tmp.name)
        try:
            return self.run(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
```

### `Dockerfile` (rag-api)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system .

COPY app/ app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### `.env.example` (rag-api)

```env
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=bazan_knowledge
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DEVICE=cpu
EMBEDDING_BATCH_SIZE=32
API_HOST=0.0.0.0
API_PORT=8001
LOG_LEVEL=info
```

---

## Bước 4 — `services/pipelines/`

### `pipelines/bazan_rag_pipeline.py`

```python
"""Bazan AI RAG Pipeline — injects knowledge context before LLM call."""

from typing import Optional
import httpx
from app.config import settings  # noqa: F401 — placeholder


class Pipeline:
    def __init__(self):
        self.name = "Bazan AI RAG Pipeline"
        self.rag_api_url = "http://rag-api:8001"

    async def on_startup(self):
        print(f"[Bazan Pipeline] started — RAG API: {self.rag_api_url}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Intercept request, fetch relevant context, inject into system prompt."""
        query = body.get("messages", [{}])[-1].get("content", "")
        if not query:
            return body

        context = await self._fetch_context(query)
        if context:
            system_msg = {
                "role": "system",
                "content": (
                    "Bạn là trợ lý chuyên về cà phê Tây Nguyên. "
                    "Dựa vào tài liệu sau để trả lời:\n\n" + context
                ),
            }
            body["messages"] = [system_msg] + body.get("messages", [])
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        return body

    async def _fetch_context(self, query: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    f"{self.rag_api_url}/search",
                    json={"query": query, "top_k": 5},
                )
                results = resp.json().get("results", [])
                return "\n\n".join(
                    f"[{r['source']}]\n{r['content']}" for r in results
                )
            except Exception as e:
                print(f"[Bazan Pipeline] RAG fetch failed: {e}")
                return ""
```

### `tools/weather_tool.py`

```python
"""Weather tool — 7-day forecast for Tay Nguyen coffee provinces."""

import httpx
from pydantic import BaseModel, Field


PROVINCES = {
    "dak_lak": {"name": "Đắk Lắk", "q": "Buon Ma Thuot,VN"},
    "lam_dong": {"name": "Lâm Đồng", "q": "Da Lat,VN"},
    "gia_lai": {"name": "Gia Lai", "q": "Pleiku,VN"},
    "kon_tum": {"name": "Kon Tum", "q": "Kon Tum,VN"},
    "dak_nong": {"name": "Đắk Nông", "q": "Gia Nghia,VN"},
}


class Tools:
    class Valves(BaseModel):
        OPENWEATHER_API_KEY: str = Field(default="", description="OpenWeatherMap API key")

    def __init__(self):
        self.valves = self.Valves()

    def get_weather(self, province: str) -> str:
        """
        Lấy dự báo thời tiết 7 ngày cho tỉnh Tây Nguyên.
        :param province: Tên tỉnh (dak_lak, lam_dong, gia_lai, kon_tum, dak_nong)
        :return: Thông tin thời tiết dạng text
        """
        info = PROVINCES.get(province.lower())
        if not info:
            return f"Không tìm thấy tỉnh '{province}'. Các tỉnh hỗ trợ: {', '.join(PROVINCES.keys())}"

        try:
            resp = httpx.get(
                "https://api.openweathermap.org/data/2.5/forecast",
                params={"q": info["q"], "appid": self.valves.OPENWEATHER_API_KEY,
                        "lang": "vi", "units": "metric", "cnt": 7},
                timeout=10.0,
            )
            data = resp.json()
            lines = [f"Thời tiết {info['name']}:"]
            for item in data.get("list", [])[:7]:
                lines.append(
                    f"- {item['dt_txt']}: {item['weather'][0]['description']}, "
                    f"{item['main']['temp']:.1f}°C, độ ẩm {item['main']['humidity']}%"
                )
            return "\n".join(lines)
        except Exception as e:
            return f"Lỗi khi lấy thời tiết: {e}"
```

### `tools/price_tool.py`

```python
"""Coffee price tool — retrieves current robusta/arabica prices."""

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        PRICE_API_URL: str = Field(
            default="http://data-collector:8002/prices/latest",
            description="URL của price API nội bộ",
        )

    def __init__(self):
        self.valves = self.Valves()

    def get_coffee_price(self, province: str = "") -> str:
        """
        Lấy giá cà phê nhân xô hiện tại.
        :param province: Tên tỉnh (để trống = lấy tất cả)
        :return: Bảng giá dạng text
        """
        import httpx
        try:
            params = {"province": province} if province else {}
            resp = httpx.get(self.valves.PRICE_API_URL, params=params, timeout=10.0)
            data = resp.json()
            lines = ["Giá cà phê nhân xô (VNĐ/kg):"]
            for item in data.get("prices", []):
                lines.append(f"- {item['province']}: {item['price']:,} đ/kg ({item['date']})")
            return "\n".join(lines)
        except Exception as e:
            return f"Lỗi khi lấy giá cà phê: {e}"
```

### `tools/farming_plan_tool.py`

```python
"""Farming plan tool — generates cultivation schedule based on inputs."""

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def create_farming_plan(self, province: str, area_ha: float, current_month: int) -> str:
        """
        Tạo kế hoạch trồng trọt cà phê dựa theo địa điểm và thời điểm hiện tại.
        :param province: Tỉnh trồng cà phê
        :param area_ha: Diện tích (ha)
        :param current_month: Tháng hiện tại (1-12)
        :return: Kế hoạch canh tác dạng text
        """
        # Placeholder — logic sẽ được implement trong issue tiếp theo
        return (
            f"Kế hoạch canh tác cà phê tại {province}, "
            f"diện tích {area_ha} ha, tháng {current_month}:\n"
            "[Nội dung sẽ được bổ sung từ knowledge base]"
        )
```

### `tools/soil_tool.py`

```python
"""Soil and nutrition lookup tool for Tay Nguyen coffee farming."""

from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def get_soil_info(self, province: str) -> str:
        """
        Tra cứu thông tin đất đai và dinh dưỡng phù hợp cho cà phê tại tỉnh.
        :param province: Tên tỉnh Tây Nguyên
        :return: Thông tin đất đai dạng text
        """
        # Placeholder — sẽ đọc từ seeds/soil_types.json
        return f"Thông tin đất đai tỉnh {province}: [sẽ được bổ sung]"
```

---

## Bước 5 — `infra/`

### `infra/docker-compose.yml`

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - OPENAI_API_BASE_URL=http://pipelines:9099
      - OPENAI_API_KEY=0p3n-w3bu!
    volumes:
      - webui_data:/app/backend/data
    depends_on:
      - ollama
      - pipelines
    restart: always

  pipelines:
    build: ../services/pipelines
    ports:
      - "9099:9099"
    environment:
      - RAG_API_URL=http://rag-api:8001
    env_file:
      - ../.env
    depends_on:
      - rag-api
    restart: unless-stopped

  rag-api:
    build: ../services/rag-api
    ports:
      - "8001:8001"
    env_file:
      - ../services/rag-api/.env
    depends_on:
      - qdrant
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  data-collector:
    build: ../services/data-collector
    env_file:
      - ../.env
    depends_on:
      - qdrant
    restart: unless-stopped

volumes:
  ollama_data:
  webui_data:
  qdrant_data:
```

### `infra/scripts/ingest_all.sh`

```bash
#!/usr/bin/env bash
set -e

TYPE=${1:-all}
RAW_DIR="$(dirname "$0")/../../data/raw"
API_URL="http://localhost:8001/ingest"

ingest_dir() {
  local dir=$1
  echo "Ingesting files in $dir..."
  find "$dir" -type f | while read -r file; do
    echo "  -> $(basename "$file")"
    curl -s -X POST "$API_URL" \
      -F "file=@$file" \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'     {d[\"chunks_indexed\"]} chunks')"
  done
}

case $TYPE in
  pdf)      ingest_dir "$RAW_DIR/pdf" ;;
  markdown) ingest_dir "$RAW_DIR/markdown" ;;
  all)
    ingest_dir "$RAW_DIR/pdf"
    ingest_dir "$RAW_DIR/markdown"
    ;;
  *)
    echo "Usage: $0 [pdf|markdown|all]"
    exit 1
    ;;
esac

echo "Done."
```

### `infra/scripts/backup_db.sh`

```bash
#!/usr/bin/env bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backing up Qdrant..."
docker compose -f infra/docker-compose.yml exec qdrant \
  tar czf - /qdrant/storage > "$BACKUP_DIR/qdrant.tar.gz"

echo "Backup saved to $BACKUP_DIR"
```

---

## Bước 6 — `tests/`

### `tests/conftest.py`

```python
"""Shared pytest fixtures for Bazan AI test suite."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def sample_pdf_path(tmp_path):
    """Creates a minimal temp file to simulate PDF upload in tests."""
    f = tmp_path / "sample.pdf"
    f.write_bytes(b"%PDF-1.4 sample")
    return f


@pytest.fixture
def sample_md_path(tmp_path):
    f = tmp_path / "guide.md"
    f.write_text("# Canh tác cà phê\n\nNội dung hướng dẫn.\n\n## Tưới nước\n\nTưới 2 lần/tuần.")
    return f
```

### `tests/unit/test_chunker.py`

```python
"""Unit tests for text chunker."""

from app.core.chunker import chunk_text


def test_chunk_basic():
    text = " ".join(["word"] * 600)
    chunks = chunk_text(text, chunk_size=512, overlap=64)
    assert len(chunks) >= 2


def test_chunk_empty():
    assert chunk_text("") == []


def test_chunk_overlap():
    text = " ".join([str(i) for i in range(100)])
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    # Each chunk except the last should share 2 words with the next
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]
```

### `tests/unit/test_md_loader.py`

```python
"""Unit tests for Markdown loader."""

from pathlib import Path
from app.ingest.md_loader import MarkdownLoader


def test_md_splits_by_headers(sample_md_path):
    loader = MarkdownLoader()
    docs = loader.load(sample_md_path)
    assert len(docs) >= 2
    headings = [d.metadata["heading"] for d in docs]
    assert "Canh tác cà phê" in headings
    assert "Tưới nước" in headings


def test_md_metadata(sample_md_path):
    loader = MarkdownLoader()
    docs = loader.load(sample_md_path)
    assert all(d.metadata["doc_type"] == "markdown" for d in docs)
    assert all(d.metadata["source"] == sample_md_path.name for d in docs)
```

---

## Bước 7 — `data/seeds/` placeholder files

Tạo 4 file JSON placeholder:

**`data/seeds/provinces.json`**
```json
[
  {"id": "dak_lak",  "name": "Đắk Lắk",  "lat": 12.6667, "lon": 108.0500, "weather_q": "Buon Ma Thuot,VN"},
  {"id": "lam_dong", "name": "Lâm Đồng", "lat": 11.9465, "lon": 108.4419, "weather_q": "Da Lat,VN"},
  {"id": "gia_lai",  "name": "Gia Lai",  "lat": 13.9833, "lon": 108.0000, "weather_q": "Pleiku,VN"},
  {"id": "kon_tum",  "name": "Kon Tum",  "lat": 14.3500, "lon": 107.9833, "weather_q": "Kon Tum,VN"},
  {"id": "dak_nong", "name": "Đắk Nông", "lat": 12.0046, "lon": 107.6903, "weather_q": "Gia Nghia,VN"}
]
```

**`data/seeds/soil_types.json`**
```json
[
  {"id": "do_bazan", "name": "Đất đỏ bazan", "provinces": ["dak_lak", "gia_lai", "lam_dong"], "ph_range": [5.5, 6.5], "notes": "Thích hợp nhất cho cà phê Robusta và Arabica"},
  {"id": "xam_bac_mau", "name": "Đất xám bạc màu", "provinces": ["kon_tum"], "ph_range": [4.5, 5.5], "notes": "Cần bổ sung hữu cơ"}
]
```

**`data/seeds/crop_calendar.json`**
```json
{
  "robusta": {
    "pruning":    [1, 2],
    "fertilize1": [3, 4],
    "bloom":      [3, 4, 5],
    "fertilize2": [6, 7],
    "harvest":    [10, 11, 12]
  },
  "arabica": {
    "pruning":    [2, 3],
    "fertilize1": [4, 5],
    "bloom":      [4, 5, 6],
    "fertilize2": [7, 8],
    "harvest":    [11, 12, 1]
  }
}
```

**`data/seeds/nutrition_db.json`**
```json
[
  {"stage": "sau_thu_hoach", "n_kg_ha": 80,  "p_kg_ha": 40, "k_kg_ha": 80,  "notes": "Bổ sung hữu cơ sau thu hoạch"},
  {"stage": "ra_hoa",        "n_kg_ha": 60,  "p_kg_ha": 60, "k_kg_ha": 60,  "notes": "Tăng lân để kích thích ra hoa"},
  {"stage": "nuoi_trai",     "n_kg_ha": 100, "p_kg_ha": 30, "k_kg_ha": 120, "notes": "Tăng kali để nuôi trái"}
]
```

---

## Bước 8 — `docs/`

Tạo 4 file Markdown placeholder với heading structure chuẩn (nội dung sẽ được bổ sung sau):

- `docs/architecture.md` — System architecture, service interactions
- `docs/rag-pipeline.md` — RAG pipeline: ingest flow, chunking strategy, embedding
- `docs/tools.md` — Danh sách tools, cách đăng ký tool mới
- `docs/deployment.md` — Setup dev, production deployment checklist

---

## Xác nhận hoàn thành

Sau khi tạo xong toàn bộ, chạy các lệnh kiểm tra sau và báo cáo kết quả:

```bash
# Kiểm tra cấu trúc thư mục
find bazan-ai -type f | sort

# Kiểm tra syntax Python
cd bazan-ai/services/rag-api
uv run python -c "from app.main import app; print('OK')"

# Chạy tests
uv run pytest tests/unit/ -v
```

Nếu có lỗi import hoặc syntax, tự sửa trước khi báo cáo hoàn thành.
