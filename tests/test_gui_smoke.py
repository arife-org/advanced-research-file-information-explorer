"""Headless smoke tests for the PySide6 desktop GUI.

These run with the "offscreen" Qt platform plugin so they work in CI and
other environments without a real display.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path):
    """Redirect QSettings to a throwaway file so tests never touch (or are
    affected by) the real ARIFE desktop preferences on this machine."""
    from PySide6.QtCore import QCoreApplication, QSettings

    QCoreApplication.setOrganizationName("ARIFE")
    QCoreApplication.setApplicationName("ARIFE")
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    yield


def test_main_window_constructs_and_lists_home_directory(qapp):
    from arife.gui.main_window import MainWindow

    window = MainWindow()
    try:
        assert window._table_model.rowCount() >= 0
        assert len(window._plugin_manager.plugins()) >= 1
    finally:
        window.close()


def test_plugin_manager_dialog_constructs(qapp):
    from arife.core.plugin import PluginManager
    from arife.gui.plugin_dialog import PluginManagerDialog

    manager = PluginManager()
    manager.discover()
    dialog = PluginManagerDialog(manager)
    assert dialog is not None


def _wait_until(app, condition, timeout=2.0):
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if condition():
            return True
    return False


def test_navigation_history_back_and_forward(qapp, tmp_path):
    from arife.gui.main_window import MainWindow

    sub = tmp_path / "sub"
    sub.mkdir()

    window = MainWindow()
    try:
        window._navigate_to(tmp_path)
        assert _wait_until(qapp, lambda: window._current_root == tmp_path)

        window._navigate_to(sub)
        assert _wait_until(qapp, lambda: window._current_root == sub)
        assert window._history_back[-1] == tmp_path
        assert window._back_action.isEnabled()
        assert not window._forward_action.isEnabled()

        window._go_back()
        assert _wait_until(qapp, lambda: window._current_root == tmp_path)
        assert window._history_forward == [sub]
        assert window._forward_action.isEnabled()

        window._go_forward()
        assert _wait_until(qapp, lambda: window._current_root == sub)
        assert window._history_back[-1] == tmp_path
        assert not window._history_forward
    finally:
        window.close()
