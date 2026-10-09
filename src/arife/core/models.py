"""Data models shared across ARIFE's core, plugins and GUI."""
from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class FileEntry:
    """A single filesystem entry (file or directory) discovered by the scanner."""

    path: Path
    is_dir: bool
    size: int
    modified: datetime
    created: datetime

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def suffix(self) -> str:
        return self.path.suffix.lower()

    @property
    def mime_type(self) -> str | None:
        if self.is_dir:
            return None
        guessed, _ = mimetypes.guess_type(self.path.name)
        return guessed

    @classmethod
    def from_path(cls, path: Path) -> FileEntry:
        stat = path.stat()
        return cls(
            path=path,
            is_dir=path.is_dir(),
            size=0 if path.is_dir() else stat.st_size,
            modified=datetime.fromtimestamp(stat.st_mtime),
            created=datetime.fromtimestamp(stat.st_ctime),
        )


def relative_location(entry: FileEntry, root: Path | None) -> str:
    """Return `entry`'s parent directory relative to `root`.

    Yields "" for a top-level entry (directly inside `root`) or when `root`
    is unknown / not an ancestor of `entry`.
    """
    if root is None:
        return ""
    try:
        rel = entry.path.parent.relative_to(root)
    except ValueError:
        return ""
    return "" if str(rel) == "." else str(rel)


@dataclass
class MetadataResult:
    """Metadata extracted from a single `FileEntry` by one plugin."""

    plugin_id: str
    plugin_display_name: str
    values: dict[str, object] = field(default_factory=dict)
    error: str | None = None
