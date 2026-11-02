"""Basic file operations (creating folders, renaming, copying, moving)."""
from __future__ import annotations

import shutil
from pathlib import Path


def validate_filename(name: str) -> str | None:
    """Return an error message if `name` is not a valid filename, else None."""
    name = name.strip()
    if not name:
        return "Name cannot be empty."
    if name in (".", ".."):
        return f'"{name}" is not a valid name.'
    if "/" in name or "\x00" in name:
        return "Name cannot contain '/'."
    return None


def create_folder(parent: Path, name: str) -> Path:
    """Create a new subfolder named `name` inside `parent`.

    Raises `ValueError` for an invalid name, `FileExistsError` if something
    with that name already exists there.
    """
    error = validate_filename(name)
    if error:
        raise ValueError(error)

    target = parent / name.strip()
    target.mkdir()
    return target


def rename_entry(path: Path, new_name: str) -> Path:
    """Rename `path` to `new_name`, keeping it in the same parent directory.

    Raises `ValueError` for an invalid name, `FileExistsError` if the target
    name is already taken.
    """
    error = validate_filename(new_name)
    if error:
        raise ValueError(error)

    target = path.parent / new_name.strip()
    if target.exists():
        raise FileExistsError(f'"{new_name}" already exists.')

    path.rename(target)
    return target


def unique_destination(destination_dir: Path, name: str) -> Path:
    """Return a free path for `name` inside `destination_dir`.

    If `name` is already taken, appends " (copy)", " (copy 2)", ... before
    the extension until a free name is found.
    """
    candidate = destination_dir / name
    if not candidate.exists():
        return candidate

    stem, suffix = candidate.stem, candidate.suffix
    candidate = destination_dir / f"{stem} (copy){suffix}"
    counter = 2
    while candidate.exists():
        candidate = destination_dir / f"{stem} (copy {counter}){suffix}"
        counter += 1
    return candidate


def copy_entry(source: Path, destination_dir: Path) -> Path:
    """Copy `source` (file or directory) into `destination_dir`.

    Auto-renames on a name collision (including copying onto its own
    parent), so this also implements "duplicate in place".
    """
    target = unique_destination(destination_dir, source.name)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)
    return target


def move_entry(source: Path, destination_dir: Path) -> Path:
    """Move `source` into `destination_dir`, keeping its name.

    A no-op if `source` is already directly inside `destination_dir`.
    Raises `FileExistsError` if a different entry already has that name.
    """
    target = destination_dir / source.name
    if target == source:
        return source
    if target.exists():
        raise FileExistsError(f'"{source.name}" already exists in the destination.')

    shutil.move(str(source), str(target))
    return target
