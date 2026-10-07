from pydantic import BaseModel

from app.models.cast.silly_tavern import SillyTavern


class Character(BaseModel):
    id: str
    name: str
    description: str | None = None
    voice_id: str | None = None
    silly_tavern: SillyTavern | None = None