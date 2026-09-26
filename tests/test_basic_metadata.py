from pathlib import Path

from arife.core.models import FileEntry
from arife.plugins.basic_metadata import BasicMetadataPlugin, human_size


def test_human_size_formats_bytes_and_larger_units() -> None:
    assert human_size(500) == "500 B"
    assert human_size(2048) == "2.00 KB"
    assert human_size(5 * 1024 * 1024) == "5.00 MB"


def test_basic_metadata_supports_everything(tmp_path: Path) -> None:
    file_path = tmp_path / "notes.txt"
    file_path.write_text("hello world")
    entry = FileEntry.from_path(file_path)

    plugin = BasicMetadataPlugin()
    assert plugin.supports(entry) is True

    values = plugin.extract(entry)
    assert values["Name"] == "notes.txt"
    assert values["Type"] == "File"
    assert values["Extension"] == ".txt"
    assert values["Size (bytes)"] == len("hello world")


def test_basic_metadata_on_directory(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    entry = FileEntry.from_path(sub)

    plugin = BasicMetadataPlugin()
    values = plugin.extract(entry)

    assert values["Type"] == "Directory"
    assert values["Size"] == "-"
