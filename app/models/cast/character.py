from pydantic import BaseModel


class Character(BaseModel):
    id: str
    name: str
    description: str | None = None
    voice_id: str | None = None