from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import db_session
from app.models import User
from app.profile import get_profile
from app.schemas import Profile

router = APIRouter()


@router.get("/profile", response_model=Profile)
def profile(
    db: Session = Depends(db_session),
    user: User = Depends(current_user),
) -> Profile:
    result = get_profile(db, user.id)
    if result is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return result
