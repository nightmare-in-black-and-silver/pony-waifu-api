from fastapi import FastAPI


from app.api.routes.websocket.v1.websocket import router as websocket_router
from app.api.routes.http.v1.assets import router as assets_router

from app.config import Config
from app.services.cast_service import CastService
from app.services.llm_service import LLMService
from app.services.user_service import UserService
from app.services.scene_service import SceneService
from app.services.asset_service import AssetService
from app.services.websocket_service import WebSocketService
from app.services.speech_service import SpeechService

config = Config()

cast_service = CastService(config)
cast_service.load()

user_service = UserService(config)
user_service.load()

asset_service = AssetService(config)
asset_service.load()

scene_service = SceneService(config=config,assets_service=asset_service)
scene_service.load()

speech_service = SpeechService(config=config)
speech_service.load()

llm_services = LLMService(config=config, scene_service=scene_service, cast_service=cast_service, speech_service=speech_service, asset_service=asset_service, user_service=user_service)
llm_services.load()

websocket_service = WebSocketService(llm_service=llm_services, asset_service=asset_service, cast_service=cast_service)


app = FastAPI(
    title="Pony Waifu API",
    version="0.1.0",
)

app.state.config = config
app.state.cast_service = cast_service
app.state.asset_service = asset_service
app.state.scene_service = scene_service
app.state.llm_service = llm_services
app.state.speech_service = speech_service
app.state.websocket_service = websocket_service

# V1 Routers Websocket
app.include_router(websocket_router, prefix="/v1")
app.include_router(assets_router, prefix="/v1")