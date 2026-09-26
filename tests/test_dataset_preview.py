import json
from pathlib import Path

from arife.core.models import FileEntry
from arife.plugins.dataset_preview import DatasetPreviewPlugin


def test_supports_csv_tsv_json(tmp_path: Path) -> None:
    plugin = DatasetPreviewPlugin()
    for suffix in (".csv", ".tsv", ".json", ".jsonl"):
        path = tmp_path / f"file{suffix}"
        path.write_text("{}")
        assert plugin.supports(FileEntry.from_path(path)) is True

    other = tmp_path / "file.txt"
    other.write_text("x")
    assert plugin.supports(FileEntry.from_path(other)) is False


def test_extract_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")

    plugin = DatasetPreviewPlugin()
    values = plugin.extract(FileEntry.from_path(csv_path))

    assert values["Columns"] == 3
    assert values["Rows"] == 2
    assert values["Column names"] == "a, b, c"


def test_extract_json_array(tmp_path: Path) -> None:
    json_path = tmp_path / "data.json"
    json_path.write_text(json.dumps([{"x": 1, "y": 2}, {"x": 3, "y": 4}]))

    plugin = DatasetPreviewPlugin()
    values = plugin.extract(FileEntry.from_path(json_path))

    assert values["Format"] == "JSON array"
    assert values["Records"] == 2
    assert values["Fields (first record)"] == "x, y"
