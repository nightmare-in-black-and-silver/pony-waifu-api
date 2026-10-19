import base64
from uuid import uuid4

from fastapi import WebSocket

import httpx
import logging
from pydantic import ValidationError

from app.models.messages.incoming.chat import ChatMessage
from app.models.messages.incoming.message import IncomingMessage
from app.services.asset_service import AssetService
from app.services.llm_service import LLMService


class WebSocketService:
    def __init__(self, llm_service: LLMService, asset_service: AssetService):
        self._llm_service = llm_service
        self._asset_service = asset_service
        self._connections: dict[str, WebSocket] = {}
        self.logger = logging.getLogger(__name__)

    def connect(self, websocket: WebSocket) -> str:
        connection_id = str(uuid4())
        self._connections[connection_id] = websocket
        return connection_id

    def disconnect(self, connection_id: str) -> None:
        self._connections.pop(connection_id, None)

    def get(self, connection_id: str) -> WebSocket | None:
        return self._connections.get(connection_id)


    async def handle_message(
        self,
        connection_id: str,
        data: dict,
    ) -> None:
        request_id = data.get("request_id")

        try:
            incoming = IncomingMessage.model_validate(data)

            match incoming.type:
                case "llm.health_check":
                    await self._handle_llm_health_check(
                        connection_id,
                        incoming,
                    )
                    
                case "llm.chat":
                    await self._handle_llm_chat_request(
                        connection_id,
                        incoming,
                    )
                    
                case "asset.expression.get":
                    await self._handle_asset_expression_get(
                        connection_id,
                        incoming,
                    )

                case _:
                    await self.send_json(
                        connection_id,
                        {
                            "type": "error",
                            "request_id": incoming.request_id,
                            "payload": {
                                "message": f"Unknown message type: {incoming.type}",
                            },
                        },
                    )

        except (ValidationError, ValueError) as exc:
            await self.send_json(
                connection_id,
                {
                    "type": "error",
                    "request_id": request_id,
                    "payload": {
                        "message": str(exc),
                    },
                },
            )

        except httpx.ConnectError as exc:
            self.logger.exception("HTTP connection failed")

            await self.send_json(
                connection_id,
                {
                    "type": f"{incoming.type}.error",
                    "request_id": request_id,
                    "payload": {
                        "message": f"Unable to connect to endpoint: {exc.request.url}",
                    },
                },
            )

        except httpx.TimeoutException as exc:
            self.logger.exception("HTTP request timed out")

            await self.send_json(
                connection_id,
                {
                    "type": f"{incoming.type}.error",
                    "request_id": request_id,
                    "payload": {
                        "message": f"Endpoint request timed out: {exc.request.url}",
                    },
                },
            )

        except Exception:
            self.logger.exception("Error processing WebSocket message")

            await self.send_json(
                connection_id,
                {
                    "type": "error",
                    "request_id": request_id,
                    "payload": {
                        "message": "Internal server error",
                    },
                },
            )

    async def send_json(
        self,
        connection_id: str,
        data: dict,
    ) -> None:
        websocket = self.get(connection_id)

        if websocket is None:
            raise ValueError(
                f"WebSocket connection '{connection_id}' not found"
            )

        await websocket.send_json(data)
        
    async def _handle_llm_health_check(
        self,
        connection_id: str,
        incoming: IncomingMessage,
    ) -> None:
        message = incoming.payload.get("message")

        if not isinstance(message, str):
            raise ValueError("Health check requires a text message")

        result = await self._llm_service.health_check(message)

        await self.send_json(
            connection_id,
            {
                "type": "llm.health_check.result",
                "request_id": incoming.request_id,
                "payload": {
                    "message": result,
                },
            },
        )
        
    async def _handle_asset_expression_get(
        self,
        connection_id: str,
        incoming: IncomingMessage,
    ) -> None:
        character_id = incoming.payload["character_id"]

        image_bytes = self._asset_service.get_expression_bytes(
            character_id=character_id,
            expression_id="neutral",
        )

        if image_bytes is None:
            await self.send_json(
                connection_id,
                {
                    "type": "asset.expression.error",
                    "request_id": incoming.request_id,
                    "payload": {
                        "message": f"Neutral expression not found for character: {character_id}",
                    },
                },
            )
            return

        await self.send_json(
            connection_id,
            {
                "type": "asset.expression.result",
                "request_id": incoming.request_id,
                "payload": {
                    "character_id": character_id,
                    "expression": "neutral",
                    "image": base64.b64encode(image_bytes).decode("ascii"),
                },
            },
        )

    async def _handle_llm_chat_request(
        self,
        connection_id: str,
        incoming: IncomingMessage,
    ) -> None:
        chat_request = ChatMessage.model_validate(incoming.payload)

        async for response in self._llm_service.generate_response(chat_request):
            await self.send_json(
                connection_id,
                {
                    "type": f"llm.chat.{response['type']}",
                    "request_id": incoming.request_id,
                    "payload": {
                        key: value
                        for key, value in response.items()
                        if key != "type"
                    },
                },
            )