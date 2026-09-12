from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User
from app.schemas import Profile


def load_user_profile(db: Session, user_id: int) -> Profile | None:
    user = db.get(User, user_id)
    if user is None:
        return None
    return Profile(
        id=user.id,
        username=user.username,
        favorite_colors=list(user.favorite_colors or []),
        hobbies=user.hobbies,
        notes=user.notes,
    )
