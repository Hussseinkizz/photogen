from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import AIError, edit_photo_with_taste
from app.auth import current_user
from app.db import get_db
from app.models import Photo, User
from app.photos import editable_source_path, latest_edit_filename
from app.schemas import PhotoEdit, PhotoResponse
from app.storage import (
    fork_source_into_originals,
    store_edited_image,
    store_original_upload,
)

log = logging.getLogger("photogen")
router = APIRouter(prefix="/photos")


def present_photo(photo: Photo) -> PhotoResponse:
    edits = [
        PhotoEdit(url=f"/generated/{item['path']}", prompt=item.get("prompt") or "")
        for item in (photo.edits or [])
        if item.get("path")
    ]
    created = photo.created_at.isoformat() if isinstance(photo.created_at, datetime) else str(photo.created_at)
    return PhotoResponse(
        id=photo.id,
        original_url=f"/uploads/{photo.original_path}",
        generated=edits,
        parent_id=photo.parent_id,
        created_at=created,
    )


def append_photo_edit(db: Session, user: User, photo: Photo, prompt: str) -> PhotoResponse:
    try:
        image_bytes = edit_photo_with_taste(db, user.id, editable_source_path(photo), prompt)
        edits = list(photo.edits or [])
        edits.append({"path": store_edited_image(image_bytes), "prompt": prompt})
        photo.edits = edits
        db.commit()
        db.refresh(photo)
    except AIError as exc:
        status = 503 if "is not set" in str(exc) else 502
        log.exception("image edit failed")
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    return present_photo(photo)


def require_owned_photo(db: Session, photo_id: int, user_id: int) -> Photo:
    photo = db.get(Photo, photo_id)
    if photo is None or photo.user_id != user_id:
        raise HTTPException(status_code=404, detail="Photo not found")
    return photo


@router.get("", response_model=list[PhotoResponse])
def list_photos(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> list[PhotoResponse]:
    photos = db.scalars(
        select(Photo).where(Photo.user_id == user.id).order_by(Photo.id.desc())
    ).all()
    return [present_photo(photo) for photo in photos]


@router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PhotoResponse:
    return present_photo(require_owned_photo(db, photo_id, user.id))


@router.post("", response_model=PhotoResponse)
def create_photo(
    prompt: str = Form(..., min_length=1, max_length=500),
    image: UploadFile | None = File(default=None),
    parent_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PhotoResponse:
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    if image is not None and image.filename:
        original_name = store_original_upload(image)
        parent = None
    elif parent_id is not None:
        parent_photo = require_owned_photo(db, parent_id, user.id)
        latest = latest_edit_filename(parent_photo)
        if latest:
            original_name = fork_source_into_originals(latest, from_edits=True)
        else:
            original_name = fork_source_into_originals(parent_photo.original_path, from_edits=False)
        parent = parent_id
    else:
        raise HTTPException(status_code=400, detail="Upload an image or pass parent_id")

    photo = Photo(
        user_id=user.id,
        original_path=original_name,
        edits=[],
        parent_id=parent,
        created_at=datetime.now(timezone.utc),
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return append_photo_edit(db, user, photo, prompt)


@router.post("/{photo_id}", response_model=PhotoResponse)
def add_photo_version(
    photo_id: int,
    prompt: str = Form(..., min_length=1, max_length=500),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PhotoResponse:
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    return append_photo_edit(db, user, require_owned_photo(db, photo_id, user.id), prompt)
