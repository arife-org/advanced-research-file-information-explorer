import csv
import json
from pathlib import Path

from arife.core.export import export_entries_to_csv, export_entries_to_json
from arife.core.models import FileEntry


def _make_entries(root: Path) -> list[FileEntry]:
    (root / "top.txt").write_text("hello")
    sub = root / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("world")

    return [
        FileEntry.from_path(root / "top.txt"),
        FileEntry.from_path(sub / "nested.txt"),
    ]


def test_export_entries_to_csv(tmp_path: Path) -> None:
    entries = _make_entries(tmp_path)
    destination = tmp_path / "out.csv"

    export_entries_to_csv(entries, tmp_path, destination)

    with open(destination, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    assert len(rows) == 2
    top_row = next(r for r in rows if r["name"] == "top.txt")
    assert top_row["type"] == "file"
    assert top_row["location"] == ""
    assert top_row["size_bytes"] == str(len("hello"))

    nested_row = next(r for r in rows if r["name"] == "nested.txt")
    assert nested_row["location"] == "sub"


def test_export_entries_to_json(tmp_path: Path) -> None:
    entries = _make_entries(tmp_path)
    destination = tmp_path / "out.json"

    export_entries_to_json(entries, tmp_path, destination)

    rows = json.loads(destination.read_text(encoding="utf-8"))

    assert len(rows) == 2
    nested_row = next(r for r in rows if r["name"] == "nested.txt")
    assert nested_row["location"] == "sub"
    assert nested_row["extension"] == ".txt"
