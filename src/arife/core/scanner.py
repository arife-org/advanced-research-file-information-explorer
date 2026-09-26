"""Directory scanning for ARIFE."""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from arife.core.models import FileEntry


def scan_directory(root: Path, *, recursive: bool = False, include_hidden: bool = False) -> Iterator[FileEntry]:
    """Yield `FileEntry` objects for the contents of `root`.

    Entries that cannot be stat'd (broken symlinks, permission errors) are
    silently skipped rather than aborting the whole scan.
    """
    root = Path(root)

    with os.scandir(root) as it:
        for dirent in it:
            if not include_hidden and dirent.name.startswith("."):
                continue
            try:
                entry = FileEntry.from_path(Path(dirent.path))
            except OSError:
                continue
            yield entry
            if recursive and entry.is_dir:
                yield from scan_directory(entry.path, recursive=True, include_hidden=include_hidden)


def compute_hash(path: Path, algorithm: str = "sha256", chunk_size: int = 1 << 20) -> str:
    """Compute a hex digest of `path`'s contents using `algorithm`."""
    import hashlib

    hasher = hashlib.new(algorithm)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
