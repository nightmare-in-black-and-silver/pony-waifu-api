from pydantic import BaseModel


class User(BaseModel):
    name: str
    nicknames: list[str] = []
    gender: str
    pronouns: str