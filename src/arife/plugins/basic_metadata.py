"""Built-in plugin exposing basic filesystem metadata for every entry."""
from __future__ import annotations

from arife.core.models import FileEntry
from arife.core.plugin import InfoPlugin


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


class BasicMetadataPlugin(InfoPlugin):
    id = "basic_metadata"
    display_name = "Basic Metadata"
    description = "Filesystem metadata available for any file or directory: size, timestamps, MIME type."

    def supports(self, entry: FileEntry) -> bool:
        return True

    def extract(self, entry: FileEntry) -> dict[str, object]:
        return {
            "Name": entry.name,
            "Path": str(entry.path),
            "Type": "Directory" if entry.is_dir else "File",
            "Size": human_size(entry.size) if not entry.is_dir else "-",
            "Size (bytes)": entry.size if not entry.is_dir else 0,
            "MIME type": entry.mime_type or "unknown",
            "Extension": entry.suffix or "-",
            "Modified": entry.modified.isoformat(sep=" ", timespec="seconds"),
            "Created": entry.created.isoformat(sep=" ", timespec="seconds"),
        }
