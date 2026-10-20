from typing import Any

from pydantic import BaseModel, Field


class IncomingMessage(BaseModel):
    type: str
    request_id: str
    payload: dict[str, Any] = Field(default_factory=dict)