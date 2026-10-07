from fastapi import APIRouter, HTTPException, Request
import httpx

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/llm")
async def llm_health(request: Request) -> dict[str, str]:
    try:
        await request.app.state.api_service.get_lm_studio_models()

        return {
            "status": "ok",
            "service": "lm_studio",
        }

    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unavailable",
                "service": "lm_studio",
                "error": str(exc),
            },
        ) from exc