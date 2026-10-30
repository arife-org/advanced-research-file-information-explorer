# Contributing to ARIFE

Thanks for considering a contribution. ARIFE is a small, plugin-based
desktop tool, and most changes fit into one of three places: a new/fixed
plugin, a core improvement (scanning, duplicates, search, export, file
ops), or a GUI change. This doc covers what you need to get a change in.

## Setting up a dev environment

```bash
git clone https://github.com/arife-org/advanced-research-file-information-explorer.git
cd advanced-research-file-information-explorer

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -e ".[all,dev]"        # installs every plugin extra + pytest/ruff
```

Run the app with `arife` or `python -m arife`.

## Running tests and lint

```bash
pytest          # full suite, including headless GUI smoke tests
ruff check .     # lint
```

The GUI tests run with `QT_QPA_PLATFORM=offscreen` automatically (set in
the test files themselves), so they work without a real display — this is
also how CI runs them. If you add a test that constructs `MainWindow` or
anything else backed by `QSettings`, isolate it the way
`tests/test_gui_smoke.py`'s `isolated_settings` fixture does: real app
preferences should never be touched by the test suite.

## Code organization

```
src/arife/
├── core/     # pure logic: scanning, models, plugins, duplicates, search,
│             # export, file ops. No Qt imports here - keeps this half of
│             # the codebase testable without a display or event loop.
├── plugins/  # built-in InfoPlugin implementations
└── gui/      # PySide6 widgets, dialogs, and background QRunnable workers
```

Slow or blocking work (scanning, hashing, duplicate detection, content
search, plugin metadata extraction) runs on a background thread via a
`QRunnable` in `gui/worker.py`, emitting Qt signals back to the main
thread. Follow that pattern for new long-running operations instead of
blocking the GUI thread.

## Adding a plugin

See the "Writing your own plugin" section in [README.md](README.md). A
built-in plugin registers itself as an entry point in `pyproject.toml`
under `[project.entry-points."arife.plugins"]`; a third-party plugin
package does the same in its own `pyproject.toml` and needs no changes to
ARIFE's code at all.

If your plugin needs an optional dependency, override `is_available()` so
ARIFE can show it as disabled (with a reason) instead of crashing when
that dependency is missing - see `pdf_research.py` or `image_exif.py` for
examples.

## Commit and PR expectations

- Keep commits focused; a bug fix and an unrelated refactor belong in
  separate commits.
- Add or update tests for any behavior change. Core logic (`core/`) should
  be unit-testable without Qt; GUI behavior gets a headless smoke/
  integration test where practical.
- Run `pytest` and `ruff check .` before opening a PR - CI runs both on
  every push and PR, so a red CI run will block review either way.
- Describe *why* a change was made, not just what changed, in the PR
  description.

## Reporting bugs / requesting features

Open a GitHub issue. For bugs, include your OS, Python version, ARIFE
version (`Help -> About ARIFE`), and steps to reproduce. For feature
requests, a concrete use case ("I'm trying to do X with Y kind of files
and ARIFE doesn't support Z") is more actionable than an abstract ask.
