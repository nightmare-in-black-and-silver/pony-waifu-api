from pydantic import BaseModel


class Assets(BaseModel):
    expressions: dict[str, list[str]] = {}
    voices: dict[str, list[str]] = {}
    profile_picture: bytes | None = None