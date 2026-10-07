import json
import random

from app.config import Config
from app.models.expression.expression import Expression


class ExpressionsService:
    def __init__(self, config: Config):
        self._config = config
        self._expressions: list[Expression] = []

    def load(self) -> None:
        with self._config.expressions_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._expressions = [
            Expression.model_validate(expression)
            for expression in data["expressions"]
        ]

    def get_all(self) -> list[Expression]:
        return self._expressions
    
    def get_expression(
        self,
        character_id: str,
        expression_id: str,
    ) -> str | None:
        character_expression_dir = (
            self._config.expression_files_dir / character_id
        )

        if not character_expression_dir.exists():
            return None

        expression_files = [
            file
            for file in character_expression_dir.iterdir()
            if file.is_file()
            and file.name.startswith(expression_id)
        ]

        if not expression_files:
            return None

        return random.choice(expression_files).name