# AI Agent Instructions: Local TTS Server

## 1. Purpose
Use this local server to convert text to speech (WAV) without cloud APIs or API keys.

Base URL (default): `http://127.0.0.1:8000`

## 2. Preconditions
- Server process is running.
- Voices are downloaded to `voices/piper` (for Piper backend).

## 3. Minimal Workflow
1. Check service health: `GET /health`
2. Check available voices: `GET /v1/voices`
3. Send TTS request: `POST /v1/tts`
4. Save response bytes as `.wav`

## 4. Endpoints

### `GET /health`
Returns service status and backend info.

Expected fields:
- `status`
- `model_ready`
- `device`
- `backend`
- `last_error`

### `GET /ready`
Returns readiness status.
- `200` if ready
- `503` if model/backend is not ready

### `GET /v1/voices`
Returns available voices.

Example response:
```json
{
  "count": 4,
  "voices": [
    "ru_RU-denis-medium",
    "ru_RU-dmitri-medium",
    "ru_RU-irina-medium",
    "ru_RU-ruslan-medium"
  ]
}
```

### `POST /v1/tts`
Content-Type: `application/json`

Request schema:
```json
{
  "text": "string, required",
  "language": "string, optional, default ru",
  "voice": "string, optional",
  "speed": "number, optional, 0.5..2.0",
  "format": "wav"
}
```

Response:
- `200` + `audio/wav` bytes on success
- `4xx/5xx` + JSON error on failure

## 5. Defaults
If `voice`/`speed` are omitted, server uses `.env` defaults:
- `TTS_DEFAULT_VOICE=ru_RU-ruslan-medium`
- `TTS_DEFAULT_SPEED=1.0`

## 6. Agent Behavior Rules
- Always send UTF-8 JSON.
- Always set `"format": "wav"`.
- Keep text length within server limit (`TTS_MAX_TEXT_LENGTH`, default 1000).
- Before first synthesis in a session, call `/health` or `/ready`.
- If `voice` is unknown, call `/v1/voices` and retry with a valid voice.
- On HTTP `422`, fix request JSON shape/types.
- On HTTP `400`, use server `detail` to correct request.
- On HTTP `500`, retry once after short delay; if still failing, surface error.

## 7. Example Request
```bash
curl -X POST "http://127.0.0.1:8000/v1/tts" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Привет! Это тест.\",\"language\":\"ru\",\"voice\":\"ru_RU-ruslan-medium\",\"speed\":1.0,\"format\":\"wav\"}" \
  --output out.wav
```

## 8. Quick Diagnostics
- `GET /health` returns `model_ready=false`: backend/model init issue.
- `GET /v1/voices` empty: voices not downloaded or wrong voices path.
- `POST /v1/tts` with `400` unknown voice: select one from `/v1/voices`.
