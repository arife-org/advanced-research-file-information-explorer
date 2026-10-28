from pathlib import Path

import pytest

from arife.core.file_ops import create_folder, rename_entry, validate_filename


def test_validate_filename_rejects_empty_and_whitespace() -> None:
    assert validate_filename("") is not None
    assert validate_filename("   ") is not None


def test_validate_filename_rejects_dot_and_dotdot() -> None:
    assert validate_filename(".") is not None
    assert validate_filename("..") is not None


def test_validate_filename_rejects_path_separator() -> None:
    assert validate_filename("a/b") is not None


def test_validate_filename_accepts_normal_names() -> None:
    assert validate_filename("notes.txt") is None
    assert validate_filename("My Folder") is None


def test_create_folder_creates_a_new_directory(tmp_path: Path) -> None:
    created = create_folder(tmp_path, "new-folder")

    assert created == tmp_path / "new-folder"
    assert created.is_dir()


def test_create_folder_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        create_folder(tmp_path, "")


def test_create_folder_raises_if_already_exists(tmp_path: Path) -> None:
    (tmp_path / "existing").mkdir()

    with pytest.raises(FileExistsError):
        create_folder(tmp_path, "existing")


def test_rename_entry_renames_a_file(tmp_path: Path) -> None:
    original = tmp_path / "old.txt"
    original.write_text("data")

    renamed = rename_entry(original, "new.txt")

    assert renamed == tmp_path / "new.txt"
    assert renamed.exists()
    assert not original.exists()


def test_rename_entry_rejects_invalid_name(tmp_path: Path) -> None:
    original = tmp_path / "old.txt"
    original.write_text("data")

    with pytest.raises(ValueError):
        rename_entry(original, "")

    assert original.exists()


def test_rename_entry_raises_if_target_already_exists(tmp_path: Path) -> None:
    original = tmp_path / "old.txt"
    original.write_text("data")
    (tmp_path / "taken.txt").write_text("other")

    with pytest.raises(FileExistsError):
        rename_entry(original, "taken.txt")

    assert original.exists()
