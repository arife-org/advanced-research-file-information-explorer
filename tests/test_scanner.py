from pathlib import Path

from arife.core.scanner import compute_hash, scan_directory


def test_scan_directory_lists_files_and_dirs(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("world")

    entries = list(scan_directory(tmp_path, recursive=False))
    names = {e.name for e in entries}

    assert names == {"a.txt", "sub"}


def test_scan_directory_recursive(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.txt").write_text("world")

    entries = list(scan_directory(tmp_path, recursive=True))
    names = {e.name for e in entries}

    assert names == {"a.txt", "sub", "b.txt"}


def test_scan_directory_skips_hidden_by_default(tmp_path: Path) -> None:
    (tmp_path / ".hidden").write_text("secret")
    (tmp_path / "visible.txt").write_text("data")

    entries = list(scan_directory(tmp_path))
    names = {e.name for e in entries}

    assert names == {"visible.txt"}


def test_compute_hash_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    file_a = tmp_path / "a.bin"
    file_b = tmp_path / "b.bin"
    file_a.write_bytes(b"some content")
    file_b.write_bytes(b"different content")

    assert compute_hash(file_a) == compute_hash(file_a)
    assert compute_hash(file_a) != compute_hash(file_b)
