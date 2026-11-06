"""Tests for the background image-thumbnail loader."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

pytest.importorskip("PySide6")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_is_supported_image_recognizes_common_formats(qapp):
    from arife.gui.worker import is_supported_image

    assert is_supported_image(".png")
    assert is_supported_image(".PNG")
    assert not is_supported_image(".csv")
    assert not is_supported_image(".zip")


def test_load_thumbnail_returns_none_for_non_image(qapp, tmp_path):
    from arife.gui.worker import load_thumbnail

    text_file = tmp_path / "notes.txt"
    text_file.write_text("not an image")

    assert load_thumbnail(text_file, max_size=100) is None


def test_load_thumbnail_scales_down_oversized_images(qapp, tmp_path):
    from PySide6.QtGui import QImage

    from arife.gui.worker import load_thumbnail

    image_path = tmp_path / "big.png"
    original = QImage(400, 200, QImage.Format.Format_RGB32)
    original.fill(0xFF0000)
    assert original.save(str(image_path), "PNG")

    thumbnail = load_thumbnail(image_path, max_size=100)

    assert thumbnail is not None
    assert max(thumbnail.width(), thumbnail.height()) <= 100


def test_load_thumbnail_leaves_small_images_unscaled(qapp, tmp_path):
    from PySide6.QtGui import QImage

    from arife.gui.worker import load_thumbnail

    image_path = tmp_path / "small.png"
    original = QImage(50, 30, QImage.Format.Format_RGB32)
    original.fill(0x00FF00)
    assert original.save(str(image_path), "PNG")

    thumbnail = load_thumbnail(image_path, max_size=220)

    assert thumbnail is not None
    assert thumbnail.width() == 50
    assert thumbnail.height() == 30
