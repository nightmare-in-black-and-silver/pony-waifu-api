import json

from app.config import Config
from app.models.cast.character import Character


class CastService:
    def __init__(self, config: Config):
        self._config = config
        self._characters: dict[str, Character] = {}
        self._anatomy: dict[str, str] = {}

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

        with self._config.anatomy_file.open("r", encoding="utf-8") as file:
            anatomy_data = json.load(file)

        self._anatomy = {
            species_id: species["description"]
            for species_id, species in anatomy_data.items()
        }

    def get_all(self) -> list[Character]:
        return list(self._characters.values())

    def get(self, character_id: str) -> Character | None:
        return self._characters.get(character_id)

    def get_anatomy(self, species_id: str) -> str | None:
        return self._anatomy.get(species_id)