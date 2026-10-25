"""Full-text search across file contents (plain text files and PDFs)."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from arife.core.models import FileEntry

TEXT_SUFFIXES = {
    ".txt", ".md", ".rst", ".csv", ".tsv", ".json", ".jsonl",
    ".py", ".yaml", ".yml", ".log", ".ini", ".cfg", ".xml", ".html",
}
_MAX_TEXT_BYTES = 5 * 1024 * 1024  # skip absurdly large text files
_SNIPPET_CONTEXT = 40


@dataclass
class SearchMatch:
    path: Path
    snippet: str


def _read_text_file(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_TEXT_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _read_pdf_text(path: Path) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None

    try:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:  # noqa: BLE001 - a single malformed PDF shouldn't abort the whole search
        return None


def _is_searchable(entry: FileEntry) -> bool:
    return not entry.is_dir and (entry.suffix in TEXT_SUFFIXES or entry.suffix == ".pdf")


def _build_snippet(text: str, query: str) -> str:
    idx = text.lower().find(query.lower())
    if idx == -1:
        return ""
    start = max(0, idx - _SNIPPET_CONTEXT)
    end = min(len(text), idx + len(query) + _SNIPPET_CONTEXT)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def search_file_contents(
    entries: Iterable[FileEntry],
    query: str,
    *,
    progress_callback: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> list[SearchMatch]:
    """Search `entries` for `query` (case-insensitive substring) and return matches."""
    query = query.strip()
    if not query:
        return []

    candidates = [entry for entry in entries if _is_searchable(entry)]
    total = len(candidates)
    matches: list[SearchMatch] = []

    for index, entry in enumerate(candidates, start=1):
        if should_cancel and should_cancel():
            break

        text = _read_pdf_text(entry.path) if entry.suffix == ".pdf" else _read_text_file(entry.path)
        if text and query.lower() in text.lower():
            matches.append(SearchMatch(entry.path, _build_snippet(text, query)))

        if progress_callback:
            progress_callback(index, total)

    return matches
