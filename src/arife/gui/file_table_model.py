"""Qt table model presenting scanned `FileEntry` objects."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from arife.core.models import FileEntry
from arife.plugins.basic_metadata import human_size

_COLUMNS = ("Name", "Type", "Size", "Modified", "Extension", "Location")
LOCATION_COLUMN = _COLUMNS.index("Location")


class FileTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: list[FileEntry] = []
        self._root: Path | None = None

    def set_entries(self, entries: list[FileEntry], root: Path | None = None) -> None:
        self.beginResetModel()
        self._entries = entries
        self._root = root
        self.endResetModel()

    def entry_at(self, row: int) -> FileEntry | None:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

    def _location_of(self, entry: FileEntry) -> str:
        if self._root is None:
            return ""
        try:
            rel = entry.path.parent.relative_to(self._root)
        except ValueError:
            return ""
        return "" if str(rel) == "." else str(rel)

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        key_funcs = {
            0: lambda e: e.name.lower(),
            1: lambda e: e.mime_type or "",
            2: lambda e: e.size,
            3: lambda e: e.modified,
            4: lambda e: e.suffix,
            5: self._location_of,
        }
        key_func = key_funcs.get(column)
        if key_func is None:
            return

        reverse = order == Qt.SortOrder.DescendingOrder
        self.layoutAboutToBeChanged.emit()
        # Directories always stay on top, sorted among themselves; files below them.
        dirs = sorted((e for e in self._entries if e.is_dir), key=key_func, reverse=reverse)
        files = sorted((e for e in self._entries if not e.is_dir), key=key_func, reverse=reverse)
        self._entries = dirs + files
        self.layoutChanged.emit()

    # -- QAbstractTableModel overrides -------------------------------------------------
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._entries)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(_COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None

        entry = self._entries[index.row()]
        column = _COLUMNS[index.column()]

        if column == "Name":
            return entry.name
        if column == "Type":
            return "Folder" if entry.is_dir else (entry.mime_type or "file")
        if column == "Size":
            return "-" if entry.is_dir else human_size(entry.size)
        if column == "Modified":
            return entry.modified.strftime("%Y-%m-%d %H:%M")
        if column == "Extension":
            return entry.suffix or "-"
        if column == "Location":
            return self._location_of(entry) or "."
        return None
