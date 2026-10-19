from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    service = websocket.app.state.websocket_service
    connection_id = service.connect(websocket)

    try:
        await service.send_json(
            connection_id,
            {
                "type": "connection.ready",
                "connection_id": connection_id,
            },
        )

        while True:
            data = await websocket.receive_json()

            await service.handle_message(
                connection_id,
                data,
            )

    except WebSocketDisconnect:
        pass

    finally:
        service.disconnect(connection_id)