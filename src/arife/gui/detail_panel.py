"""Widget rendering extracted metadata for the currently selected file."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from arife.core.models import MetadataResult


class DetailPanel(QWidget):
    hash_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._title = QLabel("Select a file to see details")
        self._title.setStyleSheet("font-weight: bold; padding: 4px;")

        self._hash_button = QPushButton("Compute SHA-256 Hash")
        self._hash_button.setEnabled(False)
        self._hash_button.clicked.connect(self.hash_requested.emit)

        self._hash_label = QLabel("")
        self._hash_label.setStyleSheet("color: gray;")
        self._hash_label.setWordWrap(True)
        self._hash_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        hash_row = QHBoxLayout()
        hash_row.addWidget(self._hash_button)
        hash_row.addWidget(self._hash_label, stretch=1)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Field", "Value"])
        self._tree.setColumnWidth(0, 180)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addLayout(hash_row)
        layout.addWidget(self._tree)

    def show_loading(self, name: str, *, is_dir: bool) -> None:
        self._title.setText(f"{name} — analyzing…")
        self._tree.clear()
        self._hash_label.setText("")
        self._hash_button.setEnabled(not is_dir)

    def show_results(self, name: str, results: list[MetadataResult]) -> None:
        self._title.setText(name)
        self._tree.clear()

        for result in results:
            group = QTreeWidgetItem([result.plugin_display_name, ""])
            group.setExpanded(True)
            self._tree.addTopLevelItem(group)

            if result.error:
                group.addChild(QTreeWidgetItem(["Error", result.error]))
                continue

            for key, value in result.values.items():
                group.addChild(QTreeWidgetItem([str(key), str(value)]))

        if not results:
            self._tree.addTopLevelItem(QTreeWidgetItem(["No plugin applies to this file", ""]))

    def show_hash_pending(self) -> None:
        self._hash_button.setEnabled(False)
        self._hash_label.setText("Computing…")

    def show_hash_result(self, digest: str) -> None:
        self._hash_button.setEnabled(True)
        self._hash_label.setText(digest)

    def show_hash_error(self, message: str) -> None:
        self._hash_button.setEnabled(True)
        self._hash_label.setText(f"Error: {message}")
