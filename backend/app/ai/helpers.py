from __future__ import annotations

import json
from typing import Any

from openrouter.types import UNSET


def tool_calls_on(message: Any) -> list[Any]:
    calls = getattr(message, "tool_calls", None)
    if calls is UNSET or calls is None:
        return []
    return list(calls)


def tool_name(call: Any) -> str:
    if isinstance(call, dict):
        fn = call.get("function") or {}
        return str(fn.get("name") or call.get("name") or "")
    fn = getattr(call, "function", None)
    if fn is not None:
        return str(getattr(fn, "name", "") or "")
    return str(getattr(call, "name", "") or "")


def tool_call_id(call: Any) -> str:
    if isinstance(call, dict):
        return str(call.get("id") or "")
    return str(getattr(call, "id", "") or "")


def tool_arguments(call: Any) -> dict[str, Any]:
    if isinstance(call, dict):
        fn = call.get("function") or {}
        raw = fn.get("arguments") or call.get("arguments") or {}
    else:
        fn = getattr(call, "function", None)
        raw = getattr(fn, "arguments", None) if fn is not None else getattr(call, "arguments", None)
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    parsed: Any = json.loads(raw)
    if not isinstance(parsed, dict):
        return {}
    return parsed


def as_dict(value: Any) -> dict[str, Any]:
    """Turn an SDK object into a plain dict."""
    if isinstance(value, dict):
        return value
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        payload = dump(exclude_none=True, exclude_unset=True)
        if isinstance(payload, dict):
            return payload
    return {}


def message_text(message: Any) -> str:
    content = getattr(message, "content", None)
    if content is UNSET or content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(getattr(item, "text", "") or ""))
        return " ".join(part for part in parts if part).strip()
    return str(content or "").strip()


def json_object_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("reply must be a JSON object")
    data = json.loads(cleaned[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("reply must be a JSON object")
    return data
