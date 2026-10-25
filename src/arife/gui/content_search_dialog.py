"""Dialog for searching file contents (text files and PDFs) within a folder."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt, QThreadPool
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from arife.core.scanner import scan_directory
from arife.gui.file_actions import open_with_default_app, reveal_in_file_manager, reveal_label
from arife.gui.worker import ContentSearchWorker


class ContentSearchDialog(QDialog):
    def __init__(self, root: Path, *, recursive: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._root = root
        self.setWindowTitle(f"Search File Contents — {root}")
        self.setMinimumSize(560, 420)

        self._worker: ContentSearchWorker | None = None
        self._searching = False

        self._query_box = QLineEdit()
        self._query_box.setPlaceholderText("Search text in files…")
        self._query_box.returnPressed.connect(self._start_search)

        self._recursive_checkbox = QCheckBox("Include subfolders")
        self._recursive_checkbox.setChecked(recursive)

        self._search_button = QPushButton("Search")
        self._search_button.clicked.connect(self._start_search)

        search_row = QHBoxLayout()
        search_row.addWidget(self._query_box, stretch=1)
        search_row.addWidget(self._recursive_checkbox)
        search_row.addWidget(self._search_button)

        self._status_label = QLabel(
            "Searches plain-text files (.txt, .md, .csv, .py, …) and PDFs for a substring."
        )
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(0)

        self._results = QListWidget()
        self._results.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._results.customContextMenuRequested.connect(self._on_results_context_menu)
        self._results.itemDoubleClicked.connect(self._on_result_double_clicked)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(close_button)

        layout = QVBoxLayout(self)
        layout.addLayout(search_row)
        layout.addWidget(self._status_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._results)
        layout.addLayout(button_row)

        self._query_box.setFocus()

    def _start_search(self) -> None:
        query = self._query_box.text().strip()
        if not query or self._searching:
            return

        if self._worker is not None:
            self._worker.cancel()

        self._results.clear()
        self._searching = True
        self._search_button.setEnabled(False)
        self._status_label.setText("Scanning for searchable files…")
        self._progress_bar.setRange(0, 0)

        entries = list(scan_directory(self._root, recursive=self._recursive_checkbox.isChecked()))
        self._worker = ContentSearchWorker(entries, query)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        QThreadPool.globalInstance().start(self._worker)

    def _on_progress(self, current: int, total: int) -> None:
        self._status_label.setText(f"Searching… {current}/{total} files")
        self._progress_bar.setRange(0, max(1, total))
        self._progress_bar.setValue(current)

    def _on_finished(self, matches: list) -> None:
        self._searching = False
        self._search_button.setEnabled(True)
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(1)

        self._results.clear()
        for match in matches:
            item = QListWidgetItem(f"{match.path.name} — {match.snippet}")
            item.setData(Qt.ItemDataRole.UserRole, match.path)
            item.setToolTip(str(match.path))
            self._results.addItem(item)

        noun = "match" if len(matches) == 1 else "matches"
        self._status_label.setText(f"Found {len(matches)} {noun}.")

    def _on_result_double_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path is not None:
            open_with_default_app(path)

    def _on_results_context_menu(self, position: QPoint) -> None:
        item = self._results.itemAt(position)
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if path is None:
            return

        menu = QMenu(self)
        open_action = menu.addAction("Open")
        reveal_action = menu.addAction(reveal_label())

        chosen = menu.exec(self._results.viewport().mapToGlobal(position))
        if chosen is open_action:
            open_with_default_app(path)
        elif chosen is reveal_action:
            reveal_in_file_manager(path)

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._searching:
            self._worker.cancel()
        super().closeEvent(event)
