from __future__ import annotations

from pathlib import Path

from app.models import Photo
from app.storage import GENERATED_DIR, uploaded_path


def latest_generated_path(photo: Photo) -> str | None:
    versions = list(photo.generated or [])
    if not versions:
        return None
    return versions[-1].get("path")


def source_image_path(photo: Photo) -> Path:
    latest = latest_generated_path(photo)
    if latest:
        return GENERATED_DIR / latest
    return uploaded_path(photo.original_path)
