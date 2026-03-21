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
