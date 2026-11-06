"""Background workers running slow work off the GUI thread."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QSize, Signal
from PySide6.QtGui import QImage, QImageReader

from arife.core.content_search import SearchMatch, search_file_contents
from arife.core.duplicates import find_duplicate_files
from arife.core.models import FileEntry, MetadataResult
from arife.core.plugin import PluginManager
from arife.core.scanner import compute_hash, scan_directory


class _WorkerSignals(QObject):
    finished = Signal(object, list)  # FileEntry, list[MetadataResult]


class MetadataExtractionWorker(QRunnable):
    """Runs all enabled plugins for one `FileEntry` on a background thread."""

    def __init__(self, entry: FileEntry, plugin_manager: PluginManager) -> None:
        super().__init__()
        self._entry = entry
        self._plugin_manager = plugin_manager
        self.signals = _WorkerSignals()

    def run(self) -> None:
        results: list[MetadataResult] = self._plugin_manager.extract_all(self._entry)
        self.signals.finished.emit(self._entry, results)


class _HashWorkerSignals(QObject):
    finished = Signal(object, str)  # FileEntry, hex digest
    failed = Signal(object, str)  # FileEntry, error message


class HashWorker(QRunnable):
    """Computes a SHA-256 hash for one `FileEntry` on a background thread."""

    def __init__(self, entry: FileEntry, algorithm: str = "sha256") -> None:
        super().__init__()
        self._entry = entry
        self._algorithm = algorithm
        self.signals = _HashWorkerSignals()

    def run(self) -> None:
        try:
            digest = compute_hash(self._entry.path, self._algorithm)
        except OSError as exc:
            self.signals.failed.emit(self._entry, str(exc))
            return
        self.signals.finished.emit(self._entry, digest)


class _DirectoryScanSignals(QObject):
    finished = Signal(int, object, list)  # generation, root (Path), list[FileEntry]


class DirectoryScanWorker(QRunnable):
    """Scans a directory (optionally recursively) on a background thread.

    `generation` is an opaque token the caller uses to discard results from
    a stale scan superseded by a newer navigation/filter action.
    """

    def __init__(self, root: Path, *, recursive: bool, generation: int) -> None:
        super().__init__()
        self._root = root
        self._recursive = recursive
        self._generation = generation
        self.signals = _DirectoryScanSignals()

    def run(self) -> None:
        entries = sorted(
            scan_directory(self._root, recursive=self._recursive),
            key=lambda e: (not e.is_dir, e.name.lower()),
        )
        self.signals.finished.emit(self._generation, self._root, entries)


class _DuplicateFinderSignals(QObject):
    progress = Signal(int, int)  # current, total candidates hashed
    finished = Signal(dict)  # hash -> list[Path]


class DuplicateFinderWorker(QRunnable):
    """Finds duplicate files among `entries` by content hash on a background thread."""

    def __init__(self, entries: list[FileEntry]) -> None:
        super().__init__()
        self._entries = entries
        self._cancelled = False
        self.signals = _DuplicateFinderSignals()

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        result = find_duplicate_files(
            self._entries,
            progress_callback=lambda current, total: self.signals.progress.emit(current, total),
            should_cancel=lambda: self._cancelled,
        )
        self.signals.finished.emit(result)


def is_supported_image(suffix: str) -> bool:
    """Return whether `suffix` (e.g. ".png") is a format Qt can decode."""
    formats = {fmt.data().decode().lower() for fmt in QImageReader.supportedImageFormats()}
    return suffix.lstrip(".").lower() in formats


def load_thumbnail(path: Path, max_size: int) -> QImage | None:
    """Read `path` as an image, downscaled so neither side exceeds `max_size`.

    Uses `QImageReader.setScaledSize` so oversized research images (e.g. a
    multi-megapixel scan) are never fully decoded at full resolution just to
    be shrunk afterward. Returns None if the file isn't a readable image.
    """
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and max(size.width(), size.height()) > max_size:
        scale = max_size / max(size.width(), size.height())
        reader.setScaledSize(
            QSize(max(1, round(size.width() * scale)), max(1, round(size.height() * scale)))
        )
    image = reader.read()
    return None if image.isNull() else image


class _ThumbnailSignals(QObject):
    finished = Signal(object, object)  # FileEntry, QImage or None


class ThumbnailWorker(QRunnable):
    """Loads a scaled-down image preview for one `FileEntry` on a background thread."""

    def __init__(self, entry: FileEntry, max_size: int = 220) -> None:
        super().__init__()
        self._entry = entry
        self._max_size = max_size
        self.signals = _ThumbnailSignals()

    def run(self) -> None:
        image = load_thumbnail(self._entry.path, self._max_size)
        self.signals.finished.emit(self._entry, image)


class _ContentSearchSignals(QObject):
    progress = Signal(int, int)  # current, total candidate files searched
    finished = Signal(list)  # list[SearchMatch]


class ContentSearchWorker(QRunnable):
    """Searches `entries` for `query` by file content on a background thread."""

    def __init__(self, entries: list[FileEntry], query: str) -> None:
        super().__init__()
        self._entries = entries
        self._query = query
        self._cancelled = False
        self.signals = _ContentSearchSignals()

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        matches: list[SearchMatch] = search_file_contents(
            self._entries,
            self._query,
            progress_callback=lambda current, total: self.signals.progress.emit(current, total),
            should_cancel=lambda: self._cancelled,
        )
        self.signals.finished.emit(matches)
