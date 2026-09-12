from __future__ import annotations

import json
import logging
from typing import Any, cast

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.env import AIError, chat_client, chat_model_name
from app.ai.helpers import as_dict, message_text, tool_call_id, tool_calls_on, tool_name
from app.ai.tools.get_profile import (
    GET_PROFILE_TOOL,
    SYSTEM_PROMPT,
    profile_from_text,
    run_get_profile_tool,
)
from app.schemas import Profile

log = logging.getLogger("photogen.ai")

PROFILE_TRIES = 3

TOOLS = [GET_PROFILE_TOOL]


def run_tool(db: Session, call: Any) -> dict[str, Any]:
    name = tool_name(call)
    if name == "get_profile":
        return run_get_profile_tool(db, call)
    raise AIError(f"Unknown tool: {name}")


def fetch_profile_from_model(db: Session, profile_id: int) -> Profile:
    """Tool call get_profile(profile_id), then validate the model's JSON as Profile. 3 tries."""
    messages: list[Any] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"The profile id is {profile_id}. Fetch it and return the profile JSON.",
        },
    ]
    tries = 0
    rounds = 0
    called_tool = False
    with chat_client() as client:
        while tries < PROFILE_TRIES:
            rounds += 1
            if rounds > 8:
                raise AIError("Profile tool loop ran too long")
            result = client.chat.send(
                messages=cast(Any, messages),
                model=chat_model_name(),
                tools=cast(Any, TOOLS),
                stream=False,
                timeout_ms=120_000,
            )
            message = result.choices[0].message
            calls = tool_calls_on(message)
            if calls:
                messages.append(as_dict(message))
                for call in calls:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id(call),
                            "content": json.dumps(run_tool(db, call)),
                        }
                    )
                    called_tool = True
                continue
            if not called_tool:
                messages.append(as_dict(message))
                messages.append(
                    {
                        "role": "user",
                        "content": f"Call get_profile with profile_id {profile_id} first.",
                    }
                )
                tries += 1
                continue
            try:
                profile = profile_from_text(message_text(message))
            except (ValueError, ValidationError, json.JSONDecodeError) as exc:
                tries += 1
                log.info("profile JSON failed try %s: %s", tries, exc)
                messages.append(as_dict(message))
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"That is not a valid Profile. Errors: {exc}. "
                            "Return JSON only with id, username, favorite_colors, hobbies, notes."
                        ),
                    }
                )
                continue
            log.info("validated profile id=%s", profile.id)
            return profile
    raise AIError("Model did not return a valid profile after 3 tries")
