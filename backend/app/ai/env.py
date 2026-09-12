from __future__ import annotations

import os

from google import genai
from openai import OpenAI

GOOGLE_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class AIError(Exception):
    pass


def read_env(name: str) -> str:
    return os.getenv(name, "").strip()


def require_env_setting(name: str) -> str:
    value = read_env(name)
    if not value:
        raise AIError(f"{name} is not set")
    return value


def gemini_api_key() -> str:
    return require_env_setting("GEMINI_API_KEY")


def chat_model_name() -> str:
    return read_env("CHAT_MODEL_NAME") or "gemini-2.5-flash"


def image_model_name() -> str:
    return read_env("IMAGE_MODEL_NAME") or "gemini-3.1-flash-image"


def chat_client() -> OpenAI:
    # Profile tool loop runs on the OpenAI-compatible Gemini endpoint.
    return OpenAI(
        api_key=gemini_api_key(),
        base_url=read_env("MODEL_URL") or GOOGLE_OPENAI_BASE_URL,
    )


def image_client() -> genai.Client:
    return genai.Client(api_key=gemini_api_key())
