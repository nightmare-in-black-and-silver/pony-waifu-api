# Pony Waifu API

A local API for real-time voice conversations with AI-driven characters.

The project provides the backend for lightweight voice-chat clients. The client handles recording, playback, and presentation, while speech recognition, character interaction, conversation state, expression selection, and speech synthesis are handled by the local server.

The initial implementation is being developed around a small number of characters, but the architecture is intended to support multiple characters with independent personalities, prompts, voices, expressions, and conversation histories.

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
  ├── Command Processing
  │     └── Detect application-level commands such as character switching
  │
  ├── Session
  │     ├── Determine the active character
  │     └── Maintain conversation state
  │
  ├── Character Context
  │     ├── Personality / prompt
  │     ├── Relevant conversation history
  │     ├── Voice configuration
  │     └── Available expressions
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
  ├── Active character
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
- Allow users to move between characters during a session.
- Maintain character personality, conversation context, and history server-side.
- Support natural voice conversations rather than traditional long-form roleplay responses.
- Return structured character responses including dialogue and expressions.
- Generate character-specific spoken responses.
- Keep application commands separate from character dialogue.
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

## Characters

Characters are intended to be configuration and data rather than application code.

A character may eventually contain data such as:

```text
data/
└── characters/
    ├── shakedown/
    │   ├── character.json
    │   ├── prompt.txt
    │   ├── voice/
    │   │   └── reference.wav
    │   └── expressions/
    │       ├── neutral.png
    │       ├── angry.png
    │       ├── amused.png
    │       └── ...
    │
    └── luna/
        ├── character.json
        ├── prompt.txt
        ├── voice/
        │   └── reference.wav
        └── expressions/
            └── ...
```

This allows new characters to be added without implementing character-specific application logic.

## Sessions

A conversation takes place within a session.

A session is responsible for maintaining application state such as:

- The currently active character.
- Conversation history.
- Character-specific conversation context.
- Session-level events.
- Character changes.

This allows a user to move between characters while remaining within the same overall session.

For example:

```text
Session begins
    │
    ├── Talk to Shakedown
    │
    ├── Visit Luna
    │
    ├── Talk to Luna
    │
    ├── Visit Shakedown
    │
    └── Continue talking to Shakedown
```

Conversation knowledge does not necessarily need to be shared between characters. The session may maintain an overall event history while each character receives only the information appropriate to them.

The exact memory and context model will be determined during development.

## Commands

Application-level commands should be handled separately from normal character dialogue.

For example:

```text
Visit Luna
```

may be interpreted as:

```text
Command: VISIT
Target: luna
```

rather than being sent to the currently active character as dialogue.

The command processor can then update the session's active character before continuing the conversation.

Conceptually:

```text
Speech
  │
  ▼
Speech-to-Text
  │
  ▼
Command Processor
  │
  ├── Application command
  │       │
  │       └── Update session state
  │
  └── Normal dialogue
          │
          ▼
     Active Character
          │
          ▼
         LLM
```

Commands may eventually include operations such as:

```text
visit luna
visit shakedown
who am I talking to?
go home
start a new conversation
```

The exact command syntax and implementation have not yet been finalised.

## API

The primary conversation endpoint is expected to operate against a session rather than requiring the client to manage the active character directly.

For example:

```http
POST /v1/chat
```

A request may eventually contain:

```json
{
  "session_id": "abc123",
  "audio": "..."
}
```

A normal character response may resemble:

```json
{
  "type": "message",
  "session_id": "abc123",
  "character": {
    "id": "shakedown",
    "name": "Shakedown"
  },
  "transcript": "How was your day?",
  "reply": "Eh, pretty good. Nearly dropped a dumbbell on some asshole's hoof, though.",
  "expression": "amusement",
  "audio": "..."
}
```

A character-switching command may instead produce something similar to:

```json
{
  "type": "character_changed",
  "session_id": "abc123",
  "character": {
    "id": "luna",
    "name": "Princess Luna"
  },
  "reply": "Oh! We were not expecting thee.",
  "expression": "surprise",
  "audio": "..."
}
```

The client therefore does not need to independently track which character should be active. It renders whatever character state is returned by the server.

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
SessionService
CommandService
```

A local implementation could therefore be replaced with a remote service—or vice versa—without changing the public API.

## Development Setup

### Conda Environment

Development is performed inside a dedicated Conda environment named `Pony-Waifu`.

Create the environment with Python 3.12:

```powershell
conda create -n Pony-Waifu python=3.12
```

Activate the environment:

```powershell
conda activate Pony-Waifu
```

### Dependencies

Python dependencies are managed through `requirements.txt`.

After activating the Conda environment, install the project dependencies with:

```powershell
pip install -r requirements.txt
```

When returning to the project later, activate the environment before running or developing the API:

```powershell
conda activate Pony-Waifu
```

## Development Status

🚧 **Very early development**

Current priorities:

1. Establish the FastAPI project structure.
2. Implement basic health and conversation endpoints.
3. Define the character configuration format.
4. Define the session model.
5. Implement basic command processing and character switching.
6. Integrate speech-to-text.
7. Integrate LM Studio.
8. Define structured LLM output for dialogue and expressions.
9. Integrate F5-TTS.
10. Implement character-specific conversation state/history.
11. Build the first lightweight client.

## Why?

Because apparently the reasonable response to wanting to talk to fictional characters is to build an entire local AI voice infrastructure.

## Branching Strategy

The default branch is:

```text
waifu
```

This is a serious software engineering decision and should be treated accordingly.