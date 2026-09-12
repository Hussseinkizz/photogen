from __future__ import annotations

import base64
from pathlib import Path

from app.ai.env import AIError, image_client, image_model_name

SOURCE_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def render_edited_image(path: Path, instruction: str) -> bytes:
    encoded_source = base64.b64encode(path.read_bytes()).decode()
    mime = SOURCE_MIME_TYPES.get(path.suffix.lower(), "image/jpeg")
    interaction = image_client().interactions.create(
        model=image_model_name(),
        input=[
            {"type": "text", "text": instruction},
            {"type": "image", "data": encoded_source, "mime_type": mime},
        ],
        response_format={"type": "image"},
        timeout=120,
    )
    for step in interaction.steps or []:
        if getattr(step, "type", None) != "model_output":
            continue
        for block in getattr(step, "content", None) or []:
            if getattr(block, "type", None) == "image" and getattr(block, "data", None):
                return base64.b64decode(str(block.data))
    raise AIError("Image model did not return image bytes")
