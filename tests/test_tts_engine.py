from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MethodType

from app.tts_engine import TTSEngine, VoicePreset


@dataclass
class DummySettings:
    tts_backend: str = "auto"
    tts_device: str = "cpu"
    tts_model_name: str = "dummy"
    voices_dir_path: Path = Path(".")
    piper_voices_dir_path: Path = Path(".")


def test_list_voices_uses_backend_selected_during_load(tmp_path: Path):
    piper_dir = tmp_path / "piper"
    piper_dir.mkdir(parents=True, exist_ok=True)
    (piper_dir / "ru-test.onnx").write_bytes(b"x")
    (piper_dir / "ru-test.onnx.json").write_text("{}", encoding="utf-8")

    engine = TTSEngine(
        settings=DummySettings(
            tts_backend="auto",
            tts_device="cpu",
            piper_voices_dir_path=piper_dir,
            voices_dir_path=tmp_path,
        )
    )

    def fake_load(self: TTSEngine) -> None:
        self._backend = "piper"
        self._model = {"piper_ready": True}

    engine.load = MethodType(fake_load, engine)
    voices = engine.list_voices()
    assert voices == [VoicePreset(name="ru-test")]


def test_synthesize_uses_backend_selected_during_load(tmp_path: Path):
    engine = TTSEngine(
        settings=DummySettings(
            tts_backend="auto",
            tts_device="cpu",
            piper_voices_dir_path=tmp_path,
            voices_dir_path=tmp_path,
        )
    )

    def fake_load(self: TTSEngine) -> None:
        self._backend = "piper"
        self._model = {"piper_ready": True}

    def fake_synthesize_piper(self: TTSEngine, *, text: str, voice: str | None, speed: float | None) -> bytes:
        return f"{text}|{voice}|{speed}".encode("utf-8")

    engine.load = MethodType(fake_load, engine)
    engine._synthesize_piper = MethodType(fake_synthesize_piper, engine)

    audio = engine.synthesize(text="hello", language="ru", voice="demo", speed=1.25)
    assert audio == b"hello|demo|1.25"


def test_pyttsx3_speed_does_not_accumulate_between_calls(tmp_path: Path):
    class FakeEngine:
        def __init__(self):
            self.rate = 100

        def getProperty(self, name: str):
            if name == "rate":
                return self.rate
            return None

        def setProperty(self, name: str, value):
            if name == "rate":
                self.rate = int(value)

        def save_to_file(self, text: str, path: str):
            Path(path).write_bytes(text.encode("utf-8"))

        def runAndWait(self):
            return None

    engine = TTSEngine(
        settings=DummySettings(
            tts_backend="pyttsx3",
            tts_device="cpu",
            piper_voices_dir_path=tmp_path,
            voices_dir_path=tmp_path,
        )
    )
    fake_engine = FakeEngine()
    engine._backend = "pyttsx3"
    engine._model = fake_engine
    engine._pyttsx3_base_rate = 100

    first = engine._synthesize_pyttsx3(text="a", voice=None, speed=2.0)
    second = engine._synthesize_pyttsx3(text="b", voice=None, speed=2.0)

    assert first == b"a"
    assert second == b"b"
    assert fake_engine.rate == 200
