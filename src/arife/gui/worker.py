"""Background worker running plugin extraction off the GUI thread."""
from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, Signal

from arife.core.models import FileEntry, MetadataResult
from arife.core.plugin import PluginManager


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
