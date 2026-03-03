from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DeviceMode = Literal["auto", "cuda", "cpu"]
BackendMode = Literal["auto", "piper", "coqui", "pyttsx3"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")

    tts_device: DeviceMode = Field(default="auto", alias="TTS_DEVICE")
    tts_backend: BackendMode = Field(default="auto", alias="TTS_BACKEND")
    tts_model_name: str = Field(
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        alias="TTS_MODEL_NAME",
    )
    tts_max_text_length: int = Field(default=1000, alias="TTS_MAX_TEXT_LENGTH")
    tts_voices_dir: str = Field(default="voices", alias="TTS_VOICES_DIR")
    tts_default_language: str = Field(default="ru", alias="TTS_DEFAULT_LANGUAGE")
    tts_default_voice: str = Field(default="ru_RU-ruslan-medium", alias="TTS_DEFAULT_VOICE")
    tts_default_speed: float = Field(default=1.0, alias="TTS_DEFAULT_SPEED")
    tts_piper_voices_dir: str = Field(default="voices/piper", alias="TTS_PIPER_VOICES_DIR")

    @property
    def voices_dir_path(self) -> Path:
        return Path(self.tts_voices_dir).resolve()

    @property
    def piper_voices_dir_path(self) -> Path:
        return Path(self.tts_piper_voices_dir).resolve()


def get_settings() -> Settings:
    return Settings()
