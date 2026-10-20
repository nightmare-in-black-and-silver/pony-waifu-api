from pydantic import BaseModel


class LLMEndpoint(BaseModel):
    id: str
    base_url: str
    api_key: str | None = None
    default_model: str | None = None


class LLMEndpoints(BaseModel):
    apis: list[LLMEndpoint]