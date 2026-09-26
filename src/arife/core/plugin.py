"""Plugin base class and plugin discovery/management for ARIFE.

Third-party plugins are discovered via the standard Python entry-points
mechanism under the ``arife.plugins`` group, e.g. in a plugin package's
``pyproject.toml``::

    [project.entry-points."arife.plugins"]
    my_plugin = "my_package.my_module:MyPlugin"

Built-in plugins shipped with ARIFE register themselves the same way (see
``pyproject.toml`` in this repository), so there is exactly one discovery
path for both first- and third-party plugins.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from importlib.metadata import entry_points

from arife.core.models import FileEntry, MetadataResult

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "arife.plugins"


class InfoPlugin(ABC):
    """Base class for all ARIFE metadata plugins."""

    #: Stable machine-readable identifier, e.g. "pdf_research".
    id: str = "unnamed_plugin"

    #: Human-readable name shown in the GUI.
    display_name: str = "Unnamed Plugin"

    #: Short description shown in the plugin manager.
    description: str = ""

    def is_available(self) -> bool:
        """Whether the plugin's optional dependencies are installed."""
        return True

    @abstractmethod
    def supports(self, entry: FileEntry) -> bool:
        """Return True if this plugin can extract metadata from `entry`."""

    @abstractmethod
    def extract(self, entry: FileEntry) -> dict[str, object]:
        """Extract and return metadata for `entry` as a flat key/value dict."""

    def safe_extract(self, entry: FileEntry) -> MetadataResult:
        """Call `extract`, converting exceptions into an error result."""
        try:
            values = self.extract(entry)
            return MetadataResult(self.id, self.display_name, values=values)
        except Exception as exc:
            logger.exception("Plugin %s failed on %s", self.id, entry.path)
            return MetadataResult(self.id, self.display_name, error=str(exc))


class PluginManager:
    """Discovers, holds and runs `InfoPlugin` instances."""

    def __init__(self) -> None:
        self._plugins: dict[str, InfoPlugin] = {}
        self._enabled: dict[str, bool] = {}

    def discover(self) -> None:
        """Load all plugins registered under the `arife.plugins` entry-point group."""
        for ep in entry_points(group=ENTRY_POINT_GROUP):
            try:
                plugin_cls = ep.load()
                plugin: InfoPlugin = plugin_cls()
            except Exception:
                logger.exception("Failed to load plugin entry point %r", ep.name)
                continue
            self.register(plugin)

    def register(self, plugin: InfoPlugin) -> None:
        self._plugins[plugin.id] = plugin
        self._enabled.setdefault(plugin.id, plugin.is_available())

    def plugins(self) -> list[InfoPlugin]:
        return list(self._plugins.values())

    def enabled_plugins(self) -> list[InfoPlugin]:
        return [p for p in self._plugins.values() if self._enabled.get(p.id, False)]

    def is_enabled(self, plugin_id: str) -> bool:
        return self._enabled.get(plugin_id, False)

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        if plugin_id in self._plugins:
            self._enabled[plugin_id] = enabled

    def extract_all(self, entry: FileEntry) -> list[MetadataResult]:
        """Run every enabled, applicable plugin against `entry`."""
        results = []
        for plugin in self.enabled_plugins():
            if not plugin.is_available():
                continue
            try:
                if not plugin.supports(entry):
                    continue
            except Exception:
                logger.exception("Plugin %s.supports() failed on %s", plugin.id, entry.path)
                continue
            results.append(plugin.safe_extract(entry))
        return results
