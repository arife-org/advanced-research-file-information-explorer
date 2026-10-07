"""Dialog for finding duplicate files by content hash within a folder."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from arife.core.scanner import scan_directory
from arife.gui.worker import DuplicateFinderWorker
from arife.plugins.basic_metadata import human_size


class DuplicateFinderDialog(QDialog):
    def __init__(self, root: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Duplicate Files — {root}")
        self.setMinimumSize(560, 420)

        self._worker: DuplicateFinderWorker | None = None
        self._finished = False

        self._status_label = QLabel("Scanning for files…")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Duplicate group", "Path"])
        self._tree.setColumnWidth(0, 260)

        self._close_button = QPushButton("Cancel")
        self._close_button.clicked.connect(self._on_close_clicked)
        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self._close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._status_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._tree)
        layout.addLayout(button_row)

        self._start(root)

    def _start(self, root: Path) -> None:
        entries = list(scan_directory(root, recursive=True))
        self._worker = DuplicateFinderWorker(entries)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        QThreadPool.globalInstance().start(self._worker)

    def _on_progress(self, current: int, total: int) -> None:
        self._status_label.setText(f"Hashing candidate files… {current}/{total}")
        self._progress_bar.setRange(0, max(1, total))
        self._progress_bar.setValue(current)

    def _on_finished(self, duplicates: dict) -> None:
        self._finished = True
        self._tree.clear()
        total_wasted = 0

        if not duplicates:
            self._status_label.setText("No duplicate files found.")
        else:
            groups = sorted(duplicates.items(), key=lambda kv: -len(kv[1]))
            for index, (_digest, paths) in enumerate(groups, start=1):
                try:
                    size = Path(paths[0]).stat().st_size
                except OSError:
                    size = 0
                total_wasted += size * (len(paths) - 1)

                group_item = QTreeWidgetItem(
                    [f"Group {index} — {len(paths)} copies, {human_size(size)} each", ""]
                )
                group_item.setExpanded(True)
                self._tree.addTopLevelItem(group_item)
                for path in paths:
                    group_item.addChild(QTreeWidgetItem(["", str(path)]))

            self._status_label.setText(
                f"Found {len(duplicates)} duplicate group(s) — "
                f"{human_size(total_wasted)} could be reclaimed."
            )

        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(1)
        self._close_button.setText("Close")

    def _on_close_clicked(self) -> None:
        if self._worker is not None and not self._finished:
            self._worker.cancel()
        self.accept()

    def closeEvent(self, event) -> None:
        if self._worker is not None and not self._finished:
            self._worker.cancel()
        super().closeEvent(event)
