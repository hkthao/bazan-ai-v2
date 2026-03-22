"""Hierarchical chunking với context prefix cho RAG."""

from dataclasses import dataclass
from extractor import ExtractedDoc


@dataclass
class Chunk:
    content: str         # text đầy đủ bao gồm context prefix
    source_file: str
    section_heading: str
    page: int | None
    chunk_index: int


def chunk_document(doc: ExtractedDoc, source_name: str,
                   chunk_size: int = 512, overlap: int = 64) -> list[Chunk]:
    chunks = []

    for section in doc.sections:
        text = section["content"]
        words = text.split()
        heading = section.get("heading", "")
        page = section.get("page")

        # Context prefix — giúp LLM biết chunk này thuộc về đâu
        if page:
            prefix = f"[{source_name} | {heading} | Trang {page}]\n"
        else:
            prefix = f"[{source_name} | {heading}]\n"

        # Split theo word count
        start = 0
        idx = 0
        while start < len(words):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end])

            if chunk_text.strip():
                chunks.append(Chunk(
                    content=prefix + chunk_text,
                    source_file=source_name,
                    section_heading=heading,
                    page=page,
                    chunk_index=idx,
                ))
                idx += 1

            start += chunk_size - overlap

    return chunks


def create_summary_document(summary_text: str, source_name: str,
                            metadata: dict) -> str:
    """Tạo document summary với metadata header."""
    topic = metadata.get("topic", "")
    region = metadata.get("region", "")
    quality = metadata.get("quality_score", "")
    doc_type = metadata.get("doc_type", "")

    header = f"""---
Tài liệu: {source_name}
Chủ đề: {topic}
Vùng: {region}
Loại: {doc_type}
Chất lượng: {quality}/10
---

"""
    return header + summary_text
