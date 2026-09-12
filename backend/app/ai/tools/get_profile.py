from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.ai.helpers import json_object_from_text, tool_arguments
from app.profile import get_profile
from app.schemas import Profile

log = logging.getLogger("photogen.ai")

GET_PROFILE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_profile",
        "description": "Load a user profile by id. Pass the profile_id from the prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "profile_id": {
                    "type": "integer",
                    "description": "The profile id given in the user prompt",
                }
            },
            "required": ["profile_id"],
        },
    },
}

SYSTEM_PROMPT = (
    "Call get_profile with the profile_id from the user message. "
    "Then reply with JSON only, no markdown, matching this shape: "
    '{"id": 1, "username": "name", "favorite_colors": ["color"], "hobbies": "text", "notes": "text"}. '
    "Do not invent a profile. Use only what the tool returns."
)


def profile_from_text(text: str) -> Profile:
    return Profile(**json_object_from_text(text))


def run_get_profile_tool(db: Session, call: Any) -> dict[str, Any]:
    args = tool_arguments(call)
    raw_id = args.get("profile_id")
    if raw_id is None:
        return {"error": "profile_id must be an integer"}
    try:
        profile_id = int(raw_id)
    except (TypeError, ValueError):
        return {"error": "profile_id must be an integer"}
    log.info("tool call: get_profile profile_id=%s", profile_id)
    profile = get_profile(db, profile_id)
    if profile is None:
        return {"error": "profile not found"}
    return {
        "id": profile.id,
        "username": profile.username,
        "favorite_colors": profile.favorite_colors,
        "hobbies": profile.hobbies,
        "notes": profile.notes,
    }
