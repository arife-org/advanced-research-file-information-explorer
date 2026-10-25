from pathlib import Path

from arife.core.content_search import search_file_contents
from arife.core.models import FileEntry


def _entries(paths: list[Path]) -> list[FileEntry]:
    return [FileEntry.from_path(p) for p in paths]


def test_finds_substring_case_insensitively(tmp_path: Path) -> None:
    hit = tmp_path / "notes.txt"
    hit.write_text("This paper discusses Quantum Computing in depth.")
    miss = tmp_path / "other.txt"
    miss.write_text("Nothing relevant here.")

    matches = search_file_contents(_entries([hit, miss]), "quantum computing")

    assert len(matches) == 1
    assert matches[0].path == hit
    assert "Quantum Computing" in matches[0].snippet


def test_empty_query_returns_no_matches(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("anything")

    assert search_file_contents(_entries([target]), "") == []
    assert search_file_contents(_entries([target]), "   ") == []


def test_ignores_unsupported_file_types(tmp_path: Path) -> None:
    target = tmp_path / "image.png"
    target.write_bytes(b"not actually an image but has query text in it")

    matches = search_file_contents(_entries([target]), "query")

    assert matches == []


def test_ignores_directories(tmp_path: Path) -> None:
    sub = tmp_path / "query-named-folder"
    sub.mkdir()

    entries = [FileEntry.from_path(sub)]
    assert search_file_contents(entries, "query") == []


def test_progress_callback_reports_candidate_count(tmp_path: Path) -> None:
    paths = []
    for i in range(3):
        p = tmp_path / f"f{i}.txt"
        p.write_text("needle in here")
        paths.append(p)

    calls = []
    search_file_contents(_entries(paths), "needle", progress_callback=lambda i, t: calls.append((i, t)))

    assert calls == [(1, 3), (2, 3), (3, 3)]


def test_cancellation_stops_early(tmp_path: Path) -> None:
    paths = []
    for i in range(4):
        p = tmp_path / f"f{i}.txt"
        p.write_text("needle in here")
        paths.append(p)

    calls = []
    search_file_contents(
        _entries(paths),
        "needle",
        progress_callback=lambda i, t: calls.append((i, t)),
        should_cancel=lambda: len(calls) >= 2,
    )

    assert len(calls) == 2


def test_malformed_pdf_is_skipped_without_crashing(tmp_path: Path) -> None:
    fake_pdf = tmp_path / "broken.pdf"
    fake_pdf.write_bytes(b"not actually a pdf file")

    matches = search_file_contents(_entries([fake_pdf]), "anything")

    assert matches == []


def test_snippet_includes_ellipsis_when_truncated(tmp_path: Path) -> None:
    target = tmp_path / "long.txt"
    target.write_text("padding " * 20 + "findme" + " more padding" * 20)

    matches = search_file_contents(_entries([target]), "findme")

    assert len(matches) == 1
    assert matches[0].snippet.startswith("…")
    assert matches[0].snippet.endswith("…")
    assert "findme" in matches[0].snippet
