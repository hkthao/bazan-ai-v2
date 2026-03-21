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
