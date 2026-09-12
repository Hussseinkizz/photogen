from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    create_user_session,
    current_user,
    delete_user_session,
    hash_password,
    set_session_cookie,
    verify_password,
)
from app.db import get_db
from app.models import User
from app.profile import load_user_profile
from app.schemas import LoginRequest, Profile, RegisterRequest

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=Profile)
def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> Profile:
    existing = db.scalars(select(User).where(User.username == request.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ustatus_codesername already taken")
    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        favorite_colors=request.favorite_colors,
        hobbies=request.hobbies.strip(),
        notes=request.notes.strip(),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    set_session_cookie(response, create_user_session(db, user.id))
    profile = load_user_profile(db, user.id)
    assert profile is not None
    return profile


@router.post("/login", response_model=Profile)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> Profile:
    user = db.scalars(select(User).where(User.username == request.username.strip())).first()
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    set_session_cookie(response, create_user_session(db, user.id))
    profile = load_user_profile(db, user.id)
    assert profile is not None
    return profile


@router.post("/logout")
def logout(
    response: Response,
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, bool]:
    del user
    delete_user_session(db, session_cookie)
    clear_session_cookie(response)
    return {"ok": True}
