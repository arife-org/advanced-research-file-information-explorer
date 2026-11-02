# Changelog

All notable changes to ARIFE are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- New Folder (File → New Folder…, Ctrl+Shift+N) and Rename (F2 or
  right-click → Rename…).
- Copy, Cut and Paste (Edit menu or right-click, Ctrl+C/Ctrl+X/Ctrl+V) for
  files and folders, including pasting into the same folder to duplicate,
  recursive copying of directories, and auto-renaming (`name (copy).ext`)
  on a name collision.
- `CONTRIBUTING.md` and GitHub issue/PR templates for contributors.

## [0.2.0] - 2026-10-27

### Added
- Sortable file table (click a column header; folders always stay on top).
- On-demand SHA-256 hashing of the selected file from the detail panel.
- Persisted session state (last folder, recursive-scan setting, disabled
  plugins, window geometry) via a typed `AppSettings` wrapper.
- Recursive subfolder scanning with an "Include subfolders" toggle and a
  "Location" column showing each result's path relative to the current
  folder.
- Duplicate file finder (Tools → Find Duplicate Files…), grouping files by
  content hash with a size pre-filter, cancellable and backgrounded.
- CSV/JSON export of the current file listing (File → Export File List…).
- Opening a file with the OS default app (double-click or Enter), a
  right-click context menu (Open, Reveal in Finder/Explorer, Copy Path),
  and safely moving files to the trash (Delete key or context menu) via the
  optional `send2trash` dependency — never a permanent delete.
- Multi-selection (Ctrl/Shift-click) with batch "Copy Paths" and batch
  "Move to Trash".
- Native per-file-type icons in the file table.
- "Go Up" navigation (File menu, Alt+Up).
- Full-text content search across plain-text files and PDFs (Tools →
  Search File Contents…, Ctrl+Shift+F), recursive, backgrounded, with a
  match snippet per result.
- CI pipeline (GitHub Actions) running ruff and the full pytest suite
  (including headless GUI smoke tests) on every push and pull request.

### Fixed
- `scan_directory` crashed when a recursive scan hit a permission-protected
  subfolder (e.g. a macOS Photos Library); such folders are now skipped
  instead of aborting the whole scan.
- Package metadata used a deprecated license classifier and pointed at the
  wrong repository URL.

### Changed
- Refactored `MainWindow`'s UI construction into focused builder methods
  and extracted all `QSettings` access behind `AppSettings`.

## [0.1.0] - 2026-09-27

### Added
- Initial release: directory scanner, plugin system (discovered via Python
  entry points), and a PySide6 desktop GUI (folder tree, file table, detail
  panel, plugin manager dialog).
- Built-in plugins: Basic Metadata, Research Paper (PDF), Dataset Preview,
  Image/EXIF.
- MIT license.
