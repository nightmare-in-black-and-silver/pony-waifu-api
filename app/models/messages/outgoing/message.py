from typing import Any

from pydantic import BaseModel, Field


class OutgoingMessage(BaseModel):
    type: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)