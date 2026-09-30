"""Background workers running slow work off the GUI thread."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal

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
