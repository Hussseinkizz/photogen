from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db import Base


class User(Base):
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    favorite_colors: Mapped[list[str]] = mapped_column(JSON, default=list)
    hobbies: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserSession(Base):
    __tablename__: str = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Photo(Base):
    __tablename__: str = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    original_path: Mapped[str] = mapped_column(String(255))
    # DB column stays "generated" so existing sqlite files keep working;
    # Python code uses `edits` to distinguish DB rows from rendered files.
    edits: Mapped[list[dict[str, str]]] = mapped_column("generated", JSON, default=list)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("photos.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
