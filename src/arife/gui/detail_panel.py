"""Widget rendering extracted metadata for the currently selected file."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from arife.core.models import MetadataResult


class DetailPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._title = QLabel("Select a file to see details")
        self._title.setStyleSheet("font-weight: bold; padding: 4px;")

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Field", "Value"])
        self._tree.setColumnWidth(0, 180)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._tree)

    def show_loading(self, name: str) -> None:
        self._title.setText(f"{name} — analyzing…")
        self._tree.clear()

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
