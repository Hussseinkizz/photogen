from __future__ import annotations

import json
import logging
from typing import Any, cast

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.env import AIError, chat_client, chat_model_name
from app.ai.helpers import (
    chat_message_text,
    chat_tool_call_id,
    chat_tool_calls,
    chat_tool_name,
    sdk_to_dict,
)
from app.ai.tools.get_profile import (
    PROFILE_LOOKUP_TOOL_DEF,
    PROFILE_TOOL_SYSTEM_PROMPT,
    execute_profile_lookup_tool,
    parse_profile_from_text,
)
from app.schemas import Profile

log = logging.getLogger("photogen.ai")

PROFILE_READ_ATTEMPTS = 3

MODEL_TOOLS = [PROFILE_LOOKUP_TOOL_DEF]


def dispatch_model_tool(db: Session, call: Any) -> dict[str, Any]:
    name = chat_tool_name(call)
    if name == "get_profile":
        return execute_profile_lookup_tool(db, call)
    raise AIError(f"Unknown tool: {name}")


def read_profile_via_tool(db: Session, profile_id: int) -> Profile:
    """Tool call get_profile(profile_id), then validate the model's JSON as Profile. 3 tries."""
    messages: list[Any] = [
        {"role": "system", "content": PROFILE_TOOL_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"The profile id is {profile_id}. Fetch it and return the profile JSON.",
        },
    ]
    tries = 0
    rounds = 0
    called_tool = False
    with chat_client() as client:
        while tries < PROFILE_READ_ATTEMPTS:
            rounds += 1
            if rounds > 8:
                raise AIError("Profile tool loop ran too long")
            result = client.chat.completions.create(
                model=chat_model_name(),
                messages=cast(Any, messages),
                tools=cast(Any, MODEL_TOOLS),
                timeout=120,
            )
            message = result.choices[0].message
            calls = chat_tool_calls(message)
            if calls:
                messages.append(sdk_to_dict(message))
                for call in calls:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": chat_tool_call_id(call),
                            "content": json.dumps(dispatch_model_tool(db, call)),
                        }
                    )
                    called_tool = True
                continue
            if not called_tool:
                messages.append(sdk_to_dict(message))
                messages.append(
                    {
                        "role": "user",
                        "content": f"Call get_profile with profile_id {profile_id} first.",
                    }
                )
                tries += 1
                continue
            try:
                profile = parse_profile_from_text(chat_message_text(message))
            except (ValueError, ValidationError, json.JSONDecodeError) as exc:
                tries += 1
                log.info("profile JSON failed try %s: %s", tries, exc)
                messages.append(sdk_to_dict(message))
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
