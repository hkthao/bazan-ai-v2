"""Pipeline configuration — đọc từ environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ollama
    ollama_url: str = "http://localhost:11434"
    assess_model: str = "qwen3:8b"
    assess_context: int = 8192

    # Open WebUI
    openwebui_url: str = "http://localhost:3000"
    openwebui_api_key: str = ""
    kb_detail_id: str = ""  # ID của KB bazan_detail
    kb_summary_id: str = ""  # ID của KB bazan_summary

    # Pipeline
    quality_threshold_upload: int = 7
    quality_threshold_review: int = 4
    chunk_size: int = 512
    chunk_overlap: int = 64
    summary_max_words: int = 300
    upload_delay_seconds: float = 1.0

    # Paths
    raw_pdf_dir: Path = Path("../../data/raw/pdf")
    raw_md_dir: Path = Path("../../data/raw/markdown")
    review_dir: Path = Path("../../data/review")
    rejected_dir: Path = Path("../../data/rejected")
    index_db_path: Path = Path("../../data/index.db")


settings = Settings()
