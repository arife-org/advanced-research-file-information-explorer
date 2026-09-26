"""Qt table model presenting scanned `FileEntry` objects."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

from arife.core.models import FileEntry
from arife.plugins.basic_metadata import human_size

_COLUMNS = ("Name", "Type", "Size", "Modified", "Extension")


class FileTableModel(QAbstractTableModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: list[FileEntry] = []

    def set_entries(self, entries: list[FileEntry]) -> None:
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def entry_at(self, row: int) -> FileEntry | None:
        if 0 <= row < len(self._entries):
            return self._entries[row]
        return None

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
        return None
