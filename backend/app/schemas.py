from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    favorite_colors: list[str] = Field(min_length=1, max_length=3)
    hobbies: str = Field(min_length=1, max_length=200)
    notes: str = Field(default="", max_length=200)

    @field_validator("username")
    @classmethod
    def letters_and_numbers_only(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.isalnum():
            raise ValueError("username must be letters and numbers only")
        return cleaned

    @field_validator("favorite_colors")
    @classmethod
    def trim_colors(cls, value: list[str]) -> list[str]:
        colors = [item.strip() for item in value if item.strip()]
        if not colors:
            raise ValueError("add at least one color")
        return colors[:3]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class Profile(BaseModel):
    id: int
    username: str
    favorite_colors: list[str]
    hobbies: str
    notes: str


class GeneratedVersion(BaseModel):
    url: str
    prompt: str


class PhotoResponse(BaseModel):
    id: int
    original_url: str
    generated: list[GeneratedVersion]
    parent_id: int | None
    created_at: str
