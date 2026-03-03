from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
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
        return text

