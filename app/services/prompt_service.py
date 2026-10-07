import json

from app.config import Config
from app.models.api.prompts import Prompts


class PromptService:
    def __init__(self, config: Config):
        self._config = config
        self._prompts: Prompts | None = None

    def load(self) -> None:
        with self._config.prompts_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._prompts = Prompts.model_validate(data)

    def get(self, prompt_name: str) -> str | None:
        if self._prompts is None:
            raise RuntimeError("Prompts have not been loaded")

        return getattr(self._prompts, prompt_name, None)