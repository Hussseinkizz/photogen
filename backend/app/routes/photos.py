from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import AIError, edit_image
from app.auth import current_user
from app.db import db_session
from app.models import Photo, User
from app.photos import latest_generated_path, source_image_path
from app.schemas import GeneratedVersion, PhotoResponse
from app.storage import copy_to_uploads, save_generated_image, save_upload

log = logging.getLogger("photogen")
router = APIRouter(prefix="/photos")


def photo_response(photo: Photo) -> PhotoResponse:
    versions = [
        GeneratedVersion(url=f"/generated/{item['path']}", prompt=item.get("prompt") or "")
        for item in (photo.generated or [])
        if item.get("path")
    ]
    created = photo.created_at.isoformat() if isinstance(photo.created_at, datetime) else str(photo.created_at)
    return PhotoResponse(
        id=photo.id,
        original_url=f"/uploads/{photo.original_path}",
        generated=versions,
        parent_id=photo.parent_id,
        created_at=created,
    )


def generate_new_version(db: Session, user: User, photo: Photo, prompt: str) -> PhotoResponse:
    try:
        image_bytes = edit_image(db, user.id, source_image_path(photo), prompt)
        versions = list(photo.generated or [])
        versions.append({"path": save_generated_image(image_bytes), "prompt": prompt})
        photo.generated = versions
        db.commit()
        db.refresh(photo)
    except AIError as exc:
        status = 503 if "is not set" in str(exc) else 502
        log.exception("image edit failed")
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return photo_response(photo)


def require_photo(db: Session, photo_id: int, user_id: int) -> Photo:
    photo = db.get(Photo, photo_id)
    if photo is None or photo.user_id != user_id:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.get("", response_model=list[PhotoResponse])
def list_photos(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
) -> list[PhotoResponse]:
    photos = db.scalars(
        select(Photo).where(Photo.user_id == user.id).order_by(Photo.id.desc())
    ).all()
    return [photo_response(photo) for photo in photos]


@router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo(
    photo_id: int,
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
) -> PhotoResponse:
    return photo_response(require_photo(db, photo_id, user.id))


@router.post("", response_model=PhotoResponse)
def create_photo(
    prompt: str = Form(..., min_length=1, max_length=500),
    image: UploadFile | None = File(default=None),
    parent_id: int | None = Form(default=None),
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
) -> PhotoResponse:
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    if image is not None and image.filename:
        original_name = save_upload(image)
        parent = None
    elif parent_id is not None:
        parent_photo = require_photo(db, parent_id, user.id)
        latest = latest_generated_path(parent_photo)
        if latest:
            original_name = copy_to_uploads(latest, from_generated=True)
        else:
            original_name = copy_to_uploads(parent_photo.original_path, from_generated=False)
        parent = parent_id
    else:
        raise HTTPException(status_code=400, detail="Upload an image or pass parent_id")

    photo = Photo(
        user_id=user.id,
        original_path=original_name,
        generated=[],
        parent_id=parent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return generate_new_version(db, user, photo, prompt)


@router.post("/{photo_id}", response_model=PhotoResponse)
def add_photo_version(
    photo_id: int,
    prompt: str = Form(..., min_length=1, max_length=500),
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
) -> PhotoResponse:
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    return generate_new_version(db, user, require_photo(db, photo_id, user.id), prompt)
