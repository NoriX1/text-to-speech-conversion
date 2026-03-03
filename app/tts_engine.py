from __future__ import annotations

import io
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import Settings


class TTSEngineError(RuntimeError):
    pass


@dataclass(frozen=True)
class VoicePreset:
    name: str
    speaker_wav: Path | None = None


def _cuda_available() -> bool:
    try:
        import onnxruntime  # type: ignore
    except Exception:
        return False
    providers = {p.lower() for p in onnxruntime.get_available_providers()}
    return "cudaexecutionprovider".lower() in providers


class TTSEngine:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._device = "cpu"
        self._backend = "pyttsx3"
        self._model: Any | None = None
        self._last_error: str | None = None
        self._pyttsx3_base_rate: int | None = None

    @property
    def device(self) -> str:
        return self._device

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def ready(self) -> bool:
        return self._model is not None

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def load(self) -> None:
        if self._model is not None:
            return

        requested_backend = self._settings.tts_backend

        if requested_backend in ("auto", "piper"):
            try:
                self._load_piper()
                return
            except Exception as exc:
                self._last_error = f"Piper backend unavailable: {exc}"
                if requested_backend == "piper":
                    raise TTSEngineError(self._last_error) from exc

        if requested_backend in ("auto", "coqui"):
            try:
                self._load_coqui()
                return
            except Exception as exc:
                self._last_error = f"Coqui backend unavailable: {exc}"
                if requested_backend == "coqui":
                    raise TTSEngineError(self._last_error) from exc

        self._load_pyttsx3()

    def list_voices(self) -> list[VoicePreset]:
        if not self.ready:
            self.load()

        if self._backend == "piper":
            return self._list_piper_voices()

        if self._backend == "coqui":
            voices_dir = self._settings.voices_dir_path
            voices_dir.mkdir(parents=True, exist_ok=True)
            return [
                VoicePreset(name=voice.stem, speaker_wav=voice)
                for voice in sorted(voices_dir.glob("*.wav"))
            ]

        engine = self._model
        if engine is None:
            return []
        voices = engine.getProperty("voices") or []
        return [VoicePreset(name=str(v.id)) for v in voices if getattr(v, "id", None)]

    def synthesize(
        self,
        *,
        text: str,
        language: str,
        voice: str | None,
        speed: float | None,
    ) -> bytes:
        if not self.ready:
            self.load()

        if self._backend == "piper":
            return self._synthesize_piper(text=text, voice=voice, speed=speed)
        if self._backend == "coqui":
            return self._synthesize_coqui(text=text, language=language, voice=voice, speed=speed)
        return self._synthesize_pyttsx3(text=text, voice=voice, speed=speed)

    def _load_piper(self) -> None:
        voices = self._list_piper_voices()
        if not voices:
            raise TTSEngineError(
                f"No Piper voices found in {self._settings.piper_voices_dir_path}. "
                "Run scripts/download_piper_voices.py to fetch voices."
            )
        self._backend = "piper"
        requested_device = self._settings.tts_device
        if requested_device == "cpu":
            self._device = "cpu"
        elif requested_device == "cuda":
            if _cuda_available():
                self._device = "cuda"
            else:
                self._device = "cpu"
                self._last_error = (
                    "TTS_DEVICE=cuda requested, but CUDAExecutionProvider is unavailable. "
                    "Falling back to CPU."
                )
        else:
            self._device = "cuda" if _cuda_available() else "cpu"
        self._model = {"piper_ready": True}

    def _list_piper_voices(self) -> list[VoicePreset]:
        piper_dir = self._settings.piper_voices_dir_path
        piper_dir.mkdir(parents=True, exist_ok=True)

        presets: list[VoicePreset] = []
        for model_path in sorted(piper_dir.glob("*.onnx")):
            config_path = Path(f"{model_path}.json")
            if config_path.exists():
                presets.append(VoicePreset(name=model_path.stem))
        return presets

    def _load_pyttsx3(self) -> None:
        try:
            import pyttsx3
        except Exception as exc:
            raise TTSEngineError(f"pyttsx3 import failed: {exc}") from exc

        self._model = pyttsx3.init()
        self._backend = "pyttsx3"
        self._device = "cpu"
        self._pyttsx3_base_rate = int(self._model.getProperty("rate"))

    def _load_coqui(self) -> None:
        try:
            from TTS.api import TTS
        except Exception as exc:
            raise TTSEngineError(f"TTS package import failed: {exc}") from exc

        requested_device = self._settings.tts_device
        if requested_device == "cpu":
            use_gpu = False
        elif requested_device == "cuda":
            use_gpu = True
        else:
            use_gpu = _cuda_available()

        try:
            self._model = TTS(
                model_name=self._settings.tts_model_name,
                progress_bar=False,
                gpu=use_gpu,
            )
            self._device = "cuda" if use_gpu else "cpu"
        except Exception as exc:
            if not use_gpu:
                raise TTSEngineError(f"Coqui model load failed: {exc}") from exc
            self._model = TTS(
                model_name=self._settings.tts_model_name,
                progress_bar=False,
                gpu=False,
            )
            self._device = "cpu"
            self._last_error = f"Coqui CUDA load failed, fallback to CPU: {exc}"
        self._backend = "coqui"

    def _synthesize_piper(
        self,
        *,
        text: str,
        voice: str | None,
        speed: float | None,
    ) -> bytes:
        try:
            import piper  # noqa: F401
        except Exception as exc:
            raise TTSEngineError(f"Piper import failed: {exc}") from exc

        voices = self._list_piper_voices()
        if not voices:
            raise TTSEngineError(
                f"No Piper voices found in {self._settings.piper_voices_dir_path}. "
                "Run scripts/download_piper_voices.py."
            )

        selected_name = voice or voices[0].name
        model_path = self._settings.piper_voices_dir_path / f"{selected_name}.onnx"
        config_path = Path(f"{model_path}.json")
        if not model_path.exists() or not config_path.exists():
            available = ", ".join(v.name for v in voices) or "<none>"
            raise TTSEngineError(
                f"Voice '{selected_name}' was not found. Available voices: {available}"
            )

        length_scale = 1.0
        if speed is not None and speed > 0:
            length_scale = 1.0 / speed

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            out_path = Path(temp_file.name)

        cmd = [
            sys.executable,
            "-m",
            "piper",
            "-m",
            str(model_path),
            "-c",
            str(config_path),
            "-f",
            str(out_path),
            "--length-scale",
            str(length_scale),
            "--",
            text,
        ]

        use_cuda = self._device == "cuda"
        if use_cuda:
            cmd.append("--cuda")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                check=False,
            )
            if proc.returncode != 0:
                if use_cuda:
                    self._device = "cpu"
                    self._last_error = (
                        f"Piper CUDA failed, fallback to CPU: {proc.stderr.decode('utf-8', errors='ignore')}"
                    )
                    cmd = [c for c in cmd if c != "--cuda"]
                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        check=False,
                    )
                if proc.returncode != 0:
                    raise TTSEngineError(
                        f"Piper synthesis failed: {proc.stderr.decode('utf-8', errors='ignore')}"
                    )
            return out_path.read_bytes()
        except Exception as exc:
            raise TTSEngineError(f"Piper synthesis failed: {exc}") from exc
        finally:
            if out_path.exists():
                out_path.unlink(missing_ok=True)

    def _synthesize_coqui(
        self,
        *,
        text: str,
        language: str,
        voice: str | None,
        speed: float | None,
    ) -> bytes:
        import soundfile as sf

        kwargs: dict[str, Any] = {"text": text, "language": language}
        if speed is not None:
            kwargs["speed"] = speed
        if voice:
            speaker_wav = (self._settings.voices_dir_path / f"{voice}.wav").resolve()
            if not speaker_wav.exists():
                available = ", ".join(v.name for v in self.list_voices()) or "<none>"
                raise TTSEngineError(
                    f"Voice '{voice}' was not found. Available voices: {available}"
                )
            kwargs["speaker_wav"] = str(speaker_wav)

        try:
            wav = self._model.tts(**kwargs)
            sample_rate = getattr(getattr(self._model, "synthesizer", None), "output_sample_rate", 24000)
            buffer = io.BytesIO()
            sf.write(buffer, wav, sample_rate, format="WAV")
            buffer.seek(0)
            return buffer.read()
        except Exception as exc:
            raise TTSEngineError(f"TTS synthesis failed: {exc}") from exc

    def _synthesize_pyttsx3(
        self,
        *,
        text: str,
        voice: str | None,
        speed: float | None,
    ) -> bytes:
        engine = self._model
        if engine is None:
            raise TTSEngineError("pyttsx3 engine is not initialized.")

        if voice:
            available = {v.name: v for v in self.list_voices()}
            if voice not in available:
                names = ", ".join(available.keys()) or "<none>"
                raise TTSEngineError(f"Voice '{voice}' was not found. Available voices: {names}")
            engine.setProperty("voice", voice)

        if speed is not None:
            base_rate = self._pyttsx3_base_rate
            if base_rate is None:
                base_rate = int(engine.getProperty("rate"))
                self._pyttsx3_base_rate = base_rate
            engine.setProperty("rate", int(base_rate * speed))

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            engine.save_to_file(text, str(temp_path))
            engine.runAndWait()
            return temp_path.read_bytes()
        except Exception as exc:
            raise TTSEngineError(f"pyttsx3 synthesis failed: {exc}") from exc
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
