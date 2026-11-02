# ARIFE — Advanced Research Information File Explorer

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

## Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Writing your own plugin](#writing-your-own-plugin)
- [Project layout](#project-layout)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

**Browsing & navigation**

- Folder tree + sortable file table, with native file-type icons and a live
  detail panel for whatever you select.
- Back / Forward navigation history (Alt+Left / Alt+Right) and Go Up
  (Alt+Up), the way you'd expect from any file manager.
- Recursive subfolder scanning with an "Include subfolders" toggle and a
  "Location" column showing each result's path relative to the current
  folder.
- Filter the current listing by filename as you type.

**Metadata, powered by plugins**

- Every plugin decides which files it applies to and what metadata it
  contributes; results are merged and shown grouped by plugin.
- Built in: **Basic Metadata** (size, timestamps, MIME type, extension, no
  extra dependencies), **Research Paper (PDF)** (title/author/subject, page
  count, best-effort DOI extraction), **Dataset Preview** (row/column counts
  and a first-row preview for CSV/TSV/JSON/JSON Lines), and **Image / EXIF**
  (dimensions, format, camera make/model, exposure, ISO, focal length, ...).
- On-demand SHA-256 hashing of the selected file.
- Full-text content search across plain-text files and PDFs (recursive,
  backgrounded, with a match snippet per result).
- Duplicate file finder — groups files by content hash with a size
  pre-filter so it doesn't hash everything, and reports reclaimable space.

**File management**

- Open with the OS default app, reveal in Finder/Explorer, and safely move
  to the trash (never a permanent delete) — single file or multi-selection.
- Copy, cut and paste files and folders, including pasting into the same
  folder to duplicate; name collisions are resolved automatically
  (`name (copy).ext`).
- New Folder and Rename (F2), with the same validation either way.
- Export the current listing to CSV or JSON for documentation.

**Everything else**

- Third-party plugins are discovered automatically via standard Python
  entry points — no core changes required to support a new file type.
- Metadata extraction, hashing, scanning, duplicate detection, and content
  search all run on background threads, so nothing ever freezes the UI.
- Remembers your last folder, plugin selection, recursive-scan setting, and
  window size between launches.
- 100% free and open source, MIT licensed, no telemetry, no lock-in.

## Installation

ARIFE requires **Python 3.10+**.

```bash
# Clone the repository
git clone https://github.com/arife-org/advanced-research-information-file-explorer.git
cd advanced-research-information-file-explorer

# Install with all optional extras (PDF, images, datasets, trash)
pip install -e ".[all]"
```

Prefer a minimal install and add extras later? Install the core package
and add extras as needed:

```bash
pip install -e .            # core + basic metadata + dataset preview only
pip install -e ".[pdf]"     # + PDF research paper plugin + PDF content search
pip install -e ".[images]"  # + image/EXIF plugin
pip install -e ".[trash]"   # + safe "move to trash" instead of permanent delete
```

## Usage

Launch the desktop app:

```bash
arife
# or
python -m arife
```

Then:

1. Browse to a folder using the tree on the left, **File → Open Folder…**,
   **File → Go Up** (Alt+Up), or **Back/Forward** (Alt+Left/Alt+Right) to
   retrace your steps.
2. Select a file in the table to see everything ARIFE's active plugins can
   tell you about it, in the panel on the right — including an on-demand
   SHA-256 hash via the button in the detail panel.
3. Use the filter box to narrow down large folders by filename, and click
   any column header to sort (folders always stay on top). Select multiple
   rows with Ctrl/Shift-click.
4. Check **Include subfolders** to scan recursively; a "Location" column
   then shows each result's path relative to the current folder.
5. Double-click or press Enter to open the selected file with your OS's
   default application; press Delete (or right-click → Move to Trash) to
   send it to the trash — never a permanent delete. Right-click also offers
   "Reveal in Finder/Explorer", "Copy Path", Copy/Cut/Paste (Ctrl+C/X/V),
   and Rename (F2).
6. **Tools → Search File Contents…** (Ctrl+Shift+F) to search inside text
   files and PDFs, **Tools → Find Duplicate Files…** to locate duplicate
   content, and **File → Export File List…** (Ctrl+E) to save the current
   listing as CSV/JSON.
7. Open **Tools → Plugin Manager…** to enable or disable individual plugins
   (useful if a plugin's optional dependency isn't installed, or you simply
   don't need it).

ARIFE remembers your last opened folder, plugin selection, recursive-scan
setting, and window size between launches.

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
├── core/           # scanning, data models, plugins, duplicates, search, export
├── plugins/        # built-in plugins (basic metadata, PDF, datasets, images)
└── gui/            # PySide6 desktop application
tests/              # pytest test suite for core + GUI (headless, offscreen)
```

See [CHANGELOG.md](CHANGELOG.md) for release history.

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
or research workflow rarely touches the core at all. See
[CONTRIBUTING.md](CONTRIBUTING.md) for dev environment setup, how the
codebase is organized, and what a good PR looks like.

## License

ARIFE is released under the [MIT License](LICENSE) — free for anyone to use,
modify and distribute.
