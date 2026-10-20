"""FastAPI adapter for an existing Gradio F5-TTS service.

Voices are configured by character and expression.
No F5TTS/PyTorch model is loaded in this process.
"""

import argparse
import asyncio
import contextlib
import io
import json
import logging
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from uuid import uuid4

import soundfile as sf
import yaml
from fastapi import FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import Response
from pydantic import BaseModel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
GRADIO_URL = os.getenv(
    "GRADIO_URL", "http://127.0.0.1:7860"
).rstrip("/")


class VoiceConfig(BaseModel):
    ref_file: Path
    ref_text: str = ""


class Config:
    def load(self):
        with (BASE_DIR / "config.yaml").open(
            "rt", encoding="utf-8"
        ) as inp:
            data = yaml.safe_load(inp)

        self.VOICES = {
            character: {
                expression: VoiceConfig.model_validate(config)
                for expression, config in expressions.items()
            }
            for character, expressions in data["voices"].items()
        }

        if not self.VOICES:
            raise ValueError("Must configure at least one character")


CONFIG = Config()
INFERENCE_LOCK = asyncio.Lock()


@contextlib.asynccontextmanager
async def setup_teardown(_app):
    CONFIG.load()
    logger.info(
        "Gradio backend: %s; characters: %s",
        GRADIO_URL,
        list(CONFIG.VOICES),
    )
    yield


app = FastAPI(
    title="Pony Waifu F5-TTS",
    lifespan=setup_teardown,
)


def http_request(
    method: str,
    url: str,
    body: bytes | None = None,
    content_type: str | None = None,
) -> bytes:
    headers = {"Content-Type": content_type} if content_type else {}
    req = Request(url, data=body, headers=headers, method=method)

    with urlopen(req, timeout=180) as response:
        return response.read()


def upload_reference(path: Path) -> str:
    """Upload reference audio to the Gradio backend."""
    boundary = f"----f5adapter{uuid4().hex}"
    content = path.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files"; filename="{path.name}"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()

    result = json.loads(
        http_request(
            "POST",
            f"{GRADIO_URL}/gradio_api/upload",
            body,
            f"multipart/form-data; boundary={boundary}",
        )
    )

    if not isinstance(result, list) or not result:
        raise ValueError(
            f"Unexpected Gradio upload response: {result!r}"
        )

    return result[0]


def generate_via_gradio(
    voice: VoiceConfig,
    text: str,
) -> tuple:
    ref_path = voice.ref_file

    if not ref_path.is_absolute():
        ref_path = BASE_DIR / ref_path

    if not ref_path.is_file():
        raise FileNotFoundError(
            f"Reference WAV not found: {ref_path}"
        )

    uploaded_path = upload_reference(ref_path)

    payload = {
        "ref_audio_input": {
            "path": uploaded_path,
            "meta": {"_type": "gradio.FileData"},
        },
        "ref_text_input": voice.ref_text,
        "gen_text_input": text,
        "remove_silence": False,
        "randomize_seed": True,
        "seed_input": 0,
        "cross_fade_duration_slider": 0.15,
        "nfe_slider": 32,
        "speed_slider": 1.0,
    }

    submitted = json.loads(
        http_request(
            "POST",
            f"{GRADIO_URL}/gradio_api/call/v2/basic_tts",
            json.dumps(payload).encode(),
            "application/json",
        )
    )

    event_id = submitted["event_id"]

    sse = http_request(
        "GET",
        f"{GRADIO_URL}/gradio_api/call/basic_tts/{event_id}",
    ).decode()

    event_type = None
    result = None

    for line in sse.splitlines():
        if line.startswith("event: "):
            event_type = line[7:]

        elif line.startswith("data: "):
            if event_type == "error":
                raise RuntimeError(
                    f"Gradio inference failed: {line[6:]}"
                )

            if event_type == "complete":
                result = json.loads(line[6:])
                break

    if (
        not result
        or not isinstance(result[0], dict)
        or not result[0].get("url")
    ):
        raise RuntimeError(
            f"Unexpected Gradio output: {result!r}"
        )

    audio_url = urljoin(
        GRADIO_URL + "/", result[0]["url"]
    )

    if not audio_url.startswith(GRADIO_URL + "/"):
        raise RuntimeError(
            "Unexpected audio URL returned by Gradio"
        )

    audio_bytes = http_request("GET", audio_url)

    return sf.read(
        io.BytesIO(audio_bytes),
        dtype="float32",
    )


@app.post("/voices/{character}/{expression}")
async def create_speech(
    character: str,
    expression: str,
    request: FastAPIRequest,
):
    expressions = CONFIG.VOICES.get(character)

    if expressions is None:
        raise HTTPException(
            404, detail=f"Unknown character: {character}"
        )

    voice = expressions.get(expression)

    if voice is None:
        raise HTTPException(
            404,
            detail=(
                f"Unknown expression '{expression}' "
                f"for character '{character}'"
            ),
        )

    try:
        text = (await request.body()).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            400, detail="Request body must be UTF-8 text"
        ) from exc

    if not text.strip():
        raise HTTPException(
            400, detail="Text must not be empty"
        )

    logger.info(
        "Speech request: character=%s expression=%s",
        character,
        expression,
    )

    try:
        async with INFERENCE_LOCK:
            wave, rate = await asyncio.to_thread(
                generate_via_gradio,
                voice,
                text,
            )

        output = io.BytesIO()
        sf.write(output, wave, rate, format="WAV")

        return Response(
            content=output.getvalue(),
            media_type="audio/wav",
        )

    except (
        HTTPError,
        URLError,
        OSError,
        ValueError,
        RuntimeError,
    ) as exc:
        logger.exception("TTS request failed")
        raise HTTPException(
            502, detail=f"Gradio backend error: {exc}"
        ) from exc


@app.get("/voices")
async def list_voices():
    return {
        "voices": {
            character: list(expressions)
            for character, expressions in CONFIG.VOICES.items()
        }
    }


def main():
    parser = argparse.ArgumentParser(
        "Pony Waifu F5-TTS adapter"
    )
    parser.add_argument(
        "-H", "--host", default="127.0.0.1"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8000
    )

    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
