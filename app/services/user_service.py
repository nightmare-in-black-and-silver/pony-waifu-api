import json

from app.config import Config
from app.models.user.user import User


class UserService:
    def __init__(self, config: Config):
        self._config = config
        self._user: User | None = None

    def load(self) -> None:
        with self._config.user_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._user = User.model_validate(data)

    def get(self) -> User:
        if self._user is None:
            raise RuntimeError("User has not been loaded")

        return self._user