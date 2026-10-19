import json
import httpx
import re
from collections.abc import AsyncIterator
import base64


from app.config import Config
from app.models.llm.llm_endpoint import LLMEndpoint
from app.models.llm.instruction_templates import InstructionTemplate
from app.services.asset_service import AssetService
from app.services.cast_service import CastService
from app.services.scene_service import SceneService
from app.services.speech_service import SpeechService

from app.models.llm.response_plan import ResponsePlan
from app.models.messages.incoming.chat import ChatMessage
from app.services.user_service import UserService


class LLMService:
    def __init__(
        self,
        config: Config,
        scene_service: SceneService,
        cast_service: CastService,
        speech_service: SpeechService,
        asset_service: AssetService,
        user_service: UserService,
    ):
        self._config = config
        self._scene_service = scene_service
        self._cast_service = cast_service
        self._asset_service = asset_service
        self._speech_service = speech_service
        self._user_service = user_service

        self._instruction_templates: InstructionTemplate | None = None

        self._endpoint_address: str | None = None
        self._endpoint_key: str | None = None
        self._default_model: str | None = None

    def load(self) -> None:
        with self._config.instruction_template_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        self._instruction_templates = InstructionTemplate.model_validate(data)

        with self._config.llm_endpoints_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        endpoints = [
            LLMEndpoint.model_validate(api)
            for api in data["endpoints"]
        ]

        text_generator = next(
            (endpoint for endpoint in endpoints if endpoint.id == "text_generator_llm"),
            None,
        )

        if text_generator is None:
            raise RuntimeError("Text Generator Endpoint is not configured")

        self._endpoint_address = text_generator.base_url
        self._endpoint_key = text_generator.api_key
        self._default_model = text_generator.default_model
        
        # print("Template file:", self._config.instruction_template_file)
        # print("Loaded templates:", self._instruction_templates.model_dump().keys())

    def get_instruction_template(self, template_name: str) -> str | None:
        if self._instruction_templates is None:
            raise RuntimeError("LLM instruction templates have not been loaded")

        return getattr(self._instruction_templates, template_name, None)
    
    async def health_check(self, message: str) -> str:
        if self._endpoint_address is None or self._default_model is None:
            raise RuntimeError("LLM endpoint has not been configured")

        headers = {}

        if self._endpoint_key:
            headers["Authorization"] = f"Bearer {self._endpoint_key}"

        payload = {
            "model": self._default_model,
            "messages": [
                {
                    "role": "user",
                    "content": message,
                }
            ],
        }

        timeout = httpx.Timeout(
            connect=5.0,
            read=120.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self._endpoint_address.rstrip('/')}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

            return response.json()["choices"][0]["message"]["content"]
        
    async def generate_response(
        self,
        chat_request: ChatMessage,
    ) -> AsyncIterator[dict]:
        response_plan = await self.plan_response(chat_request)

        generated_lines: list[str] = []

        line = await self.generate_segment(
            chat_request=chat_request,
            response_direction=response_plan.response_direction,
        )

        # line = self.extract_spoken_dialogue(line)
        
        # if not line:
        #     raise ValueError("LLM generated no valid spoken dialogue") 

        # print(f"[LLM OUTPUT] {line!r}")

        expression = await self.classify_expression(
            character_id=chat_request.character_id,
            text=line,
        )

        image_bytes = self._asset_service.get_expression_bytes(
            character_id=chat_request.character_id,
            expression_id=expression,
        )

        image_data = (
            base64.b64encode(image_bytes).decode("ascii")
            if image_bytes is not None
            else None
        )

        async for speech_line in self._speech_service.generate_speech(
            text=line,
            voice_id=f"{chat_request.character_id}/{expression}",
        ):
            yield {
                "type": "line",
                "character_id": chat_request.character_id,
                "segment": 0,
                "id": speech_line.id,
                "text": speech_line.text,
                "expression": expression,
                "image": image_data,
                "audio": base64.b64encode(speech_line.audio).decode("ascii"),
            }

        scene_mood = await self.classify_scene_mood(
            current_mood=chat_request.current_mood,
            conversation_trajectory=response_plan.response_direction,
            lines=[line],
        )
        
        print(response_plan.model_dump_json(indent=2))

        yield {
            "type": "complete",
            "character_id": chat_request.character_id,
            "scene_mood": scene_mood,
        }
        
    async def generate_segment(
        self,
        chat_request: ChatMessage,
        response_direction: str,
    ) -> str:
        if self._endpoint_address is None or self._default_model is None:
            raise RuntimeError("LLM endpoint has not been configured")

        character = self._cast_service.get(chat_request.character_id)

        if character is None:
            raise ValueError(
                f"Character '{chat_request.character_id}' not found"
            )

        instruction_template = self.get_instruction_template(
            "segment_generation"
        )

        if instruction_template is None:
            raise RuntimeError(
                "Segment generation instruction template not found"
            )

        system_instructions = (
            instruction_template
            .replace("{{char}}", character.name)
            .replace("{{user}}", self._user_service.get().name)
            .replace("{{character_species}}", character.species)
            .replace("{{character_anatomy}}", self._cast_service.get_anatomy(character.species) or "")
            .replace("{{character_description}}", character.description)
            .replace("{{character_appearance}}", character.appearance)
            .replace("{{character_personality}}", character.personality)
            .replace("{{character_interests}}", character.interests)
            .replace("{{current_mood}}", chat_request.current_mood)
            .replace("{{response_direction}}", response_direction)
        )
        conversation = []
        
        print(f"[SEGMENT SYSTEM INSTRUCTIONS]\n{system_instructions}")

        for entry in chat_request.history:
            if isinstance(entry, str):
                conversation.append({
                    "role": "user",
                    "content": entry,
                })
            else:
                conversation.append({
                    "role": "assistant",
                    "content": "\n".join(entry.lines),
                })

        conversation.append({
            "role": "user",
            "content": chat_request.message,
        })

        headers = {}

        if self._endpoint_key:
            headers["Authorization"] = f"Bearer {self._endpoint_key}"

        payload = {
            "model": self._default_model,
            "messages": [
                {
                    "role": "system",
                    "content": system_instructions,
                },
                *conversation,
            ],
            "temperature": 0.7,
        }

        timeout = httpx.Timeout(
            connect=5.0,
            read=120.0,
            write=10.0,
            pool=5.0,
        )

        max_attempts = 3

        for attempt in range(max_attempts):
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self._endpoint_address.rstrip('/')}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )

                response.raise_for_status()
                
            content = response.json()["choices"][0]["message"]["content"]
            print(f"[RAW LM OUTPUT] {content!r}")

            if not isinstance(content, str):
                content = ""

            dialogue = self._clean_dialogue(content)
            
            if not dialogue:
                continue

            if dialogue:
                return dialogue

        raise RuntimeError(
            f"LLM failed to generate spoken dialogue after {max_attempts} attempts"
        )
        
    async def plan_response(
        self,
        chat_request: ChatMessage,
    ) -> ResponsePlan:
        if self._endpoint_address is None or self._default_model is None:
            raise RuntimeError("LLM endpoint has not been configured")

        character = self._cast_service.get(chat_request.character_id)

        if character is None:
            raise ValueError(
                f"Character '{chat_request.character_id}' not found"
            )

        instruction_template = self.get_instruction_template("response_planning")

        if instruction_template is None:
            raise RuntimeError("Response planning instruction template not found")

        user = self._user_service.get()

        system_instructions = (
            f"{instruction_template}\n\n"
            f"Character: {character.name}\n\n"
            f"Character Species: {character.species}\n\n"
            f"Description: {character.description}\n\n"
            f"Appearance: {character.appearance}\n\n"
            f"Personality: {character.personality}\n\n"
            f"Interests: {character.interests}\n\n"
            f"User name: {user.name}\n"
            f"User nicknames: {', '.join(user.nicknames)}\n"
            f"User gender: {user.gender}\n"
            f"User pronouns: {user.pronouns}"
        )

        conversation = []

        for entry in chat_request.history:
            if isinstance(entry, str):
                conversation.append({
                    "role": "user",
                    "content": entry,
                })
            else:
                conversation.append({
                    "role": "assistant",
                    "content": "\n".join(entry.lines),
                })

        conversation.append({
            "role": "user",
            "content": chat_request.message,
        })

        payload = {
            "model": self._default_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"{system_instructions}\n\n"
                        f"Current scene mood: {chat_request.current_mood}"
                    ),
                },
                *conversation,
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "response_plan",
                    "strict": True,
                    "schema": ResponsePlan.model_json_schema(),
                },
            },
        }

        headers = {}

        if self._endpoint_key:
            headers["Authorization"] = f"Bearer {self._endpoint_key}"

        timeout = httpx.Timeout(
            connect=5.0,
            read=120.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self._endpoint_address.rstrip('/')}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]

        return ResponsePlan.model_validate_json(content)
    
    async def classify_expression(
        self,
        character_id: str,
        text: str,
    ) -> str:
        if self._endpoint_address is None or self._default_model is None:
            raise RuntimeError("LLM endpoint has not been configured")

        instruction_template = self.get_instruction_template(
            "expressions_prompt"
        )

        if instruction_template is None:
            raise RuntimeError(
                "Expression classification instruction template not found"
            )

        expressions = self._scene_service.get_expressions()

        expression_names = [
            expression.name
            for expression in expressions
        ]

        if not expression_names:
            raise RuntimeError("No expressions have been configured")

        expression_prompt = (
            instruction_template
            .replace("{{response}}", text)
            .replace("{{labels}}", ", ".join(expression_names))
        )

        headers = {}

        if self._endpoint_key:
            headers["Authorization"] = f"Bearer {self._endpoint_key}"

        payload = {
            "model": self._default_model,
            "messages": [
                {
                    "role": "system",
                    "content": expression_prompt,
                }
            ],
            "temperature": 0.0,
        }

        timeout = httpx.Timeout(
            connect=5.0,
            read=120.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self._endpoint_address.rstrip('/')}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]

        if not isinstance(content, str):
            content = ""

        expression = content.strip().strip("*").strip().lower()

        valid_expressions = {
            name.lower(): name
            for name in expression_names
        }

        if expression not in valid_expressions:
            return self._scene_service.get_expression(
                character_id,
                "neutral",
            )

        return self._scene_service.get_expression(
            character_id,
            valid_expressions[expression],
        )
    
    async def classify_scene_mood(
        self,
        current_mood: str,
        conversation_trajectory: str,
        lines: list[str],
    ) -> str:
        if self._endpoint_address is None or self._default_model is None:
            raise RuntimeError("LLM endpoint has not been configured")

        instruction_template = self.get_instruction_template(
            "scene_mood_prompt"
        )

        if instruction_template is None:
            raise RuntimeError(
                "Scene mood instruction template not found"
            )

        moods = self._scene_service.get_scene_moods()

        if not moods:
            raise RuntimeError("No scene moods have been configured")

        scene_mood_prompt = (
            instruction_template
            .replace("{{current_mood}}", current_mood)
            .replace("{{conversation_trajectory}}", conversation_trajectory)
            .replace("{{response}}", "\n".join(lines))
            .replace("{{moods}}", ", ".join(moods))
        )

        headers = {}

        if self._endpoint_key:
            headers["Authorization"] = f"Bearer {self._endpoint_key}"

        payload = {
            "model": self._default_model,
            "messages": [
                {
                    "role": "system",
                    "content": scene_mood_prompt,
                }
            ],
            "temperature": 0.0,
        }

        timeout = httpx.Timeout(
            connect=5.0,
            read=120.0,
            write=10.0,
            pool=5.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self._endpoint_address.rstrip('/')}/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]

        if not isinstance(content, str):
            return current_mood

        selected_mood = content.strip().strip("*").strip().lower()

        valid_moods = {
            mood.lower(): mood
            for mood in moods
        }

        return valid_moods.get(selected_mood, current_mood)
    
    @staticmethod
    def _clean_dialogue(text: str) -> str:
        text = re.sub(r"\*[^*\n]*\*", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n[ \t]*\n+", "\n", text)

        return text.strip()
    
    @staticmethod
    def extract_spoken_dialogue(text: str) -> str:
        lines = []

        for line in text.splitlines():
            line = line.strip()

            if line.startswith("Dialogue:"):
                spoken = line.removeprefix("Dialogue:").strip()

                if spoken:
                    lines.append(spoken)

        return "\n".join(lines)