"""
TextProcessor — utility for normalizing and pre-processing raw resume text.

Kept separate from parsers (which handle file I/O) and the agent
(which handles orchestration) following Single Responsibility Principle.

Future use: chunk long documents for RAG, detect language, clean OCR noise.
"""

from __future__ import annotations

import re
import unicodedata


class TextProcessor:
    """Stateless text normalization utilities for resume content."""

    # Characters frequently garbled in PDF extraction
    _LIGATURE_MAP = str.maketrans({
        "\ufb01": "fi",  # ﬁ
        "\ufb02": "fl",  # ﬂ
        "\u2013": "-",   # en dash
        "\u2014": "-",   # em dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2022": "-",   # bullet point
        "\u00a0": " ",   # non-breaking space
    })

    @classmethod
    def normalize(cls, text: str) -> str:
        """
        Full normalization pipeline:
        1. NFKC unicode normalization
        2. Ligature replacement
        3. Whitespace normalization
        4. Trailing space cleanup
        """
        if not text:
            return ""

        text = unicodedata.normalize("NFKC", text)
        text = text.translate(cls._LIGATURE_MAP)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = "\n".join(line.rstrip() for line in text.splitlines())
        return text.strip()

    @classmethod
    def truncate(cls, text: str, max_chars: int = 12_000) -> str:
        """Truncate text to max_chars, appending a marker."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n[DOCUMENT TRUNCATED — remaining content omitted]"

    @classmethod
    def word_count(cls, text: str) -> int:
        return len(text.split())

    @classmethod
    def estimate_pages(cls, text: str, words_per_page: int = 350) -> int:
        """Rough page count estimate for documents without page metadata."""
        return max(1, cls.word_count(text) // words_per_page)
