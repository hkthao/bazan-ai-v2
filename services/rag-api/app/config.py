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
