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
