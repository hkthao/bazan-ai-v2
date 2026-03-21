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
