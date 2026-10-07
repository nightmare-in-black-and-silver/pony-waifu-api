import json
from pathlib import Path
from app.config import Config

from app.models.cast.character import Character


class CastService:
    def __init__(self, config: Config):
        self._config = config
        self._characters: dict[str, Character] = {}

    def load(self) -> None:
        with self._config.cast_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
            
        characters = [
            Character.model_validate(character)
            for character in data["characters"]
        ]

        self._characters = {
            character.id: character
            for character in characters
        }

    def get_all(self) -> list[Character]:
        return list(self._characters.values())

    def get(self, character_id: str) -> Character | None:
        return self._characters.get(character_id)