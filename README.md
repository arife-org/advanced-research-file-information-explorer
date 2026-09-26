# ARIFE — Advanced Research File Information Explorer

**ARIFE** is a free, open-source desktop application for exploring files and
digging into their metadata — built for researchers, data scientists and
anyone who deals with large, messy collections of papers, datasets and
research artifacts.

Instead of hard-coding support for a fixed list of file types, ARIFE is built
around a small **plugin system**: every "kind of insight" about a file (basic
filesystem info, a PDF's title/author/DOI, a CSV's shape, an image's EXIF
data, ...) is a self-contained plugin. Enable the ones you need, write your
own for the file types you care about, and ARIFE stays useful no matter what
your research throws at it.

> ⚠️ Status: early alpha. Core scanning, the plugin system and the desktop UI
> are functional; expect rough edges and rapid change.

## Features

- 🗂️ **Folder tree + file table** — browse your filesystem like a normal file
  explorer, with a live detail panel for whatever you select.
- 🔌 **Plugin-based metadata extraction** — every plugin decides which files
  it applies to and what metadata it contributes; results are merged and
  shown grouped by plugin.
- 🧠 **Built-in plugins**:
  - **Basic Metadata** — size, timestamps, MIME type, extension (works for
    every file, no extra dependencies).
  - **Research Paper (PDF)** — title, author, subject, page count and a
    best-effort DOI extracted from the document text.
  - **Dataset Preview** — row/column counts, column names and a first-row
    preview for CSV/TSV, and structure for JSON/JSON Lines files.
  - **Image / EXIF** — dimensions, format, color mode and key EXIF fields
    (camera make/model, exposure, ISO, focal length, ...).
- 🧩 **Extensible by design** — third-party plugins are discovered
  automatically via standard Python entry points, no core changes required.
- ⚡ **Responsive UI** — metadata extraction runs on background threads, so
  parsing a large PDF or dataset never freezes the interface.
- 🆓 **100% free and open source**, MIT licensed, no telemetry, no lock-in.

## Installation

ARIFE requires **Python 3.10+**.

```bash
# Clone the repository
git clone https://github.com/arife-project/arife.git
cd arife

# Install with all optional plugin dependencies (PDF, images, datasets)
pip install -e ".[all]"
```

Prefer a minimal install and add plugin support later? Install the core
package and add extras as needed:

```bash
pip install -e .            # core + basic metadata + dataset preview only
pip install -e ".[pdf]"     # + PDF research paper plugin
pip install -e ".[images]"  # + image/EXIF plugin
```

## Usage

Launch the desktop app:

```bash
arife
# or
python -m arife
```

Then:

1. Browse to a folder using the tree on the left, or **File → Open Folder…**.
2. Select a file in the table to see everything ARIFE's active plugins can
   tell you about it, in the panel on the right.
3. Use the filter box to narrow down large folders by filename.
4. Open **Tools → Plugin Manager…** to enable or disable individual plugins
   (useful if a plugin's optional dependency isn't installed, or you simply
   don't need it).

## Writing your own plugin

A plugin is a small class implementing two methods: which files it applies
to, and what metadata it returns.

```python
# my_arife_plugin/plugin.py
from arife.core.models import FileEntry
from arife.core.plugin import InfoPlugin

class MarkdownWordCountPlugin(InfoPlugin):
    id = "markdown_word_count"
    display_name = "Markdown Word Count"
    description = "Counts words in Markdown files."

    def supports(self, entry: FileEntry) -> bool:
        return not entry.is_dir and entry.suffix == ".md"

    def extract(self, entry: FileEntry) -> dict[str, object]:
        text = entry.path.read_text(encoding="utf-8", errors="replace")
        return {"Word count": len(text.split())}
```

Register it via an entry point in your plugin package's `pyproject.toml`,
under the `arife.plugins` group:

```toml
[project.entry-points."arife.plugins"]
markdown_word_count = "my_arife_plugin.plugin:MarkdownWordCountPlugin"
```

Once your package is installed in the same environment as ARIFE, it shows up
automatically in **Tools → Plugin Manager…** — no core code changes needed.

If your plugin depends on an optional third-party library, override
`is_available()` to check for it; ARIFE will show the plugin as disabled with
a hint instead of crashing when the dependency is missing.

## Project layout

```
src/arife/
├── core/           # scanning, data models, plugin discovery/management
├── plugins/        # built-in plugins (basic metadata, PDF, datasets, images)
└── gui/            # PySide6 desktop application
tests/              # pytest test suite for core + built-in plugins
```

## Development

```bash
pip install -e ".[all,dev]"
pytest                # run the test suite
ruff check .          # lint
```

## Contributing

Issues and pull requests are welcome — whether that's a bug fix, a new
built-in plugin, or improvements to the UI. Since ARIFE's whole design is
built around small, independent plugins, adding support for a new file type
or research workflow rarely touches the core at all.

## License

ARIFE is released under the [MIT License](LICENSE) — free for anyone to use,
modify and distribute.
