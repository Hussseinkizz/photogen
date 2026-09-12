from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.db import ROOT

ORIGINALS_DIR = ROOT / "uploads"
EDITS_DIR = ROOT / "generated"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_UPLOAD_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def ensure_image_folders() -> None:
    ORIGINALS_DIR.mkdir(parents=True, exist_ok=True)
    EDITS_DIR.mkdir(parents=True, exist_ok=True)


def new_image_filename(suffix: str) -> str:
    return f"{uuid.uuid4().hex}{suffix}"


def store_original_upload(file: UploadFile) -> str:
    content_type = (file.content_type or "").lower()
    suffix = ALLOWED_UPLOAD_TYPES.get(content_type)
    if suffix is None:
        raise HTTPException(status_code=400, detail="Use a jpeg, png, or webp image")
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Image must be 10MB or smaller")
    name = new_image_filename(suffix)
    (ORIGINALS_DIR / name).write_bytes(data)
    return name


def fork_source_into_originals(filename: str, from_edits: bool) -> str:
    folder = EDITS_DIR if from_edits else ORIGINALS_DIR
    source = folder / filename
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Source photo file is missing")
    name = new_image_filename(source.suffix)
    shutil.copy2(source, ORIGINALS_DIR / name)
    return name


def store_edited_image(image_bytes: bytes) -> str:
    name = new_image_filename(".png")
    (EDITS_DIR / name).write_bytes(image_bytes)
    return name


def original_file_path(filename: str) -> Path:
    return ORIGINALS_DIR / filename
