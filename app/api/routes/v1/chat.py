from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    scene_mood: str = "neutral"


@router.post("/chat")
async def chat(
    chat_request: ChatRequest,
    request: Request,
) -> dict:
    return await request.app.state.api_service.chat(
        chat_request.message
    )
    

@router.post("/chat/{character_id}")
async def chat(
    character_id: str,
    chat_request: ChatRequest,
    request: Request,
) -> dict:
    character = request.app.state.cast_service.get(character_id)

    if character is None:
        raise HTTPException(
            status_code=404,
            detail=f"Character '{character_id}' not found",
        )

    return await request.app.state.api_service.chat(
        message=chat_request.message,
        character=character,
        scene_mood=chat_request.scene_mood,
    )