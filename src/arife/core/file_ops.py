"""Basic file operations (creating folders, renaming) with shared name validation."""
from __future__ import annotations

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
