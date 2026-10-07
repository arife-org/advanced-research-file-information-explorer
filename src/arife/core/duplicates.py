"""Duplicate file detection based on content hashing."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path

from arife.core.models import FileEntry
from arife.core.scanner import compute_hash


def find_duplicate_files(
    entries: Iterable[FileEntry],
    *,
    progress_callback: Callable[[int, int], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, list[Path]]:
    """Group file entries by content hash, keeping only groups with 2+ files.

    Entries are first grouped by size - a free pre-filter, since a file
    with a size no other file shares cannot have a duplicate. Only files
    that share a size with at least one other file are actually hashed.
    """
    by_size: dict[int, list[FileEntry]] = defaultdict(list)
    for entry in entries:
        if not entry.is_dir:
            by_size[entry.size].append(entry)

    candidates = [entry for group in by_size.values() if len(group) > 1 for entry in group]
    total = len(candidates)

    by_hash: dict[str, list[Path]] = defaultdict(list)
    for index, entry in enumerate(candidates, start=1):
        if should_cancel and should_cancel():
            break
        try:
            digest = compute_hash(entry.path)
        except OSError:
            continue
        by_hash[digest].append(entry.path)
        if progress_callback:
            progress_callback(index, total)

    return {digest: paths for digest, paths in by_hash.items() if len(paths) > 1}
