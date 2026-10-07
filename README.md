# Shakedown Voice API

A local API for real-time voice conversations with Shakedown.

The project provides the backend for a simple mobile voice-chat application. The phone acts primarily as a lightweight client, while speech recognition, character interaction, expression selection, and speech synthesis are handled by services running on the local server.

## Planned Pipeline

```text
Phone
  │
  │ Recorded audio
  ▼
Shakedown Voice API
  │
  ├── Speech-to-Text
  │     └── Convert the user's recording to text
  │
  ├── LM Studio
  │     └── Generate an in-character Shakedown response
  │
  ├── Expression Selection
  │     └── Determine the appropriate character expression
  │
  └── F5-TTS
        └── Generate Shakedown's spoken response
  │
  ▼
Phone
  ├── Response text
  ├── Expression
  └── Generated audio
```

## Goals

The project is intended to:

- Keep the mobile client extremely simple.
- Run AI inference locally rather than relying on cloud services.
- Maintain Shakedown's character, personality, and conversation history server-side.
- Support natural voice conversations rather than traditional long-form roleplay responses.
- Return both dialogue and an appropriate character expression.
- Generate spoken responses using F5-TTS.
- Keep individual AI components replaceable as the project evolves.

## Planned Technology

- **Python** — backend implementation
- **FastAPI** — HTTP API
- **Pydantic** — request/response models and validation
- **LM Studio** — local LLM inference
- **F5-TTS** — local text-to-speech
- **Whisper / faster-whisper** — local speech-to-text
- **Docker** — optional deployment

The exact components may change as development progresses.

## API

The primary endpoint is expected to be:

```http
POST /v1/pony/chat
```

A request will contain a recorded voice message.

The response will eventually contain data similar to:

```json
{
  "transcript": "How was your day?",
  "reply": "Eh, pretty good. Nearly dropped a dumbbell on some asshole's hoof, though.",
  "expression": "amusement",
  "audio": "..."
}
```

The exact API contract has not yet been finalised.

## Architecture

Where practical, AI components may run directly within the Python application rather than as separate HTTP services.

LM Studio will remain an external inference service and will be accessed through its API.

The backend may also manage model lifecycles to balance performance and available system/GPU memory—for example, unloading an LLM before running TTS if both models cannot comfortably remain resident simultaneously.

## Development Status

🚧 **Very early development**

Current priorities:

1. Establish the FastAPI project structure.
2. Implement a basic `/v1/pony/chat` endpoint.
3. Integrate speech-to-text.
4. Integrate LM Studio.
5. Define structured LLM output for dialogue and expressions.
6. Integrate F5-TTS.
7. Build the lightweight mobile client.

## Why?

Because apparently the reasonable response to wanting to talk to a fictional buff pony is to build an entire local AI voice pipeline.

## Important Terminology

This project uses:

```text
/v1/pony
```

Not:

```text
/v1/horse
```

This distinction is considered architecturally significant.