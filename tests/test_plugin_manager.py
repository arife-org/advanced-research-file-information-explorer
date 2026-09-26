from pathlib import Path

from arife.core.models import FileEntry
from arife.core.plugin import InfoPlugin, PluginManager


class _AlwaysPlugin(InfoPlugin):
    id = "always"
    display_name = "Always"

    def supports(self, entry: FileEntry) -> bool:
        return True

    def extract(self, entry: FileEntry) -> dict[str, object]:
        return {"ok": True}


class _FailingPlugin(InfoPlugin):
    id = "failing"
    display_name = "Failing"

    def supports(self, entry: FileEntry) -> bool:
        return True

    def extract(self, entry: FileEntry) -> dict[str, object]:
        raise RuntimeError("boom")


class _NeverPlugin(InfoPlugin):
    id = "never"
    display_name = "Never"

    def supports(self, entry: FileEntry) -> bool:
        return False

    def extract(self, entry: FileEntry) -> dict[str, object]:
        return {}


def _make_entry(tmp_path: Path) -> FileEntry:
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")
    return FileEntry.from_path(file_path)


def test_register_and_enable_by_default(tmp_path: Path) -> None:
    manager = PluginManager()
    manager.register(_AlwaysPlugin())

    assert manager.is_enabled("always") is True


def test_extract_all_only_runs_enabled_supporting_plugins(tmp_path: Path) -> None:
    manager = PluginManager()
    manager.register(_AlwaysPlugin())
    manager.register(_NeverPlugin())
    manager.set_enabled("never", False)

    entry = _make_entry(tmp_path)
    results = manager.extract_all(entry)

    assert len(results) == 1
    assert results[0].plugin_id == "always"
    assert results[0].values == {"ok": True}


def test_extract_all_isolates_plugin_failures(tmp_path: Path) -> None:
    manager = PluginManager()
    manager.register(_AlwaysPlugin())
    manager.register(_FailingPlugin())

    entry = _make_entry(tmp_path)
    results = {r.plugin_id: r for r in manager.extract_all(entry)}

    assert results["always"].error is None
    assert results["failing"].error == "boom"


def test_disabled_plugin_is_excluded(tmp_path: Path) -> None:
    manager = PluginManager()
    manager.register(_AlwaysPlugin())
    manager.set_enabled("always", False)

    entry = _make_entry(tmp_path)
    results = manager.extract_all(entry)

    assert results == []
