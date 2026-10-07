from fastapi import FastAPI

from app.api.routes.v1.health import router as health_router


app = FastAPI(
    title="Pony Waifu API",
    version="0.1.0",
)

app.include_router(health_router, prefix="/v1")