# Pony Waifu API

A local API for real-time voice conversations with AI-driven characters.

The project provides the backend for lightweight voice-chat clients. The client handles recording, playback, and presentation, while speech recognition, character interaction, expression selection, conversation state, and speech synthesis are handled by the local server.

The initial implementation is being developed around a single character, but the architecture is intended to support multiple characters with independent personalities, prompts, voices, expressions, and conversation histories.

## Planned Pipeline

```text
Client
  │
  │ Recorded audio
  ▼
Pony Waifu API
  │
  ├── Speech-to-Text
  │     └── Convert the user's recording to text
  │
  ├── Character / Conversation Context
  │     └── Build the appropriate prompt and conversation history
  │
  ├── LLM
  │     └── Generate an in-character response
  │
  ├── Expression Selection
  │     └── Determine the appropriate character expression
  │
  └── Text-to-Speech
        └── Generate the character's spoken response
  │
  ▼
Client
  ├── Transcript
  ├── Response text
  ├── Expression
  └── Generated audio
```

## Goals

The project is intended to:

- Keep clients lightweight and simple.
- Run AI inference locally rather than relying on cloud services.
- Support multiple characters with independent configurations.
- Maintain character personality, conversation context, and history server-side.
- Support natural voice conversations rather than traditional long-form roleplay responses.
- Return structured character responses including dialogue and expressions.
- Generate character-specific spoken responses.
- Keep individual AI components replaceable as the project evolves.
- Allow resource-intensive models to be loaded and unloaded as required.

## Planned Technology

- **Python** — backend implementation
- **FastAPI** — HTTP API
- **Pydantic** — request/response models and validation
- **LM Studio** — local LLM inference
- **F5-TTS** — local text-to-speech
- **Whisper / faster-whisper** — local speech-to-text
- **Docker** — optional deployment

The exact components may change as development progresses.

## Character Data

Characters are intended to be configuration rather than application code.

A character may eventually contain data such as:

```text
data/
└── characters/
    └── shakedown/
        ├── character.json
        ├── prompt.txt
        ├── voice/
        │   └── reference.wav
        └── expressions/
            ├── neutral.png
            ├── angry.png
            ├── amused.png
            └── ...
```

This allows new characters to be added without implementing character-specific application logic.

## API

The primary conversation endpoint is expected to accept a character identifier and a recorded voice message.

For example:

```http
POST /v1/chat
```

A response may eventually contain data similar to:

```json
{
  "character": "shakedown",
  "transcript": "How was your day?",
  "reply": "Eh, pretty good. Nearly dropped a dumbbell on some asshole's hoof, though.",
  "expression": "amusement",
  "audio": "..."
}
```

The exact API contract has not yet been finalised.

## Architecture

Where practical, AI components may run directly within the Python application rather than requiring separate HTTP services.

Components that already provide suitable inference servers, such as LM Studio, may remain external and be accessed through their APIs.

The backend may manage model lifecycles to balance latency and available system/GPU memory. Resource-intensive models may be loaded only when required and unloaded when another stage of the pipeline requires those resources.

Individual components should remain isolated behind service interfaces so implementations can be replaced without changing the rest of the application.

For example:

```text
SpeechToTextService
LanguageModelService
TextToSpeechService
ExpressionService
CharacterService
```

A local implementation could therefore be replaced with a remote service—or vice versa—without changing the public API.

## Development Status

🚧 **Very early development**

Current priorities:

1. Establish the FastAPI project structure.
2. Implement basic health and conversation endpoints.
3. Define the character configuration format.
4. Integrate speech-to-text.
5. Integrate LM Studio.
6. Define structured LLM output for dialogue and expressions.
7. Integrate F5-TTS.
8. Implement conversation state/history.
9. Build the first lightweight client.

## Why?

Because apparently the reasonable response to wanting to talk to fictional characters is to build an entire local AI voice infrastructure.

## Branching Strategy

The default branch is:

```text
waifu
```

This is a serious software engineering decision and should be treated accordingly.