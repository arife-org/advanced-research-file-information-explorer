"""Main window of the ARIFE desktop application."""
from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import QDir, QPoint, Qt, QThreadPool
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from arife import __version__
from arife.core.export import export_entries_to_csv, export_entries_to_json
from arife.core.file_ops import copy_entry, create_folder, move_entry, rename_entry
from arife.core.plugin import PluginManager
from arife.gui.content_search_dialog import ContentSearchDialog
from arife.gui.detail_panel import DetailPanel
from arife.gui.duplicate_finder_dialog import DuplicateFinderDialog
from arife.gui.file_actions import (
    move_to_trash,
    open_with_default_app,
    reveal_in_file_manager,
    reveal_label,
    trash_available,
)
from arife.gui.file_table_model import LOCATION_COLUMN, FileTableModel
from arife.gui.file_table_view import FileTableView
from arife.gui.plugin_dialog import PluginManagerDialog
from arife.gui.settings import AppSettings
from arife.gui.worker import (
    DirectoryScanWorker,
    HashWorker,
    MetadataExtractionWorker,
    ThumbnailWorker,
    is_supported_image,
)

APP_TAGLINE = "Advanced Research Information File Explorer"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"ARIFE — {APP_TAGLINE}")
        self.resize(1200, 750)

        self._app_settings = AppSettings()
        self._plugin_manager = PluginManager()
        self._plugin_manager.discover()
        for plugin_id in self._app_settings.disabled_plugin_ids():
            self._plugin_manager.set_enabled(plugin_id, False)
        self._thread_pool = QThreadPool.globalInstance()
        self._current_root = self._app_settings.last_folder(Path.home())
        self._selected_entry = None
        self._all_entries: list = []
        self._scan_generation = 0
        self._clipboard_paths: list[Path] = []
        self._clipboard_cut = False
        self._history_back: list[Path] = []
        self._history_forward: list[Path] = []

        self._build_ui()
        self._build_menu()
        self._load_directory(self._current_root)

        geometry = self._app_settings.window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

    def closeEvent(self, event) -> None:
        self._app_settings.set_window_geometry(self.saveGeometry())
        super().closeEvent(event)

    # -- UI construction ----------------------------------------------------------------
    def _build_ui(self) -> None:
        self._tree_view = self._build_tree_view()
        self._search_box, self._recursive_checkbox, search_row = self._build_search_row()
        self._table_model, self._table_view = self._build_table_view()

        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.addLayout(search_row)
        middle_layout.addWidget(self._table_view)

        self._detail_panel = DetailPanel()
        self._detail_panel.hash_requested.connect(self._on_hash_requested)

        splitter = QSplitter()
        splitter.addWidget(self._tree_view)
        splitter.addWidget(middle_widget)
        splitter.addWidget(self._detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)

        self.setCentralWidget(splitter)
        self.statusBar().showMessage("Ready")

    def _build_tree_view(self) -> QTreeView:
        self._dir_model = QFileSystemModel()
        self._dir_model.setRootPath("")
        self._dir_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)

        tree_view = QTreeView()
        tree_view.setModel(self._dir_model)
        tree_view.setRootIndex(self._dir_model.index(str(Path.home())))
        for col in (1, 2, 3):
            tree_view.hideColumn(col)
        tree_view.clicked.connect(self._on_tree_clicked)
        return tree_view

    def _build_search_row(self) -> tuple[QLineEdit, QCheckBox, QHBoxLayout]:
        search_box = QLineEdit()
        search_box.setPlaceholderText("Filter files by name…")
        search_box.textChanged.connect(self._apply_filter)

        recursive_checkbox = QCheckBox("Include subfolders")
        recursive_checkbox.setChecked(self._app_settings.recursive_scan())
        recursive_checkbox.toggled.connect(self._on_recursive_toggled)

        row = QHBoxLayout()
        row.addWidget(search_box, stretch=1)
        row.addWidget(recursive_checkbox)
        return search_box, recursive_checkbox, row

    def _build_table_view(self) -> tuple[FileTableModel, FileTableView]:
        model = FileTableModel()
        view = FileTableView()
        view.setModel(model)
        view.setSelectionBehavior(FileTableView.SelectionBehavior.SelectRows)
        view.setSelectionMode(FileTableView.SelectionMode.ExtendedSelection)
        view.setEditTriggers(FileTableView.EditTrigger.NoEditTriggers)
        view.horizontalHeader().setStretchLastSection(True)
        view.setSortingEnabled(True)
        view.setColumnHidden(LOCATION_COLUMN, not self._recursive_checkbox.isChecked())
        view.selectionModel().selectionChanged.connect(self._on_selection_changed)
        view.doubleClicked.connect(self._on_table_double_clicked)
        view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        view.customContextMenuRequested.connect(self._on_table_context_menu)
        view.open_requested.connect(self._on_open_requested)
        view.delete_requested.connect(self._on_delete_requested)
        view.rename_requested.connect(self._on_rename_requested)
        return model, view

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        open_action = QAction("&Open Folder…", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_folder_dialog)
        file_menu.addAction(open_action)

        go_up_action = QAction("Go &Up", self)
        go_up_action.setShortcut("Alt+Up")
        go_up_action.triggered.connect(self._go_up)
        file_menu.addAction(go_up_action)

        self._back_action = QAction("&Back", self)
        self._back_action.setShortcut("Alt+Left")
        self._back_action.setEnabled(False)
        self._back_action.triggered.connect(self._go_back)
        file_menu.addAction(self._back_action)

        self._forward_action = QAction("&Forward", self)
        self._forward_action.setShortcut("Alt+Right")
        self._forward_action.setEnabled(False)
        self._forward_action.triggered.connect(self._go_forward)
        file_menu.addAction(self._forward_action)

        new_folder_action = QAction("&New Folder…", self)
        new_folder_action.setShortcut("Ctrl+Shift+N")
        new_folder_action.triggered.connect(self._new_folder)
        file_menu.addAction(new_folder_action)

        export_action = QAction("&Export File List…", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_file_list)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = self.menuBar().addMenu("&Edit")

        copy_entry_action = QAction("&Copy", self)
        copy_entry_action.setShortcut("Ctrl+C")
        copy_entry_action.triggered.connect(self._copy_selection)
        edit_menu.addAction(copy_entry_action)

        cut_entry_action = QAction("Cu&t", self)
        cut_entry_action.setShortcut("Ctrl+X")
        cut_entry_action.triggered.connect(self._cut_selection)
        edit_menu.addAction(cut_entry_action)

        self._paste_action = QAction("&Paste", self)
        self._paste_action.setShortcut("Ctrl+V")
        self._paste_action.setEnabled(False)
        self._paste_action.triggered.connect(self._paste_clipboard)
        edit_menu.addAction(self._paste_action)

        tools_menu = self.menuBar().addMenu("&Tools")
        plugins_action = QAction("&Plugin Manager…", self)
        plugins_action.triggered.connect(self._open_plugin_manager)
        tools_menu.addAction(plugins_action)

        duplicates_action = QAction("Find &Duplicate Files…", self)
        duplicates_action.triggered.connect(self._open_duplicate_finder)
        tools_menu.addAction(duplicates_action)

        search_action = QAction("&Search File Contents…", self)
        search_action.setShortcut("Ctrl+Shift+F")
        search_action.triggered.connect(self._open_content_search)
        tools_menu.addAction(search_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About ARIFE", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # -- Directory / file listing ---------------------------------------------------------
    def _load_directory(self, path: Path) -> None:
        self._current_root = path
        self._search_box.clear()
        self._app_settings.set_last_folder(path)

        self._scan_generation += 1
        generation = self._scan_generation
        recursive = self._recursive_checkbox.isChecked()

        self.statusBar().showMessage(f"Scanning {path}…")
        worker = DirectoryScanWorker(path, recursive=recursive, generation=generation)
        worker.signals.finished.connect(self._on_scan_finished)
        self._thread_pool.start(worker)

    def _on_scan_finished(self, generation: int, root: Path, entries: list) -> None:
        if generation != self._scan_generation:
            return  # superseded by a newer navigation/toggle

        self._all_entries = entries
        self._table_model.set_entries(entries, root)
        self.statusBar().showMessage(f"{root}  —  {len(entries)} entries")

    def _apply_filter(self, text: str) -> None:
        text = text.lower()
        filtered = [e for e in self._all_entries if text in e.name.lower()]
        self._table_model.set_entries(filtered, self._current_root)

    def _on_recursive_toggled(self, checked: bool) -> None:
        self._app_settings.set_recursive_scan(checked)
        self._table_view.setColumnHidden(LOCATION_COLUMN, not checked)
        self._load_directory(self._current_root)

    def _navigate_to(self, path: Path) -> None:
        """Load `path`, recording the current folder in the back history."""
        if path == self._current_root:
            self._load_directory(path)
            return

        self._history_back.append(self._current_root)
        self._history_forward.clear()
        self._load_directory(path)
        self._update_nav_actions()

    def _go_back(self) -> None:
        if not self._history_back:
            return
        self._history_forward.append(self._current_root)
        self._load_directory(self._history_back.pop())
        self._update_nav_actions()

    def _go_forward(self) -> None:
        if not self._history_forward:
            return
        self._history_back.append(self._current_root)
        self._load_directory(self._history_forward.pop())
        self._update_nav_actions()

    def _update_nav_actions(self) -> None:
        self._back_action.setEnabled(bool(self._history_back))
        self._forward_action.setEnabled(bool(self._history_forward))

    def _open_folder_dialog(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Open Folder", str(self._current_root))
        if directory:
            self._navigate_to(Path(directory))

    def _go_up(self) -> None:
        parent = self._current_root.parent
        if parent != self._current_root:
            self._navigate_to(parent)

    def _new_folder(self) -> None:
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name:
            return

        try:
            create_folder(self._current_root, name)
        except (ValueError, OSError) as exc:
            QMessageBox.critical(self, "Could not create folder", str(exc))
            return

        self._load_directory(self._current_root)

    def _export_file_list(self) -> None:
        default_path = str(self._current_root / "arife-export.csv")
        path_str, selected_filter = QFileDialog.getSaveFileName(
            self, "Export File List", default_path, "CSV files (*.csv);;JSON files (*.json)"
        )
        if not path_str:
            return

        destination = Path(path_str)
        use_json = "JSON" in selected_filter or destination.suffix.lower() == ".json"
        wanted_suffix = ".json" if use_json else ".csv"
        if destination.suffix.lower() != wanted_suffix:
            destination = destination.with_suffix(wanted_suffix)

        entries = self._table_model.entries()
        try:
            if use_json:
                export_entries_to_json(entries, self._current_root, destination)
            else:
                export_entries_to_csv(entries, self._current_root, destination)
        except OSError as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return

        self.statusBar().showMessage(f"Exported {len(entries)} entries to {destination}")

    def _on_tree_clicked(self, index) -> None:
        path = self._dir_model.filePath(index)
        self._navigate_to(Path(path))

    def _open_entry(self, entry) -> None:
        if entry.is_dir:
            self._navigate_to(entry.path)
        else:
            open_with_default_app(entry.path)

    def _on_table_double_clicked(self, index) -> None:
        entry = self._table_model.entry_at(index.row())
        if entry is not None:
            self._open_entry(entry)

    def _selected_entries(self) -> list:
        rows = self._table_view.selectionModel().selectedRows()
        entries = (self._table_model.entry_at(r.row()) for r in rows)
        return [e for e in entries if e is not None]

    def _on_open_requested(self) -> None:
        entries = self._selected_entries()
        if len(entries) == 1:
            self._open_entry(entries[0])

    def _on_delete_requested(self) -> None:
        entries = self._selected_entries()
        if entries:
            self._trash_entries(entries)

    def _on_rename_requested(self) -> None:
        entries = self._selected_entries()
        if len(entries) == 1:
            self._rename_entry_interactive(entries[0])

    def _rename_entry_interactive(self, entry) -> None:
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=entry.name)
        if not ok or not new_name or new_name == entry.name:
            return

        try:
            rename_entry(entry.path, new_name)
        except (ValueError, OSError) as exc:
            QMessageBox.critical(self, "Could not rename", str(exc))
            return

        self._load_directory(self._current_root)

    def _on_table_context_menu(self, position: QPoint) -> None:
        index = self._table_view.indexAt(position)
        if not index.isValid():
            if self._clipboard_paths:
                menu = QMenu(self)
                paste_action = menu.addAction("Paste")
                if menu.exec(self._table_view.viewport().mapToGlobal(position)) is paste_action:
                    self._paste_clipboard()
            return

        if not self._table_view.selectionModel().isSelected(index):
            self._table_view.selectionModel().clearSelection()
            self._table_view.selectRow(index.row())

        entries = self._selected_entries()
        if not entries:
            return

        menu = QMenu(self)
        menu.setToolTipsVisible(True)

        open_action = reveal_action = rename_action = None
        if len(entries) == 1:
            open_action = menu.addAction("Open")
            reveal_action = menu.addAction(reveal_label())
            menu.addSeparator()
            copy_path_action = menu.addAction("Copy Path")
            rename_action = menu.addAction("Rename…")
        else:
            copy_path_action = menu.addAction("Copy Paths")

        menu.addSeparator()
        cut_action = menu.addAction("Cut")
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        paste_action.setEnabled(bool(self._clipboard_paths))

        menu.addSeparator()
        trash_label = "Move to Trash…" if len(entries) == 1 else f"Move {len(entries)} Items to Trash…"
        trash_action = menu.addAction(trash_label)
        trash_action.setEnabled(trash_available())
        if not trash_available():
            trash_action.setToolTip("Install the 'send2trash' extra to enable this (pip install arife[trash])")

        chosen = menu.exec(self._table_view.viewport().mapToGlobal(position))
        if chosen is None:
            return

        if chosen is open_action:
            self._open_entry(entries[0])
        elif chosen is reveal_action:
            reveal_in_file_manager(entries[0].path)
        elif chosen is copy_path_action:
            QApplication.clipboard().setText("\n".join(str(e.path) for e in entries))
        elif chosen is rename_action:
            self._rename_entry_interactive(entries[0])
        elif chosen is cut_action:
            self._cut_selection()
        elif chosen is copy_action:
            self._copy_selection()
        elif chosen is paste_action:
            self._paste_clipboard()
        elif chosen is trash_action:
            self._trash_entries(entries)

    def _trash_entries(self, entries: list) -> None:
        if len(entries) == 1:
            message = f'Move "{entries[0].name}" to the trash?'
        else:
            message = f"Move {len(entries)} items to the trash?"

        confirmed = QMessageBox.question(
            self,
            "Move to Trash",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmed != QMessageBox.StandardButton.Yes:
            return

        failures = []
        for entry in entries:
            try:
                move_to_trash(entry.path)
            except Exception as exc:  # noqa: BLE001 - surface any backend failure, not just OSError
                failures.append(f"{entry.name}: {exc}")

        self._load_directory(self._current_root)

        if failures:
            QMessageBox.warning(self, "Some items could not be trashed", "\n".join(failures))

    def _copy_selection(self) -> None:
        entries = self._selected_entries()
        if not entries:
            return
        self._set_clipboard([e.path for e in entries], cut=False)

    def _cut_selection(self) -> None:
        entries = self._selected_entries()
        if not entries:
            return
        self._set_clipboard([e.path for e in entries], cut=True)

    def _set_clipboard(self, paths: list[Path], *, cut: bool) -> None:
        self._clipboard_paths = paths
        self._clipboard_cut = cut
        self._paste_action.setEnabled(True)
        verb = "Cut" if cut else "Copied"
        self.statusBar().showMessage(f"{verb} {len(paths)} item(s)")

    def _paste_clipboard(self) -> None:
        if not self._clipboard_paths:
            return

        failures = []
        for source in self._clipboard_paths:
            try:
                if self._clipboard_cut:
                    move_entry(source, self._current_root)
                else:
                    copy_entry(source, self._current_root)
            except (OSError, shutil.Error) as exc:
                failures.append(f"{source.name}: {exc}")

        if self._clipboard_cut:
            self._clipboard_paths = []
            self._paste_action.setEnabled(False)

        self._load_directory(self._current_root)

        if failures:
            QMessageBox.warning(self, "Some items could not be pasted", "\n".join(failures))

    # -- Metadata extraction --------------------------------------------------------------
    def _on_selection_changed(self, *_args) -> None:
        rows = self._table_view.selectionModel().selectedRows()
        if not rows:
            self._selected_entry = None
            return

        if len(rows) > 1:
            self._selected_entry = None
            self._detail_panel.show_multi_selection(len(rows))
            return

        entry = self._table_model.entry_at(rows[0].row())
        if entry is None:
            self._selected_entry = None
            return

        self._selected_entry = entry
        self._detail_panel.show_loading(entry.name, is_dir=entry.is_dir)
        worker = MetadataExtractionWorker(entry, self._plugin_manager)
        worker.signals.finished.connect(self._on_metadata_ready)
        self._thread_pool.start(worker)

        if not entry.is_dir and is_supported_image(entry.suffix):
            thumbnail_worker = ThumbnailWorker(entry)
            thumbnail_worker.signals.finished.connect(self._on_thumbnail_ready)
            self._thread_pool.start(thumbnail_worker)

    def _on_metadata_ready(self, entry, results) -> None:
        self._detail_panel.show_results(entry.name, results)

    def _on_thumbnail_ready(self, entry, image) -> None:
        if entry is self._selected_entry:
            self._detail_panel.show_thumbnail(image)

    def _on_hash_requested(self) -> None:
        entry = self._selected_entry
        if entry is None or entry.is_dir:
            return

        self._detail_panel.show_hash_pending()
        worker = HashWorker(entry)
        worker.signals.finished.connect(self._on_hash_ready)
        worker.signals.failed.connect(self._on_hash_failed)
        self._thread_pool.start(worker)

    def _on_hash_ready(self, entry, digest: str) -> None:
        if entry is self._selected_entry:
            self._detail_panel.show_hash_result(digest)

    def _on_hash_failed(self, entry, message: str) -> None:
        if entry is self._selected_entry:
            self._detail_panel.show_hash_error(message)

    # -- Menu actions -----------------------------------------------------------------------
    def _open_plugin_manager(self) -> None:
        dialog = PluginManagerDialog(self._plugin_manager, self)
        if dialog.exec():
            dialog.apply()
            disabled_ids = [
                plugin.id
                for plugin in self._plugin_manager.plugins()
                if not self._plugin_manager.is_enabled(plugin.id)
            ]
            self._app_settings.set_disabled_plugin_ids(disabled_ids)

    def _open_duplicate_finder(self) -> None:
        dialog = DuplicateFinderDialog(self._current_root, self)
        dialog.exec()

    def _open_content_search(self) -> None:
        dialog = ContentSearchDialog(
            self._current_root, recursive=self._recursive_checkbox.isChecked(), parent=self
        )
        dialog.exec()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About ARIFE",
            f"<h3>ARIFE {__version__}</h3>"
            f"<p>{APP_TAGLINE}</p>"
            "<p>A free, open-source, plugin-based file and metadata explorer "
            "for researchers.</p>"
            "<p>Licensed under the MIT License.</p>",
        )
