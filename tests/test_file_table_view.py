"""Tests for FileTableView's Enter-to-open / Delete-to-trash key handling."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_enter_key_emits_open_requested(qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    from arife.gui.file_table_view import FileTableView

    view = FileTableView()
    received = []
    view.open_requested.connect(lambda: received.append(True))

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(view, event)

    assert received == [True]


def test_delete_key_emits_delete_requested(qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    from arife.gui.file_table_view import FileTableView

    view = FileTableView()
    received = []
    view.delete_requested.connect(lambda: received.append(True))

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(view, event)

    assert received == [True]


def test_other_keys_do_not_trigger_either_signal(qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtWidgets import QApplication

    from arife.gui.file_table_view import FileTableView

    view = FileTableView()
    opened = []
    deleted = []
    view.open_requested.connect(lambda: opened.append(True))
    view.delete_requested.connect(lambda: deleted.append(True))

    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(view, event)

    assert opened == []
    assert deleted == []
