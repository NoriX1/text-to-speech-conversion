# Local Text-to-Speech Server

Полностью локальный TTS-сервер на FastAPI без API-ключей и платных сервисов.

Основной backend: `piper` (качественные офлайн ONNX-голоса).  
Fallback: `pyttsx3` (системный TTS).

## 1. Быстрый старт (рекомендуется)

### Windows
```powershell
copy .env.example .env
.\scripts\start.ps1
```

### Linux
```bash
cp .env.example .env
bash scripts/start.sh
```

Скрипты автоматически:
- создают `.venv` (если его нет),
- устанавливают зависимости из `requirements.txt`,
- запускают `uvicorn` c `APP_HOST`/`APP_PORT` из `.env` (если хост/порт не переданы аргументами).

## 2. Ручная установка (опционально)

### Windows
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

### Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## 3. Скачать голоса Piper
```powershell
.\.venv\Scripts\python.exe scripts\download_piper_voices.py
```

По умолчанию скачиваются:
- `ru_RU-denis-medium`
- `ru_RU-dmitri-medium`
- `ru_RU-irina-medium`
- `ru_RU-ruslan-medium`

Файлы попадут в `voices/piper`.

## 4. Запуск сервера (ручной вариант)
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Скрипты `scripts/start.ps1` и `scripts/start.sh` читают `APP_HOST`/`APP_PORT` из `.env`, если host/port не переданы аргументами.

Пример явного переопределения через аргументы:
- PowerShell: `.\scripts\start.ps1 -HostAddress 0.0.0.0 -Port 9000`
- Bash: `bash scripts/start.sh 0.0.0.0 9000`

## 5. API

### `GET /health`
Проверка состояния сервиса.

### `GET /ready`
Проверка готовности TTS backend.

### `GET /v1/voices`
Список доступных голосов.

### `POST /v1/tts`
```bash
curl -X POST "http://127.0.0.1:8000/v1/tts" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"Привет!\",\"language\":\"ru\",\"voice\":\"ru_RU-irina-medium\",\"format\":\"wav\"}" \
  --output out.wav
```

## 6. Настройки `.env`
```dotenv
APP_HOST=127.0.0.1
APP_PORT=8000
TTS_DEVICE=auto
TTS_BACKEND=piper
TTS_MODEL_NAME=tts_models/multilingual/multi-dataset/xtts_v2
TTS_MAX_TEXT_LENGTH=1000
TTS_VOICES_DIR=voices
TTS_PIPER_VOICES_DIR=voices/piper
TTS_DEFAULT_LANGUAGE=ru
TTS_DEFAULT_VOICE=ru_RU-ruslan-medium
TTS_DEFAULT_SPEED=1.0
```

По умолчанию сервер использует голос `ru_RU-ruslan-medium` со скоростью `1.0`, если `voice/speed` не переданы в запросе.

`TTS_BACKEND`:
- `piper` - только Piper
- `pyttsx3` - только системный офлайн TTS
- `coqui` - только Coqui (если установлен отдельно)
- `auto` - Piper -> Coqui -> pyttsx3

`TTS_DEVICE`:
- `auto` - CUDA при наличии, иначе CPU
- `cuda` - принудительно GPU
- `cpu` - принудительно CPU
