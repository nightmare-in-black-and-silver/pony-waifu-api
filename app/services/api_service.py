import json
import httpx
import asyncio


from app.config import Config
from app.models.api.api import Api
from app.models.cast.character import Character
from app.services.prompt_service import PromptService
from app.services.user_service import UserService
from app.services.expression_service import ExpressionsService


class ApiService:
    def __init__(
        self,
        config: Config,
        prompt_service: PromptService,
        user_service: UserService,
        expression_service: ExpressionsService,
    ):
        self._config = config
        self._prompt_service = prompt_service
        self._expression_service = expression_service
        self._user_service = user_service
        self._apis: dict[str, Api] = {}

        self.api_address: str | None = None
        self.api_key: str | None = None
        self.default_model: str | None = None

    def load(self) -> None:
        with self._config.api_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        apis = [
            Api.model_validate(api)
            for api in data["apis"]
        ]

        self._apis = {
            api.id: api
            for api in apis
        }

        lm_studio = self.get("lm_studio")

        if lm_studio is None:
            raise RuntimeError("LM Studio API is not configured")

        self.api_address = lm_studio.base_url
        self.api_key = lm_studio.api_key
        self.default_model = lm_studio.default_model

    def get_all(self) -> list[Api]:
        return list(self._apis.values())

    def get(self, api_id: str) -> Api | None:
        return self._apis.get(api_id)
    
    async def get_lm_studio_models(self) -> dict:
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_address}/api/v1/models",
                headers=headers,
            )

            response.raise_for_status()
            return response.json()
        
    async def load_lm_studio_model(self, model: str | None = None) -> dict:
        model = model or self.default_model

        if model is None:
            raise RuntimeError("No LM Studio model specified")

        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_address}/api/v1/models/load",
                headers=headers,
                json={"model": model},
            )

            response.raise_for_status()
            return response.json()


    async def unload_lm_studio_model(self, model: str | None = None) -> dict:
        model = model or self.default_model

        if model is None:
            raise RuntimeError("No LM Studio model specified")

        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_address}/api/v1/models/unload",
                headers=headers,
                json={"model": model},
            )

            response.raise_for_status()
            return response.json()
        
    async def chat(
        self,
        message: str,
        character: Character | None = None,
    ) -> dict:
        if self.default_model is None:
            raise RuntimeError("No LM Studio default model specified")

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if character is None:
            payload = {
                "model": self.default_model,
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ],
            }
        else:
            system_prompt = self._prompt_service.get("system_prompt")

            user = self._user_service.get()

            user_prompt = (
                f"The user's name is {user.name}. "
                f"{user.name} is {user.gender} and uses "
                f"{user.pronouns} pronouns exclusively."
            )

            if user.nicknames:
                user_prompt += (
                    f" {user.name} is also known by the following nicknames: "
                    f"{', '.join(user.nicknames)}."
                )

            full_system_prompt = (
                f"{system_prompt}\n\n"
                f"{user_prompt}\n\n"
                f"Your name is {character.name}.\n\n"
                f"{character.silly_tavern.description}\n\n"
                f"{character.silly_tavern.personality}\n\n"
                f"{character.silly_tavern.character_prompt}"
            )

            payload = {
                "model": self.default_model,
                "messages": [
                    {
                        "role": "system",
                        "content": full_system_prompt,
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "character_response",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "segments": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                    },
                                    "minItems": 1,
                                    "maxItems": 4,
                                }
                            },
                            "required": ["segments"],
                            "additionalProperties": False,
                        },
                    },
                },
            }

        timeout = httpx.Timeout(
            connect=5.0,
            read=120.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.api_address}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

            parsed_response = await self._parse_chat_response(
                response.json(),
                structured=character is not None,
            )

            # Future expression selection and async TTS processing here.

            return parsed_response


    async def _parse_chat_response(
        self,
        response: dict,
        structured: bool = False,
    ) -> dict:
        content = response["choices"][0]["message"]["content"]

        if not structured:
            return {
                "segments": [
                    content.strip()
                ]
            }

        parsed_response = json.loads(content)

        expressions = self._expression_service.get_all()
        expression_names = [
            expression.name
            for expression in expressions
        ]

        expression_prompt = self._prompt_service.get("expressions_prompt")
        expression_prompt = expression_prompt.replace(
            "{{labels}}",
            ", ".join(expression_names),
        )

        expression_tasks = [
            self._get_expression_for_segment(
                segment,
                expression_prompt,
            )
            for segment in parsed_response["segments"]
        ]

        segment_expressions = await asyncio.gather(*expression_tasks)

        return {
            "segments": [
                {
                    "text": segment,
                    "expression": expression,
                }
                for segment, expression in zip(
                    parsed_response["segments"],
                    segment_expressions,
                )
            ]
        }
        
    async def _get_expression_for_segment(
        self,
        segment: str,
        expression_prompt: str,
    ) -> str:
        payload = {
            "model": self.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": expression_prompt,
                },
                {
                    "role": "user",
                    "content": segment,
                },
            ],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_address}/v1/chat/completions",
                json=payload,
            )

            response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"].strip().strip("*")