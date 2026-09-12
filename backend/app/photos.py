from __future__ import annotations

from pathlib import Path

from app.models import Photo
from app.storage import EDITS_DIR, original_file_path


def latest_edit_filename(photo: Photo) -> str | None:
    edits = list(photo.edits or [])
    if not edits:
        return None
    return edits[-1].get("path")


def editable_source_path(photo: Photo) -> Path:
    latest = latest_edit_filename(photo)
    if latest:
        return EDITS_DIR / latest
    return original_file_path(photo.original_path)
