from app.config import Config
from app.models.assets.assets import Assets


class AssetService:
    def __init__(self, config: Config):
        self._config = config
        self._assets: dict[str, Assets] = {}

    def load(self) -> None:
        import json

        with self._config.expressions_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        expression_names = [
            expression["name"]
            for expression in data["expressions"]
        ]

        if not self._config.expression_files_dir.exists():
            return

        for character_dir in self._config.expression_files_dir.iterdir():
            if not character_dir.is_dir():
                continue

            expressions: dict[str, list[str]] = {}

            for expression_name in expression_names:
                files = [
                    file.name
                    for file in character_dir.iterdir()
                    if file.is_file()
                    and (
                        file.stem == expression_name
                        or file.stem.startswith(f"{expression_name}-")
                    )
                ]

                if files:
                    expressions[expression_name] = files

            self._assets[character_dir.name] = Assets(
                expressions=expressions,
                voices={},
            )

    def has_expression(
        self,
        character_id: str,
        expression_id: str,
    ) -> bool:
        assets = self._assets.get(character_id)

        if assets is None:
            return False

        return expression_id in assets.expressions