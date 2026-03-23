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
