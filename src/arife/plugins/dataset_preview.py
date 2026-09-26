"""Plugin previewing tabular/structured research datasets (CSV, TSV, JSON)."""
from __future__ import annotations

import csv
import json

from arife.core.models import FileEntry
from arife.core.plugin import InfoPlugin

_TABULAR_SUFFIXES = {".csv", ".tsv"}
_JSON_SUFFIXES = {".json", ".jsonl"}


class DatasetPreviewPlugin(InfoPlugin):
    id = "dataset_preview"
    display_name = "Dataset Preview"
    description = "Shows row/column counts, column names and a data preview for CSV/TSV/JSON datasets."

    def supports(self, entry: FileEntry) -> bool:
        return not entry.is_dir and entry.suffix in (_TABULAR_SUFFIXES | _JSON_SUFFIXES)

    def extract(self, entry: FileEntry) -> dict[str, object]:
        if entry.suffix in _TABULAR_SUFFIXES:
            return self._extract_tabular(entry)
        return self._extract_json(entry)

    def _extract_tabular(self, entry: FileEntry) -> dict[str, object]:
        delimiter = "\t" if entry.suffix == ".tsv" else ","
        with open(entry.path, newline="", encoding="utf-8", errors="replace") as fh:
            reader = csv.reader(fh, delimiter=delimiter)
            rows = list(reader)

        if not rows:
            return {"Format": "tabular", "Rows": 0, "Columns": 0}

        header, *data_rows = rows
        return {
            "Format": "tabular",
            "Columns": len(header),
            "Rows": len(data_rows),
            "Column names": ", ".join(header),
            "Preview (first row)": ", ".join(data_rows[0]) if data_rows else "-",
        }

    def _extract_json(self, entry: FileEntry) -> dict[str, object]:
        if entry.suffix == ".jsonl":
            with open(entry.path, encoding="utf-8", errors="replace") as fh:
                lines = [line for line in fh if line.strip()]
            first = json.loads(lines[0]) if lines else {}
            return {
                "Format": "JSON Lines",
                "Records": len(lines),
                "Fields (first record)": ", ".join(first.keys()) if isinstance(first, dict) else "-",
            }

        with open(entry.path, encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)

        if isinstance(data, list):
            first = data[0] if data else {}
            return {
                "Format": "JSON array",
                "Records": len(data),
                "Fields (first record)": ", ".join(first.keys()) if isinstance(first, dict) else "-",
            }
        if isinstance(data, dict):
            return {
                "Format": "JSON object",
                "Top-level keys": len(data),
                "Keys": ", ".join(str(k) for k in data),
            }
        return {"Format": "JSON", "Value": str(data)[:200]}
