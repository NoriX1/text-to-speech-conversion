from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import SETTINGS


class FakeEngine:
    def __init__(self):
        self.device = "cpu"
        self.backend = "piper"
        self.last_error = None
        self.ready = True

    def load(self) -> None:
        self.ready = True

    def list_voices(self):
        class Voice:
            def __init__(self, name: str):
                self.name = name

        return [Voice("ru_RU-ruslan-medium"), Voice("ru_RU-irina-medium")]

    def synthesize(self, *, text: str, language: str, voice: str | None, speed: float | None) -> bytes:
        return f"{text}|{language}|{voice}|{speed}".encode("utf-8")


def test_voices_endpoint(monkeypatch):
    from app import main as app_main

    monkeypatch.setattr(app_main, "tts_engine", FakeEngine())
    with TestClient(app) as client:
        response = client.get("/v1/voices")

    assert response.status_code == 200
    assert response.json() == {
        "count": 2,
        "voices": ["ru_RU-ruslan-medium", "ru_RU-irina-medium"],
    }


def test_tts_endpoint_returns_wav(monkeypatch):
    from app import main as app_main

    monkeypatch.setattr(app_main, "tts_engine", FakeEngine())
    with TestClient(app) as client:
        response = client.post("/v1/tts", json={"text": "hello", "format": "wav"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content.startswith(b"hello|")


def test_tts_rejects_text_longer_than_settings_limit(monkeypatch):
    from app import main as app_main

    monkeypatch.setattr(app_main, "tts_engine", FakeEngine())
    payload = {"text": "x" * (SETTINGS.tts_max_text_length + 1), "format": "wav"}
    with TestClient(app) as client:
        response = client.post("/v1/tts", json=payload)

    assert response.status_code == 422
