from pydantic import BaseModel


class SceneMood(BaseModel):
    moods: list[str]