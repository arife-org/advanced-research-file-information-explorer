from pathlib import Path

from arife.core import duplicates as duplicates_module
from arife.core.duplicates import find_duplicate_files
from arife.core.models import FileEntry


def _entries(paths: list[Path]) -> list[FileEntry]:
    return [FileEntry.from_path(p) for p in paths]


def test_finds_identical_content_across_different_names(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("same content")
    b.write_text("same content")

    result = find_duplicate_files(_entries([a, b]))

    assert len(result) == 1
    group = next(iter(result.values()))
    assert set(group) == {a, b}


def test_different_content_with_same_size_is_not_a_duplicate(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("aaaaa")
    b.write_text("bbbbb")

    assert find_duplicate_files(_entries([a, b])) == {}


def test_unique_sized_files_are_never_hashed(tmp_path: Path, monkeypatch) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("short")
    b.write_text("a much longer piece of content than the other file")

    hashed_paths: list[Path] = []
    original_compute_hash = duplicates_module.compute_hash
    monkeypatch.setattr(
        duplicates_module,
        "compute_hash",
        lambda path, *a, **kw: hashed_paths.append(path) or original_compute_hash(path, *a, **kw),
    )

    result = find_duplicate_files(_entries([a, b]))

    assert result == {}
    assert hashed_paths == []


def test_progress_callback_reports_candidate_count(tmp_path: Path) -> None:
    paths = []
    for i in range(3):
        p = tmp_path / f"f{i}.txt"
        p.write_text("identical content")
        paths.append(p)

    calls = []
    find_duplicate_files(_entries(paths), progress_callback=lambda i, t: calls.append((i, t)))

    assert calls == [(1, 3), (2, 3), (3, 3)]


def test_cancellation_stops_early(tmp_path: Path) -> None:
    paths = []
    for i in range(4):
        p = tmp_path / f"f{i}.txt"
        p.write_text("identical content")
        paths.append(p)

    calls = []
    find_duplicate_files(
        _entries(paths),
        progress_callback=lambda i, t: calls.append((i, t)),
        should_cancel=lambda: len(calls) >= 2,
    )

    assert len(calls) == 2
