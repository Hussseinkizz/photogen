from __future__ import annotations

import os

from openrouter import OpenRouter


class AIError(Exception):
    pass


def env_value(name: str) -> str:
    return os.getenv(name, "").strip()


def require_env(name: str) -> str:
    value = env_value(name)
    if not value:
        raise AIError(f"{name} is not set")
    return value


def chat_model_name() -> str:
    return require_env("CHAT_MODEL_NAME")


def image_model_name() -> str:
    return require_env("IMAGE_MODEL_NAME")


def chat_client() -> OpenRouter:
    url = env_value("CHAT_MODEL_URL")
    if url:
        return OpenRouter(api_key=require_env("CHAT_MODEL_KEY"), server_url=url)
    return OpenRouter(api_key=require_env("CHAT_MODEL_KEY"))


def image_client() -> OpenRouter:
    url = env_value("IMAGE_MODEL_URL")
    if url:
        return OpenRouter(api_key=require_env("IMAGE_MODEL_KEY"), server_url=url)
    return OpenRouter(api_key=require_env("IMAGE_MODEL_KEY"))
