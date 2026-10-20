from pydantic import BaseModel


class Character(BaseModel):
    id: str
    name: str
    summary: str | None = None
    voice_id: str | None = None
    species: str
    description: str = ""
    appearance: str = ""
    personality: str = ""
    interests: str = ""