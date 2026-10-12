"""Cross-platform helpers for acting on a file from the GUI (open, reveal)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


def open_with_default_app(path: Path) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


def reveal_label(*, platform: str = sys.platform) -> str:
    """Menu label for revealing a file, matching the host OS's own terminology."""
    if platform == "darwin":
        return "Reveal in Finder"
    if platform == "win32":
        return "Show in Explorer"
    return "Open Containing Folder"


def reveal_command(path: Path, *, platform: str = sys.platform) -> list[str] | None:
    """OS command that reveals `path` in the system file manager, or None if unsupported."""
    if platform == "darwin":
        return ["open", "-R", str(path)]
    if platform == "win32":
        return ["explorer", f"/select,{path}"]
    if platform.startswith("linux"):
        # No universal "select this file" on Linux; open its containing folder instead.
        target = path if path.is_dir() else path.parent
        return ["xdg-open", str(target)]
    return None


def reveal_in_file_manager(path: Path) -> bool:
    """Reveal `path` in the system file manager. Returns False if unsupported or it failed."""
    command = reveal_command(path)
    if command is None:
        return False
    try:
        subprocess.Popen(command)
    except OSError:
        return False
    return True
