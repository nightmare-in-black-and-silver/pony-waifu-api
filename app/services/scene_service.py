import json

from app.config import Config
from app.models.scene_control.expression import Expression
from app.models.scene_control.scene_mood import SceneMood
from app.services.asset_service import AssetService



class SceneService:
    def __init__(
        self,
        config: Config,
        assets_service: AssetService,
    ):
        self._config = config
        self._assets_service = assets_service
        self._expressions: list[Expression] = []
        self._scene_mood: SceneMood | None = None
        self._current_mood: str = "neutral"
        
    def load(self) -> None:
        with self._config.expressions_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._expressions = [
            Expression.model_validate(expression)
            for expression in data["expressions"]
        ]

        with self._config.scene_mood_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._scene_mood = SceneMood.model_validate(data)

    def get_expressions(self) -> list[Expression]:
        return self._expressions
    
    def get_scene_moods(self) -> list[str]:
        if self._scene_mood is None:
            raise RuntimeError("Scene moods have not been loaded")

        return self._scene_mood.moods
    
    def get_expression(
        self,
        character_id: str,
        expression_id: str,
    ) -> str:
        if self._assets_service.has_expression(
            character_id,
            expression_id,
        ):
            return expression_id

        return "neutral"

    def get_mood(self) -> str:
        return self._current_mood

    def set_mood(self, mood: str) -> None:
        if mood not in self.get_scene_moods():
            raise ValueError(f"Invalid scene mood: {mood}")

        self._current_mood = mood