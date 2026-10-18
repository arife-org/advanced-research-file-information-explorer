"""Tests for the typed QSettings wrapper used to persist ARIFE's preferences."""
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")


@pytest.fixture
def isolated_qsettings(tmp_path):
    """A QSettings instance backed by a throwaway file, never the real app prefs."""
    from PySide6.QtCore import QSettings

    settings = QSettings(str(tmp_path / "arife-test.ini"), QSettings.Format.IniFormat)
    yield settings
    settings.clear()


def test_last_folder_defaults_when_nothing_saved(isolated_qsettings, tmp_path):
    from arife.gui.settings import AppSettings

    settings = AppSettings(isolated_qsettings)
    assert settings.last_folder(tmp_path) == tmp_path


def test_last_folder_round_trips(isolated_qsettings, tmp_path):
    from arife.gui.settings import AppSettings

    settings = AppSettings(isolated_qsettings)
    settings.set_last_folder(tmp_path)

    assert settings.last_folder(Path("/nonexistent-default")) == tmp_path


def test_last_folder_falls_back_if_saved_path_no_longer_exists(isolated_qsettings, tmp_path):
    from arife.gui.settings import AppSettings

    settings = AppSettings(isolated_qsettings)
    gone = tmp_path / "deleted"
    settings.set_last_folder(gone)  # never created, so it doesn't exist

    assert settings.last_folder(tmp_path) == tmp_path


def test_recursive_scan_round_trips(isolated_qsettings):
    from arife.gui.settings import AppSettings

    settings = AppSettings(isolated_qsettings)
    assert settings.recursive_scan() is False

    settings.set_recursive_scan(True)
    assert settings.recursive_scan() is True


def test_disabled_plugin_ids_round_trips_a_list(isolated_qsettings):
    from arife.gui.settings import AppSettings

    settings = AppSettings(isolated_qsettings)
    assert settings.disabled_plugin_ids() == []

    settings.set_disabled_plugin_ids(["pdf_research", "image_exif"])
    assert settings.disabled_plugin_ids() == ["pdf_research", "image_exif"]


def test_disabled_plugin_ids_handles_single_item(isolated_qsettings):
    from arife.gui.settings import AppSettings

    settings = AppSettings(isolated_qsettings)
    settings.set_disabled_plugin_ids(["pdf_research"])

    assert settings.disabled_plugin_ids() == ["pdf_research"]


def test_window_geometry_round_trips(isolated_qsettings):
    from PySide6.QtCore import QByteArray

    from arife.gui.settings import AppSettings

    settings = AppSettings(isolated_qsettings)
    assert bytes(settings.window_geometry()) == b""

    payload = QByteArray(b"some-geometry-bytes")
    settings.set_window_geometry(payload)
    assert bytes(settings.window_geometry()) == b"some-geometry-bytes"
