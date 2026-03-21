"""Abstract base class for document loaders."""

from abc import ABC, abstractmethod
from pathlib import Path
from app.models.document import Document


class BaseLoader(ABC):
    @abstractmethod
    def load(self, path: Path) -> list[Document]:
        """Load a file and return a list of Documents."""
        ...

    def supports(self, path: Path) -> bool:
        """Return True if this loader handles the given file extension."""
        return path.suffix.lower() in self.extensions

    @property
    @abstractmethod
    def extensions(self) -> list[str]:
        ...
