"""Main window of the ARIFE desktop application."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDir, QThreadPool
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QFileSystemModel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTableView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from arife import __version__
from arife.core.plugin import PluginManager
from arife.core.scanner import scan_directory
from arife.gui.detail_panel import DetailPanel
from arife.gui.file_table_model import FileTableModel
from arife.gui.plugin_dialog import PluginManagerDialog
from arife.gui.worker import MetadataExtractionWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ARIFE — Advanced Research File Information Explorer")
        self.resize(1200, 750)

        self._plugin_manager = PluginManager()
        self._plugin_manager.discover()
        self._thread_pool = QThreadPool.globalInstance()
        self._current_root = Path.home()

        self._build_ui()
        self._build_menu()
        self._load_directory(self._current_root)

    # -- UI construction ----------------------------------------------------------------
    def _build_ui(self) -> None:
        self._dir_model = QFileSystemModel()
        self._dir_model.setRootPath("")
        self._dir_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)

        self._tree_view = QTreeView()
        self._tree_view.setModel(self._dir_model)
        self._tree_view.setRootIndex(self._dir_model.index(str(Path.home())))
        for col in (1, 2, 3):
            self._tree_view.hideColumn(col)
        self._tree_view.clicked.connect(self._on_tree_clicked)

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Filter files by name…")
        self._search_box.textChanged.connect(self._apply_filter)

        self._table_model = FileTableModel()
        self._table_view = QTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._table_view.doubleClicked.connect(self._on_table_double_clicked)

        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.addWidget(self._search_box)
        middle_layout.addWidget(self._table_view)

        self._detail_panel = DetailPanel()

        splitter = QSplitter()
        splitter.addWidget(self._tree_view)
        splitter.addWidget(middle_widget)
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)

        self.setCentralWidget(splitter)
        self.statusBar().showMessage("Ready")

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        open_action = QAction("&Open Folder…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_folder_dialog)
        file_menu.addAction(open_action)

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        tools_menu = self.menuBar().addMenu("&Tools")
        plugins_action = QAction("&Plugin Manager…", self)
        plugins_action.triggered.connect(self._open_plugin_manager)
        tools_menu.addAction(plugins_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About ARIFE", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # -- Directory / file listing ---------------------------------------------------------
    def _load_directory(self, path: Path) -> None:
        self._current_root = path
        entries = sorted(
            scan_directory(path, recursive=False),
            key=lambda e: (not e.is_dir, e.name.lower()),
        )
        self._all_entries = entries
        self._table_model.set_entries(entries)
        self.statusBar().showMessage(f"{path}  —  {len(entries)} entries")
        self._search_box.clear()

    def _apply_filter(self, text: str) -> None:
        text = text.lower()
        filtered = [e for e in self._all_entries if text in e.name.lower()]
        self._table_model.set_entries(filtered)

    def _open_folder_dialog(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Open Folder", str(self._current_root))
        if directory:
            self._load_directory(Path(directory))

    def _on_tree_clicked(self, index) -> None:
        path = self._dir_model.filePath(index)
        self._load_directory(Path(path))

    def _on_table_double_clicked(self, index) -> None:
        entry = self._table_model.entry_at(index.row())
        if entry and entry.is_dir:
            self._load_directory(entry.path)

    # -- Metadata extraction --------------------------------------------------------------
    def _on_selection_changed(self, *_args) -> None:
        rows = self._table_view.selectionModel().selectedRows()
        if not rows:
            return
        entry = self._table_model.entry_at(rows[0].row())
        if entry is None:
            return

        self._detail_panel.show_loading(entry.name)
        worker = MetadataExtractionWorker(entry, self._plugin_manager)
        worker.signals.finished.connect(self._on_metadata_ready)
        self._thread_pool.start(worker)

    def _on_metadata_ready(self, entry, results) -> None:
        self._detail_panel.show_results(entry.name, results)

    # -- Menu actions -----------------------------------------------------------------------
    def _open_plugin_manager(self) -> None:
        dialog = PluginManagerDialog(self._plugin_manager, self)
        if dialog.exec():
            dialog.apply()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About ARIFE",
            f"<h3>ARIFE {__version__}</h3>"
            "<p>Advanced Research File Information Explorer</p>"
            "<p>A free, open-source, plugin-based file and metadata explorer "
            "for researchers.</p>"
            "<p>Licensed under the MIT License.</p>",
        )
