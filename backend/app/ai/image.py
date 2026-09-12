from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, cast

from app.ai.env import AIError, openrouter_client, openrouter_model_name
from app.ai.helpers import sdk_to_dict


def encode_source_as_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    media = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = media.get(suffix, "image/jpeg")
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def decode_b64_from_image_result(result: Any) -> str:
    data = getattr(result, "data", None)
    if data:
        first = data[0]
        if isinstance(first, dict):
            return str(first.get("b64_json") or "")
        return str(getattr(first, "b64_json", "") or "")
    payload = sdk_to_dict(result)
    items = payload.get("data") or []
    if items and isinstance(items[0], dict):
        return str(items[0].get("b64_json") or "")
    raise AIError("Image model did not return image bytes")


def render_edited_image(path: Path, instruction: str) -> bytes:
    with openrouter_client() as client:
        result = client.images.generate(
            model=openrouter_model_name(),
            prompt=instruction,
            input_references=cast(
                Any,
                [{"type": "image_url", "image_url": {"url": encode_source_as_data_url(path)}}],
            ),
            output_format="png",
            timeout_ms=120_000,
        )
        encoded = decode_b64_from_image_result(result)
        if not encoded:
            raise AIError("Image model did not return image bytes")
        return base64.b64decode(encoded)
