from pydantic import BaseModel, Field
from uuid import uuid4


class SpeechLine(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    audio: bytes
