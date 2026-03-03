from __future__ import annotations

import io
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import Settings, get_settings
from app.schemas import TTSRequest
from app.tts_engine import TTSEngine, TTSEngineError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts-server")

settings: Settings = get_settings()
tts_engine = TTSEngine(settings=settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        tts_engine.load()
        logger.info("TTS model loaded on device=%s", tts_engine.device)
    except Exception as exc:
        logger.exception("Failed to load model on startup: %s", exc)
    yield


app = FastAPI(title="Local TTS Server", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "model_ready": tts_engine.ready,
            "device": tts_engine.device,
            "backend": tts_engine.backend,
            "last_error": tts_engine.last_error,
        }
    )


@app.get("/ready")
def ready() -> JSONResponse:
    if not tts_engine.ready:
        return JSONResponse(
            {
                "status": "not_ready",
                "model_ready": False,
                "last_error": tts_engine.last_error,
            },
            status_code=503,
        )
    return JSONResponse(
        {
            "status": "ready",
            "model_ready": True,
            "device": tts_engine.device,
            "backend": tts_engine.backend,
        }
    )


@app.get("/v1/voices")
def list_voices() -> JSONResponse:
    voices = tts_engine.list_voices()
    return JSONResponse(
        {
            "count": len(voices),
            "voices": [voice.name for voice in voices],
        }
    )


@app.post("/v1/tts")
def synthesize(payload: TTSRequest):
    language = payload.language or settings.tts_default_language
    voice = payload.voice or settings.tts_default_voice
    speed = payload.speed if payload.speed is not None else settings.tts_default_speed

    try:
        audio = tts_engine.synthesize(
            text=payload.text,
            language=language,
            voice=voice,
            speed=speed,
        )
    except TTSEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected synth error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal TTS error") from exc

    headers = {"Content-Disposition": 'inline; filename="tts.wav"'}
    return StreamingResponse(
        io.BytesIO(audio),
        media_type="audio/wav",
        headers=headers,
    )
