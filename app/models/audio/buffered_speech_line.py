from app.models.audio.speech_line import SpeechLine
from datetime import datetime, timezone

from pydantic import Field


class BufferedSpeechLine(SpeechLine):
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
