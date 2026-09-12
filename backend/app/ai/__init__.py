from __future__ import annotations

import logging
from pathlib import Path

from google.genai.errors import APIError as GeminiAPIError
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.ai.env import AIError as AIError
from app.ai.image import render_edited_image
from app.ai.tools import read_profile_via_tool
from app.schemas import Profile

log = logging.getLogger("photogen.ai")


def describe_taste_for_prompt(profile: Profile) -> str:
    colors = ", ".join(profile.favorite_colors)
    return f"{profile.username}; favorite colors {colors}; hobbies {profile.hobbies}; {profile.notes}".strip()


def edit_photo_with_taste(db: Session, user_id: int, image_path: Path, prompt: str) -> bytes:
    try:
        profile = read_profile_via_tool(db, user_id)
        instruction = f"{prompt}. Match this taste: {describe_taste_for_prompt(profile)}"
        log.info("edit instruction ready (%s chars)", len(instruction))
        return render_edited_image(image_path, instruction)
    except (OpenAIError, GeminiAPIError) as exc:
        raise AIError(str(exc) or "Model request failed") from exc
