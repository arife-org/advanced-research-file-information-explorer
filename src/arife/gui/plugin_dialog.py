"""Dialog for enabling/disabling ARIFE plugins."""
from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from arife.core.plugin import PluginManager


class PluginManagerDialog(QDialog):
    def __init__(self, plugin_manager: PluginManager, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plugin Manager")
        self.setMinimumWidth(420)

        self._plugin_manager = plugin_manager
        self._checkboxes: dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)

        for plugin in plugin_manager.plugins():
            available = plugin.is_available()
            label = plugin.display_name
            if not available:
                label += "  (missing optional dependency)"

            checkbox = QCheckBox(label)
            checkbox.setChecked(plugin_manager.is_enabled(plugin.id) and available)
            checkbox.setEnabled(available)
            layout.addWidget(checkbox)

            if plugin.description:
                desc = QLabel(plugin.description)
                desc.setStyleSheet("color: gray; margin-left: 22px; margin-bottom: 6px;")
                desc.setWordWrap(True)
                layout.addWidget(desc)

            self._checkboxes[plugin.id] = checkbox

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def apply(self) -> None:
        for plugin_id, checkbox in self._checkboxes.items():
            self._plugin_manager.set_enabled(plugin_id, checkbox.isChecked())
