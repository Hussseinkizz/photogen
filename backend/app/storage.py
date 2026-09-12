from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.db import ROOT

UPLOAD_DIR = ROOT / "uploads"
GENERATED_DIR = ROOT / "generated"
MAX_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def ensure_folders() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def new_filename(suffix: str) -> str:
    return f"{uuid.uuid4().hex}{suffix}"


def save_upload(file: UploadFile) -> str:
    content_type = (file.content_type or "").lower()
    suffix = ALLOWED_TYPES.get(content_type)
    if suffix is None:
        raise HTTPException(status_code=400, detail="Use a jpeg, png, or webp image")
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty image")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image must be 10MB or smaller")
    name = new_filename(suffix)
    (UPLOAD_DIR / name).write_bytes(data)
    return name


def copy_to_uploads(filename: str, from_generated: bool) -> str:
    folder = GENERATED_DIR if from_generated else UPLOAD_DIR
    source = folder / filename
    if not source.is_file():
        raise HTTPException(status_code=404, detail="Source photo file is missing")
    name = new_filename(source.suffix)
    shutil.copy2(source, UPLOAD_DIR / name)
    return name


def save_generated_image(image_bytes: bytes) -> str:
    name = new_filename(".png")
    (GENERATED_DIR / name).write_bytes(image_bytes)
    return name


def uploaded_path(filename: str) -> Path:
    return UPLOAD_DIR / filename
