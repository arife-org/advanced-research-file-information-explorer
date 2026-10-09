"""Exporting scanned file listings to CSV or JSON for research record-keeping."""
from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path

from arife.core.models import FileEntry, relative_location

FIELDS = ("name", "path", "type", "size_bytes", "modified", "extension", "location")


def _row_for(entry: FileEntry, root: Path | None) -> dict[str, object]:
    return {
        "name": entry.name,
        "path": str(entry.path),
        "type": "directory" if entry.is_dir else "file",
        "size_bytes": entry.size,
        "modified": entry.modified.isoformat(sep=" ", timespec="seconds"),
        "extension": entry.suffix,
        "location": relative_location(entry, root),
    }


def export_entries_to_csv(entries: Iterable[FileEntry], root: Path | None, destination: Path) -> None:
    rows = [_row_for(entry, root) for entry in entries]
    with open(destination, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def export_entries_to_json(entries: Iterable[FileEntry], root: Path | None, destination: Path) -> None:
    rows = [_row_for(entry, root) for entry in entries]
    with open(destination, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
