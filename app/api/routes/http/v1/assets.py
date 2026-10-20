from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

router = APIRouter()


@router.get(
    "/assets/expressions/{character_id}/{expression_id}",
    name="expression_image",
)
async def get_expression_image(
    character_id: str,
    expression_id: str,
    request: Request,
):
    asset_service = request.app.state.asset_service

    image_path = asset_service.get_expression_file(
        character_id=character_id,
        expression_id=expression_id,
    )

    if image_path is None or not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Expression image not found",
        )

    return FileResponse(image_path)