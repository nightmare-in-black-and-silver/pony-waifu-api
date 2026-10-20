import httpx
import json
from collections.abc import AsyncIterator

from app.config import Config
from app.models.audio.speech_line import SpeechLine

class SpeechService:
    def __init__(self, config: Config):
        self._config = config
        self._tts_base_url: str | None = None
        self._voice_expressions: dict[str, str] = {}
    
    
    def load(self) -> None:
        with self._config.llm_endpoints_file.open("r", encoding="utf-8") as file:
            endpoints = json.load(file)["endpoints"]

        speech_generator = next(
            (
                endpoint
                for endpoint in endpoints
                if endpoint["id"] == "speech_generator_llm"
            ),
            None,
        )

        if speech_generator is None:
            raise ValueError("speech_generator_llm endpoint not configured")

        self._tts_base_url = speech_generator["base_url"].rstrip("/")
        
        with self._config.expressions_file.open("r", encoding="utf-8") as file:
            expressions = json.load(file)["expressions"]

        expression_lookup = {
            expression["name"]: expression
            for expression in expressions
        }

        for name, expression in expression_lookup.items():
            resolved = name
            visited = set()

            while "shared" in expression_lookup[resolved]:
                if resolved in visited:
                    raise ValueError(f"Circular expression mapping: {name}")

                visited.add(resolved)
                resolved = expression_lookup[resolved]["shared"]

                if resolved not in expression_lookup:
                    raise ValueError(f"Unknown shared expression: {resolved}")

            if expression_lookup[resolved].get("voice") is not True:
                raise ValueError(f"No voice configured for expression: {name}")

            self._voice_expressions[name] = resolved
    
    async def generate_speech(
        self,
        text: str,
        voice_id: str | None = None,
    ) -> AsyncIterator[SpeechLine]:
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in lines:
            audio = await self._generate_audio(
                text=line,
                voice_id=voice_id,
            )

            yield SpeechLine(
                text=line,
                audio=audio,
            )
    
    
    def split_dialogue(self, text: str) -> list[str]:
        return [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]
        
    async def _generate_audio(
        self,
        text: str,
        voice_id: str | None = None,
    ) -> bytes:
        if voice_id is None:
            raise ValueError("voice_id is required for audio generation")

        if self._tts_base_url is None:
            raise RuntimeError("SpeechService has not been loaded")

        voice, expression = voice_id.split("/", maxsplit=1)

        resolved_expression = self._voice_expressions.get(expression)

        if resolved_expression is None:
            raise ValueError(f"Unknown voice expression: {expression}")

        url = f"{self._tts_base_url}/voices/{voice}/{resolved_expression}"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                url,
                content=text.encode("utf-8"),
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                },
            )

            response.raise_for_status()
            return response.content