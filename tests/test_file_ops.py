from pathlib import Path

import pytest

from arife.core.file_ops import (
    copy_entry,
    create_folder,
    move_entry,
    rename_entry,
    unique_destination,
    validate_filename,
)


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


def test_unique_destination_returns_name_as_is_when_free(tmp_path: Path) -> None:
    assert unique_destination(tmp_path, "report.txt") == tmp_path / "report.txt"


def test_unique_destination_appends_copy_suffix_on_collision(tmp_path: Path) -> None:
    (tmp_path / "report.txt").write_text("data")

    assert unique_destination(tmp_path, "report.txt") == tmp_path / "report (copy).txt"


def test_unique_destination_increments_counter_on_repeated_collision(tmp_path: Path) -> None:
    (tmp_path / "report.txt").write_text("data")
    (tmp_path / "report (copy).txt").write_text("data")

    assert unique_destination(tmp_path, "report.txt") == tmp_path / "report (copy 2).txt"


def test_copy_entry_copies_a_file_to_another_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    original = source / "notes.txt"
    original.write_text("data")

    copied = copy_entry(original, destination)

    assert copied == destination / "notes.txt"
    assert copied.read_text() == "data"
    assert original.exists()  # copy, not move


def test_copy_entry_duplicates_in_place_with_a_copy_suffix(tmp_path: Path) -> None:
    original = tmp_path / "notes.txt"
    original.write_text("data")

    copied = copy_entry(original, tmp_path)

    assert copied == tmp_path / "notes (copy).txt"
    assert copied.read_text() == "data"
    assert original.exists()


def test_copy_entry_copies_a_directory_recursively(tmp_path: Path) -> None:
    source_dir = tmp_path / "source_dir"
    source_dir.mkdir()
    (source_dir / "inner.txt").write_text("data")
    destination = tmp_path / "destination"
    destination.mkdir()

    copied = copy_entry(source_dir, destination)

    assert copied == destination / "source_dir"
    assert (copied / "inner.txt").read_text() == "data"


def test_move_entry_moves_a_file_to_another_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    original = source / "notes.txt"
    original.write_text("data")

    moved = move_entry(original, destination)

    assert moved == destination / "notes.txt"
    assert moved.read_text() == "data"
    assert not original.exists()


def test_move_entry_is_a_noop_when_already_in_destination(tmp_path: Path) -> None:
    original = tmp_path / "notes.txt"
    original.write_text("data")

    moved = move_entry(original, tmp_path)

    assert moved == original
    assert original.exists()


def test_move_entry_raises_if_target_already_exists(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    original = source / "notes.txt"
    original.write_text("data")
    (destination / "notes.txt").write_text("other")

    with pytest.raises(FileExistsError):
        move_entry(original, destination)

    assert original.exists()
