from fastapi import FastAPI

from app.api.routes.v1.health import router as health_router
from app.api.routes.v1.characters import router as characters_router

from app.config import Config
from app.services.cast_service import CastService


config = Config()

cast_service = CastService(config)
cast_service.load()


app = FastAPI(
    title="Pony Waifu API",
    version="0.1.0",
)

app.state.config = config
app.state.cast_service = cast_service


# V1 Routers
app.include_router(health_router, prefix="/v1")
app.include_router(characters_router, prefix="/v1")