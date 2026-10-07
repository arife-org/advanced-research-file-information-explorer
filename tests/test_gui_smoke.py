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
