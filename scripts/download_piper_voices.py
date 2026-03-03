from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path


VOICE_URLS = {
    "ru_RU-denis-medium": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx.json",
    },
    "ru_RU-dmitri-medium": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx.json",
    },
    "ru_RU-irina-medium": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx.json",
    },
    "ru_RU-ruslan-medium": {
        "model": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx",
        "config": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx.json",
    },
}


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download open-source Piper voices")
    parser.add_argument(
        "--voice",
        action="append",
        choices=sorted(VOICE_URLS.keys()),
        help="Voice id to download. Can be specified multiple times.",
    )
    parser.add_argument(
        "--output-dir",
        default="voices/piper",
        help="Where to store .onnx and .onnx.json files",
    )
    args = parser.parse_args()

    selected = args.voice if args.voice else sorted(VOICE_URLS.keys())
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for voice_id in selected:
        urls = VOICE_URLS[voice_id]
        model_path = out_dir / f"{voice_id}.onnx"
        config_path = out_dir / f"{voice_id}.onnx.json"

        if not model_path.exists():
            print(f"Downloading model: {voice_id}")
            download(urls["model"], model_path)
        else:
            print(f"Model exists, skipping: {model_path}")

        if not config_path.exists():
            print(f"Downloading config: {voice_id}")
            download(urls["config"], config_path)
        else:
            print(f"Config exists, skipping: {config_path}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
