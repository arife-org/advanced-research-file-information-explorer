"""Plugin extracting research-paper metadata from PDF files.

Extracts standard PDF document info (title, author, creation date) plus a
best-effort DOI extracted from the text of the first pages via a regular
expression, which is enough to identify most academic papers without
needing network access.
"""
from __future__ import annotations

import re

from arife.core.models import FileEntry
from arife.core.plugin import InfoPlugin

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+\b")


class PdfResearchPlugin(InfoPlugin):
    id = "pdf_research"
    display_name = "Research Paper (PDF)"
    description = "Extracts title, author, DOI and page count from PDF research papers."

    def is_available(self) -> bool:
        try:
            import pypdf  # noqa: F401
        except ImportError:
            return False
        return True

    def supports(self, entry: FileEntry) -> bool:
        return not entry.is_dir and entry.suffix == ".pdf"

    def extract(self, entry: FileEntry) -> dict[str, object]:
        from pypdf import PdfReader

        reader = PdfReader(str(entry.path))
        info = reader.metadata or {}
        values: dict[str, object] = {
            "Title": (info.title or "").strip() or "-",
            "Author": (info.author or "").strip() or "-",
            "Subject": (info.subject or "").strip() or "-",
            "Creator": (info.creator or "").strip() or "-",
            "Page count": len(reader.pages),
        }

        doi = self._find_doi(reader)
        values["DOI"] = doi or "not found"
        return values

    @staticmethod
    def _find_doi(reader) -> str | None:
        for page in reader.pages[:3]:
            try:
                text = page.extract_text() or ""
            except Exception:  # noqa: BLE001, S112 - a single malformed page shouldn't abort DOI lookup
                continue
            match = DOI_PATTERN.search(text)
            if match:
                return match.group(0).rstrip(".,;)")
        return None
