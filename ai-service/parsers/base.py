"""
ResumeParser ABC and ParsedDocument data model.

Each file format gets its own parser class.
The agent interacts only with this interface and ParsedDocument.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ParsedDocument:
    """
    The output of any resume parser.

    `raw_text` is the extracted plain text passed to the LLM.
    `page_count` and `word_count` are used for quality gating
    (e.g., reject single-word or corrupt files early).
    """

    raw_text: str
    source_path: str
    file_format: str          # 'pdf', 'docx', 'txt', etc.
    page_count: int = 0
    word_count: int = field(init=False)
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        # dataclass frozen=True requires object.__setattr__ for computed fields
        object.__setattr__(self, "word_count", len(self.raw_text.split()))
        object.__setattr__(self, "char_count", len(self.raw_text))

    def is_usable(self, min_words: int = 30) -> bool:
        """Returns True if the document contains enough text to process."""
        return self.word_count >= min_words


class ResumeParser(ABC):
    """
    Abstract base class for all resume file parsers.

    Implementations must be stateless — all state lives in ParsedDocument.
    """

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a resume file and return extracted text.

        Args:
            file_path: Absolute or relative path to the resume file.

        Returns:
            ParsedDocument with raw_text and metadata.

        Raises:
            ParseError: If the file cannot be read or decoded.
            EmptyDocumentError: If the file produces no usable text.
        """

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return the file extensions this parser handles (e.g. ['.pdf'])."""

    def validate_path(self, file_path: Path) -> None:
        """
        Common pre-parse validation used by all parsers.
        Raises ParseError if the file doesn't exist or is empty.
        """
        from core.exceptions import ParseError

        if not file_path.exists():
            raise ParseError(
                message=f"File not found: {file_path}",
                details={"path": str(file_path)},
            )
        if file_path.stat().st_size == 0:
            raise ParseError(
                message=f"File is empty: {file_path}",
                details={"path": str(file_path)},
            )
