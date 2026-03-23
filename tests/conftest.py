"""Shared pytest fixtures for Bazan AI test suite."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
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
    f.write_text(
        "# Canh tác cà phê\n\nNội dung hướng dẫn.\n\n## Tưới nước\n\nTưới 2 lần/tuần."
    )
    return f
