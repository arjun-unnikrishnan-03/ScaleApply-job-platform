"""
PDFParser — extracts text from PDF resume files.

Uses pypdf (the maintained successor to PyPDF2) for reliable
cross-platform PDF text extraction with encoding normalization.
"""

from __future__ import annotations

import logging
import unicodedata
from pathlib import Path

from parsers.base import ParsedDocument, ResumeParser
from core.exceptions import EmptyDocumentError, ParseError

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
    _PYPDF_AVAILABLE = True
except ImportError:
    _PYPDF_AVAILABLE = False


class PDFParser(ResumeParser):
    """
    Parser for PDF resume files.

    Text is extracted page-by-page, normalized (unicode, whitespace),
    and concatenated into a single string for the LLM.
    """

    def __init__(self, max_pages: int = 10) -> None:
        """
        Args:
            max_pages: Maximum pages to extract (prevents runaway on large docs).
        """
        if not _PYPDF_AVAILABLE:
            raise ParseError(
                "pypdf is not installed. Run: pip install pypdf"
            )
        self._max_pages = max_pages

    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Extract text from each PDF page and return a ParsedDocument.

        Handles:
        - Encrypted PDFs (raises ParseError with clear message)
        - PDFs with no extractable text (scanned images → EmptyDocumentError)
        - Encoding issues via unicode normalization
        """
        self.validate_path(file_path)

        try:
            reader = PdfReader(str(file_path))
        except Exception as exc:
            raise ParseError(
                message=f"Failed to open PDF: {file_path.name}",
                details={"error": str(exc), "path": str(file_path)},
            ) from exc

        if reader.is_encrypted:
            raise ParseError(
                message=f"PDF is encrypted and cannot be parsed: {file_path.name}",
                details={"path": str(file_path)},
            )

        pages = reader.pages[: self._max_pages]
        page_texts: list[str] = []

        for i, page in enumerate(pages):
            try:
                text = page.extract_text() or ""
                text = self._normalize(text)
                if text:
                    page_texts.append(text)
            except Exception as exc:
                logger.warning(
                    "Could not extract text from page %d of '%s': %s",
                    i + 1,
                    file_path.name,
                    exc,
                )

        raw_text = "\n\n".join(page_texts).strip()

        if not raw_text:
            raise EmptyDocumentError(str(file_path))

        logger.debug(
            "PDF parsed: '%s' | pages=%d | chars=%d",
            file_path.name,
            len(pages),
            len(raw_text),
        )

        return ParsedDocument(
            raw_text=raw_text,
            source_path=str(file_path),
            file_format="pdf",
            page_count=len(reader.pages),
        )

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalize extracted text:
        - NFKC unicode normalization (handles ligatures like 'ﬁ' → 'fi')
        - Collapse multiple blank lines
        - Strip trailing whitespace per line
        """
        text = unicodedata.normalize("NFKC", text)
        lines = [line.rstrip() for line in text.splitlines()]
        # Collapse 3+ blank lines into 2
        normalized_lines: list[str] = []
        blank_count = 0
        for line in lines:
            if line == "":
                blank_count += 1
                if blank_count <= 2:
                    normalized_lines.append(line)
            else:
                blank_count = 0
                normalized_lines.append(line)
        return "\n".join(normalized_lines)
