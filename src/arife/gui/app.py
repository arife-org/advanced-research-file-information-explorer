"""Application bootstrap for the ARIFE desktop GUI."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from arife.gui.main_window import MainWindow


def run_app(argv: list[str]) -> int:
    app = QApplication(argv)
    app.setApplicationName("ARIFE")
    app.setOrganizationName("ARIFE")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_app(sys.argv))
