from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.config import get_settings


SETTINGS = get_settings()


class TTSRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str = Field(default="ru", min_length=2, max_length=8)
    voice: str | None = Field(default=None, min_length=1, max_length=128)
    speed: float | None = Field(default=None, ge=0.5, le=2.0)
    format: str = Field(default="wav")

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized != "wav":
            raise ValueError("Only 'wav' format is supported in MVP.")
        return normalized

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Text must not be empty.")
        limit = SETTINGS.tts_max_text_length
        if len(text) > limit:
            raise ValueError(f"Text is too long: {len(text)} > {limit}.")
        return text
