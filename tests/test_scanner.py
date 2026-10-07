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


def test_scan_directory_recursive_skips_unreadable_subdirectory(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    (blocked / "secret.txt").write_text("nope")
    readable = tmp_path / "readable"
    readable.mkdir()
    (readable / "visible.txt").write_text("ok")

    blocked.chmod(0o000)
    try:
        entries = list(scan_directory(tmp_path, recursive=True))
    finally:
        blocked.chmod(0o755)  # restore so pytest can clean up tmp_path

    names = {e.name for e in entries}
    assert "blocked" in names  # the directory entry itself is still listed
    assert "secret.txt" not in names  # but scanning its contents is skipped, not fatal
    assert "readable" in names
    assert "visible.txt" in names


def test_compute_hash_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    file_a = tmp_path / "a.bin"
    file_b = tmp_path / "b.bin"
    file_a.write_bytes(b"some content")
    file_b.write_bytes(b"different content")

    assert compute_hash(file_a) == compute_hash(file_a)
    assert compute_hash(file_a) != compute_hash(file_b)
