from __future__ import annotations

import os

from openrouter import OpenRouter


class AIError(Exception):
    pass


def read_env(name: str) -> str:
    return os.getenv(name, "").strip()


def require_env_setting(name: str) -> str:
    value = read_env(name)
    if not value:
        raise AIError(f"{name} is not set")
    return value


def openrouter_model_name() -> str:
    return require_env_setting("MODEL_NAME")


def openrouter_client() -> OpenRouter:
    url = read_env("MODEL_URL")
    if url:
        return OpenRouter(api_key=require_env_setting("MODEL_KEY"), server_url=url)
    return OpenRouter(api_key=require_env_setting("MODEL_KEY"))
