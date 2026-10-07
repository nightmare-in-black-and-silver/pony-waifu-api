from pydantic import BaseModel


class Api(BaseModel):
    id: str
    base_url: str
    api_key: str | None = None
    default_model: str | None = None