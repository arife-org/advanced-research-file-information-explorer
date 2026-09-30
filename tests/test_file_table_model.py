"""Tests for FileTableModel, including the recursive-scan "Location" column."""
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _make_entries(root: Path):
    from arife.core.models import FileEntry

    (root / "top.txt").write_text("x")
    sub = root / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("y")

    return [
        FileEntry.from_path(root / "top.txt"),
        FileEntry.from_path(sub),
        FileEntry.from_path(sub / "nested.txt"),
    ]


def test_location_is_empty_for_top_level_entries(qapp, tmp_path):
    from arife.gui.file_table_model import FileTableModel

    entries = _make_entries(tmp_path)
    model = FileTableModel()
    model.set_entries(entries, tmp_path)

    top_row = next(r for r in range(model.rowCount()) if model.entry_at(r).name == "top.txt")
    index = model.index(top_row, 5)  # Location column
    assert model.data(index) == "."


def test_location_shows_relative_subfolder_for_nested_entries(qapp, tmp_path):
    from arife.gui.file_table_model import FileTableModel

    entries = _make_entries(tmp_path)
    model = FileTableModel()
    model.set_entries(entries, tmp_path)

    nested_row = next(r for r in range(model.rowCount()) if model.entry_at(r).name == "nested.txt")
    index = model.index(nested_row, 5)
    assert model.data(index) == "sub"


def test_sort_keeps_directories_on_top(qapp, tmp_path):
    from PySide6.QtCore import Qt

    from arife.gui.file_table_model import FileTableModel

    entries = _make_entries(tmp_path)
    model = FileTableModel()
    model.set_entries(entries, tmp_path)

    model.sort(0, Qt.SortOrder.AscendingOrder)

    first_entry = model.entry_at(0)
    assert first_entry.is_dir is True
