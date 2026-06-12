"""
KnowledgeLoader — scans a directory and loads markdown files into KnowledgeDocument objects.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from pydantic import ValidationError

from models.knowledge_document import KnowledgeDocument

logger = logging.getLogger(__name__)


class KnowledgeLoader:
    """
    Scans a local directory for markdown files and parses them into
    strongly typed KnowledgeDocument domain objects.
    """

    def __init__(self, root_dir: str | Path) -> None:
        """
        Initialize the loader.

        Args:
            root_dir: The root directory to scan (e.g., 'knowledge/')
        """
        self.root_dir = Path(root_dir)

    def load_documents(self) -> list[KnowledgeDocument]:
        """
        Walk the directory tree, parse all .md files, and return a list
        of validated KnowledgeDocuments.

        Returns:
            List of KnowledgeDocument objects.
        """
        if not self.root_dir.exists() or not self.root_dir.is_dir():
            logger.warning("Knowledge directory '%s' does not exist or is not a directory.", self.root_dir)
            return []

        documents: list[KnowledgeDocument] = []
        for file_path in self._find_markdown_files():
            doc = self._parse_file(file_path)
            if doc:
                documents.append(doc)

        logger.info("Loaded %d knowledge documents from '%s'.", len(documents), self.root_dir)
        return documents

    def _find_markdown_files(self) -> Generator[Path, None, None]:
        """Recursively yield all .md files in the root directory."""
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.lower().endswith(".md"):
                    yield Path(root) / file

    def _parse_file(self, file_path: Path) -> KnowledgeDocument | None:
        """Read a file and map it to a KnowledgeDocument."""
        try:
            content = file_path.read_text(encoding="utf-8").strip()
            if not content:
                logger.warning("File '%s' is empty. Skipping.", file_path)
                return None

            # Infer category from the immediate parent folder name
            category = file_path.parent.name
            if category == self.root_dir.name:
                category = "general"

            # Use filename without extension as title, nicely formatted
            title = file_path.stem.replace("_", " ").title()

            doc = KnowledgeDocument(
                id=str(uuid.uuid4()),
                title=title,
                category=category,
                content=content,
                source=str(file_path),
                tags=[category, title.lower()],
                created_at=datetime.now(timezone.utc).isoformat()
            )
            return doc

        except ValidationError as exc:
            logger.error("Validation failed for file '%s': %s", file_path, exc)
            return None
        except Exception as exc:
            logger.error("Failed to read file '%s': %s", file_path, exc)
            return None
