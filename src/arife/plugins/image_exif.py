"""Plugin extracting image dimensions and EXIF metadata."""
from __future__ import annotations

from arife.core.models import FileEntry
from arife.core.plugin import InfoPlugin

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}

# A small, commonly useful subset of EXIF tag IDs, keyed by name for readability.
_EXIF_TAGS_OF_INTEREST = {
    "Make": 271,
    "Model": 272,
    "DateTimeOriginal": 36867,
    "ExposureTime": 33434,
    "FNumber": 33437,
    "ISOSpeedRatings": 34855,
    "FocalLength": 37386,
}


class ImageExifPlugin(InfoPlugin):
    id = "image_exif"
    display_name = "Image / EXIF"
    description = "Shows image dimensions, format and EXIF camera metadata."

    def is_available(self) -> bool:
        try:
            import PIL  # noqa: F401
        except ImportError:
            return False
        return True

    def supports(self, entry: FileEntry) -> bool:
        return not entry.is_dir and entry.suffix in _IMAGE_SUFFIXES

    def extract(self, entry: FileEntry) -> dict[str, object]:
        from PIL import Image

        values: dict[str, object] = {}
        with Image.open(entry.path) as img:
            values["Format"] = img.format or "-"
            values["Dimensions"] = f"{img.width} x {img.height}"
            values["Color mode"] = img.mode

            exif = img.getexif()
            if exif:
                for name, tag_id in _EXIF_TAGS_OF_INTEREST.items():
                    if tag_id in exif:
                        values[name] = str(exif[tag_id])

        return values
