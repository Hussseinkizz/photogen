from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.env import AIError as AIError
from app.ai.image import generate_image
from app.ai.tools import fetch_profile_from_model
from app.schemas import Profile

log = logging.getLogger("photogen.ai")


def profile_as_text(profile: Profile) -> str:
    colors = ", ".join(profile.favorite_colors)
    return f"{profile.username}; favorite colors {colors}; hobbies {profile.hobbies}; {profile.notes}".strip()


def edit_image(db: Session, user_id: int, image_path: Path, prompt: str) -> bytes:
    profile = fetch_profile_from_model(db, user_id)
    instruction = f"{prompt}. Match this taste: {profile_as_text(profile)}"
    log.info("edit instruction ready (%s chars)", len(instruction))
    return generate_image(image_path, instruction)
