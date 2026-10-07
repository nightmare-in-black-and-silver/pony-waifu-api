from fastapi import FastAPI

from app.api.routes.v1.health import router as health_router
from app.api.routes.v1.characters import router as characters_router
from app.api.routes.v1.chat import router as chat_router


from app.config import Config
from app.services.cast_service import CastService
from app.services.api_service import ApiService
from app.services.prompt_service import PromptService
from app.services.user_service import UserService
from app.services.scene_service import SceneService
from app.services.asset_service import AssetService


config = Config()

cast_service = CastService(config)
cast_service.load()

prompt_service = PromptService(config)
prompt_service.load()

user_service = UserService(config)
user_service.load()

asset_service = AssetService(config)
asset_service.load()

scene_service = SceneService(config=config,assets_service=asset_service)
scene_service.load()


api_service = ApiService(config, 
                         prompt_service=prompt_service, 
                         user_service=user_service, 
                         expression_service=scene_service)
api_service.load()





app = FastAPI(
    title="Pony Waifu API",
    version="0.1.0",
)

app.state.config = config
app.state.cast_service = cast_service
app.state.api_service = api_service
app.state.prompt_service = prompt_service
app.state.asset_service = asset_service
app.state.scene_service = scene_service


# V1 Routers
app.include_router(health_router, prefix="/v1")
app.include_router(characters_router, prefix="/v1")
app.include_router(chat_router, prefix="/v1")