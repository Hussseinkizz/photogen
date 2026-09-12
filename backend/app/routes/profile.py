from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import current_user
from app.db import get_db
from app.models import User
from app.profile import load_user_profile
from app.schemas import Profile

router = APIRouter()


@router.get("/profile", response_model=Profile)
def read_own_profile(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> Profile:
    result = load_user_profile(db, user.id)
    if result is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return result
