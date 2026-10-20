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
                    
            profile_picture_path = (
                self._config.root_dir
                / "assets"
                / "pfps"
                / f"{character_dir.name}.png"
            )

            profile_picture = (
                profile_picture_path.read_bytes()
                if profile_picture_path.is_file()
                else None
            )

            self._assets[character_dir.name] = Assets(
                expressions=expressions,
                voices={},
                profile_picture=profile_picture,
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
    
    def get_expression_file(
        self,
        character_id: str,
        expression_id: str,
    ) -> str | None:
        assets = self._assets.get(character_id)

        if assets is None:
            return None

        files = assets.expressions.get(expression_id)

        if not files:
            return None

        return files[0]
    
    def get_expression_bytes(
        self,
        character_id: str,
        expression_id: str,
    ) -> bytes | None:
        filename = self.get_expression_file(
            character_id=character_id,
            expression_id=expression_id,
        )

        if filename is None:
            return None

        path = (
            self._config.expression_files_dir
            / character_id
            / filename
        )

        return path.read_bytes()
    
    def get_profile_picture(self, character_id: str) -> bytes | None:
        assets = self._assets.get(character_id)
        return assets.profile_picture if assets else None