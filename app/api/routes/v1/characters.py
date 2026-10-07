from fastapi import APIRouter, HTTPException, Request

from app.models.cast.character import Character

router = APIRouter()


@router.get("/characters", response_model=list[Character])
async def get_characters(request: Request) -> list[Character]:
    return request.app.state.cast_service.get_all()


@router.get("/characters/{character_id}", response_model=Character)
async def get_character(
    character_id: str,
    request: Request,
) -> Character:
    character = request.app.state.cast_service.get(character_id)

    if character is None:
        raise HTTPException(
            status_code=404,
            detail=f"Character '{character_id}' not found",
        )

    return character