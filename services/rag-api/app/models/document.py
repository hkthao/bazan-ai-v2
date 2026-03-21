"""Internal document model used during ingestion pipeline."""

from dataclasses import dataclass, field


@dataclass
class Document:
    content: str
    metadata: dict = field(default_factory=dict)
