from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import db_session
from app.models import LoginSession, User

COOKIE_NAME = "session"
SESSION_DAYS = 7
PASSWORD_HASH_ROUNDS = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PASSWORD_HASH_ROUNDS
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), PASSWORD_HASH_ROUNDS
    )
    return hmac.compare_digest(check.hex(), digest)


def create_login(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        LoginSession(
            token=token,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
        )
    )
    db.commit()
    return token


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
        secure=False,
        max_age=SESSION_DAYS * 24 * 60 * 60,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


def user_from_cookie(db: Session, token: str) -> User | None:
    login = db.scalars(select(LoginSession).where(LoginSession.token == token)).first()
    if login is None:
        return None
    expires = login.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        db.delete(login)
        db.commit()
        return None
    return db.get(User, login.user_id)


def delete_login(db: Session, token: str | None) -> None:
    if not token:
        return
    login = db.scalars(select(LoginSession).where(LoginSession.token == token)).first()
    if login is not None:
        db.delete(login)
        db.commit()


def current_user(
    session_cookie: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(db_session),
) -> User:
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not signed in")
    user = user_from_cookie(db, session_cookie)
    if user is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user
