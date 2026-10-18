"""Typed wrapper around QSettings for ARIFE's persisted desktop preferences.

Centralizing the setting keys here means there is exactly one place that
knows their names and default values, instead of string literals scattered
across the GUI code.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings

_LAST_FOLDER_KEY = "last_folder"
_RECURSIVE_SCAN_KEY = "recursive_scan"
_DISABLED_PLUGINS_KEY = "disabled_plugins"
_WINDOW_GEOMETRY_KEY = "window_geometry"


class AppSettings:
    """Reads and writes ARIFE's persisted preferences via QSettings."""

    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings if settings is not None else QSettings()

    def last_folder(self, default: Path) -> Path:
        saved = self._settings.value(_LAST_FOLDER_KEY, str(default))
        path = Path(saved)
        return path if path.is_dir() else default

    def set_last_folder(self, path: Path) -> None:
        self._settings.setValue(_LAST_FOLDER_KEY, str(path))

    def recursive_scan(self, default: bool = False) -> bool:
        return self._settings.value(_RECURSIVE_SCAN_KEY, default, type=bool)

    def set_recursive_scan(self, enabled: bool) -> None:
        self._settings.setValue(_RECURSIVE_SCAN_KEY, enabled)

    def disabled_plugin_ids(self) -> list[str]:
        ids = self._settings.value(_DISABLED_PLUGINS_KEY, [])
        if isinstance(ids, str):  # QSettings collapses a one-item list to a bare string
            ids = [ids]
        return list(ids)

    def set_disabled_plugin_ids(self, ids: list[str]) -> None:
        self._settings.setValue(_DISABLED_PLUGINS_KEY, ids)

    def window_geometry(self) -> QByteArray:
        return self._settings.value(_WINDOW_GEOMETRY_KEY, QByteArray())

    def set_window_geometry(self, geometry: QByteArray) -> None:
        self._settings.setValue(_WINDOW_GEOMETRY_KEY, geometry)
