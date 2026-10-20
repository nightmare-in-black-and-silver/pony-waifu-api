from pydantic import BaseModel, Field


class AssistantHistoryMessage(BaseModel):
    lines: list[str] = Field(max_length=4)
    mood: str


class ChatMessage(BaseModel):
    character_id: str
    message: str
    current_mood: str = "neutral"
    history: list[str | AssistantHistoryMessage] = Field(
        default_factory=list,
        max_length=10,
    )