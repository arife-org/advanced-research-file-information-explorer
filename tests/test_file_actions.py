from pathlib import Path

import pytest

from arife.gui.file_actions import reveal_command, reveal_label, trash_available


def test_reveal_command_macos_selects_the_file(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("x")

    assert reveal_command(target, platform="darwin") == ["open", "-R", str(target)]


def test_reveal_command_windows_selects_the_file(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("x")

    assert reveal_command(target, platform="win32") == ["explorer", f"/select,{target}"]


def test_reveal_command_linux_opens_parent_folder_for_a_file(tmp_path: Path) -> None:
    target = tmp_path / "file.txt"
    target.write_text("x")

    assert reveal_command(target, platform="linux") == ["xdg-open", str(tmp_path)]


def test_reveal_command_linux_opens_itself_for_a_directory(tmp_path: Path) -> None:
    assert reveal_command(tmp_path, platform="linux") == ["xdg-open", str(tmp_path)]


def test_reveal_command_unsupported_platform_returns_none(tmp_path: Path) -> None:
    assert reveal_command(tmp_path, platform="freebsd13") is None


def test_reveal_label_matches_platform_terminology() -> None:
    assert reveal_label(platform="darwin") == "Reveal in Finder"
    assert reveal_label(platform="win32") == "Show in Explorer"
    assert reveal_label(platform="linux") == "Open Containing Folder"


def test_trash_available_returns_a_bool() -> None:
    assert isinstance(trash_available(), bool)


def test_move_to_trash_removes_the_file(tmp_path: Path) -> None:
    pytest.importorskip("send2trash")
    from arife.gui.file_actions import move_to_trash

    target = tmp_path / "doomed.txt"
    target.write_text("bye")

    move_to_trash(target)

    assert not target.exists()
