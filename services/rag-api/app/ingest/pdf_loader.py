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
                        docs.append(
                            Document(
                                content=table_text,
                                metadata={
                                    "source": path.name,
                                    "page": i + 1,
                                    "type": "table",
                                    "doc_type": "pdf",
                                },
                            )
                        )

                # Plain text
                text = page.extract_text() or ""
                if text.strip():
                    docs.append(
                        Document(
                            content=text,
                            metadata={
                                "source": path.name,
                                "page": i + 1,
                                "type": "text",
                                "doc_type": "pdf",
                            },
                        )
                    )
        return docs

    def _table_to_markdown(self, table: list) -> str:
        rows = [" | ".join(str(c or "").strip() for c in row) for row in table if row]
        return "\n".join(rows)
