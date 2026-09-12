from __future__ import annotations

import base64
from collections.abc import Iterable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, cast

from app.ai.env import AIError, image_client, image_model_name
from app.ai.helpers import as_dict


def image_as_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    media = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime = media.get(suffix, "image/jpeg")
    encoded = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{encoded}"


def base64_from_result(result: Any) -> str:
    data = getattr(result, "data", None)
    if data:
        first = data[0]
        if isinstance(first, dict):
            return str(first.get("b64_json") or "")
        return str(getattr(first, "b64_json", "") or "")
    payload = as_dict(result)
    items = payload.get("data") or []
    if items and isinstance(items[0], dict):
        return str(items[0].get("b64_json") or "")
    raise AIError("Image model did not return image bytes")


def generate_image(path: Path, instruction: str) -> bytes:
    with image_client() as client:
        result = client.images.generate(
            model=image_model_name(),
            prompt=instruction,
            input_references=cast(
                Any,
                [{"type": "image_url", "image_url": {"url": image_as_data_url(path)}}],
            ),
            stream=False,
            output_format="png",
            timeout_ms=120_000,
        )
        if hasattr(result, "__enter__"):
            events: list[object] = []
            with cast(AbstractContextManager[Iterable[object]], result) as stream:
                events.extend(stream)
            for event in reversed(events):
                encoded = as_dict(event).get("b64_json")
                if encoded:
                    return base64.b64decode(encoded)
            raise AIError("Image stream finished without image bytes")
        encoded = base64_from_result(result)
        if not encoded:
            raise AIError("Image model did not return image bytes")
        return base64.b64decode(encoded)
