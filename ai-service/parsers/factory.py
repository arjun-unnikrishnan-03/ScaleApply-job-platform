"""
ResumeParserFactory — selects the correct parser by file extension.

Adding a new format:
    1. Create parsers/txt_parser.py implementing ResumeParser
    2. Call ResumeParserFactory.register(".txt", TxtParser)
    Zero changes to the agent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import ClassVar, Type

from parsers.base import ResumeParser
from core.exceptions import UnsupportedFileTypeError

logger = logging.getLogger(__name__)


class ResumeParserFactory:
    """
    Registry-based factory for file-format parsers.

    Mirrors the same registry pattern as ProviderFactory for consistency.
    """

    _registry: ClassVar[dict[str, Type[ResumeParser]]] = {}

    @classmethod
    def register(cls, extension: str, parser_class: Type[ResumeParser]) -> None:
        """Register a parser for a given file extension."""
        ext = extension.lower().strip()
        if not ext.startswith("."):
            ext = f".{ext}"
        cls._registry[ext] = parser_class
        logger.debug("Parser registered: '%s' → %s", ext, parser_class.__name__)

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return sorted(cls._registry.keys())

    @classmethod
    def get_parser(cls, file_path: Path) -> ResumeParser:
        """
        Return an instantiated parser for the given file.

        Args:
            file_path: Path to the resume file.

        Returns:
            A ResumeParser appropriate for the file extension.

        Raises:
            UnsupportedFileTypeError: If no parser handles this extension.
        """
        ext = file_path.suffix.lower()
        if ext not in cls._registry:
            raise UnsupportedFileTypeError(
                extension=ext,
            )
        parser_class = cls._registry[ext]
        logger.debug(
            "Parser selected: '%s' → %s for file '%s'",
            ext,
            parser_class.__name__,
            file_path.name,
        )
        return parser_class()


# ── Auto-register built-in parsers ────────────────────────────────────────────

def _register_builtin_parsers() -> None:
    try:
        from parsers.pdf_parser import PDFParser
        ResumeParserFactory.register(".pdf", PDFParser)
    except ImportError:
        logger.warning("PDFParser not registered — pypdf not installed.")

    try:
        from parsers.docx_parser import DOCXParser
        ResumeParserFactory.register(".docx", DOCXParser)
    except ImportError:
        logger.warning("DOCXParser not registered — python-docx not installed.")

    # ── Future formats ────────────────────────────────────────────────────
    # from parsers.txt_parser import TxtParser
    # ResumeParserFactory.register(".txt", TxtParser)
    #
    # from parsers.rtf_parser import RtfParser
    # ResumeParserFactory.register(".rtf", RtfParser)


_register_builtin_parsers()
