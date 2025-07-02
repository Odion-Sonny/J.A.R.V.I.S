# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a local JARVIS-like AI assistant built with ElectronJS (frontend) and Python backend. The system uses GPT4All as the local LLM and implements a Model Control Protocol (MCP) for command routing and OS integration.

## Development Commands

### Quick Start
```bash
python3 start_jarvis.py          # Automated full setup and launch
```

### Manual Development Setup
```bash
# Backend setup
cd python-backend
pip3 install -r requirements.txt
python3 ipc_server.py --host 127.0.0.1 --port 8000

# Frontend setup (new terminal)
cd electron-app
npm install
npm start                        # Production mode
npm run dev                      # Development mode with dev flags
```

### Build Commands
```bash
# Electron builds
cd electron-app
npm run build                    # All platforms
npm run build-mac                # macOS specific
npm run build-win                # Windows specific
npm run build-linux              # Linux specific
npm run pack                     # Development build

# Distribution installer
python3 build_installer.py
```

### Testing Commands
```bash
python3 run_tests.py             # Comprehensive test suite (Python + JS)

# Individual test suites
cd electron-app && npm test     # Jest frontend tests
cd python-backend && pytest -v  # Python backend tests
python3 -m pytest tests/test_backend.py -v --tb=short
```

### Linting Commands
```bash
cd electron-app && npm run lint # ESLint for JavaScript
```

## Architecture

The application follows a three-layer architecture:
- **Electron Frontend**: Cross-platform desktop UI with chat interface
- **Python MCP Layer**: Command routing and intent parsing using FastAPI/WebSocket
- **GPT4All + Task Handlers**: Local LLM with Python function executors

### Communication Flow
```
Electron UI ↔ WebSocket/IPC ↔ Python Backend ↔ GPT4All LLM
     ↓                          ↓
User Input               Task Executors (Files, Alarms, System)
```

## Key Components

### Backend (`python-backend/`)
- `ipc_server.py` - FastAPI server with WebSocket endpoints
- `llm_interface.py` - GPT4All integration with system prompts
- `intent_parser.py` - Extracts actionable intent from LLM JSON responses
- `task_router.py` - Routes parsed intents to appropriate handlers
- `tasks/` - Task execution modules:
  - `file_tasks.py` - Document creation, search, read/write
  - `alarm_tasks.py` - Reminders and background monitoring
  - `system_tasks.py` - System info, app launching, safe commands
  - `voice_tasks.py` - TTS and speech recognition

### Frontend (`electron-app/`)
- `src/main-working.js` - Main Electron process (primary entry point)
- `src/renderer.js` - Renderer process coordinator
- `src/components/chat.js` - Chat interface component
- `src/components/settings.js` - Settings management with electron-store
- `src/utils/ipc.js` - IPC communication utilities

## JSON-Based LLM Communication

The system uses structured JSON responses from GPT4All for deterministic parsing:

```json
{
  "response": "I'll create a file called hello.txt for you.",
  "action": "create_document", 
  "params": {"name": "hello.txt", "content": "Hello World!"}
}
```

Action handlers are mapped in `task_router.py`:
```python
self.action_handlers = {
    'create_document': self.file_tasks.create_document,
    'set_alarm': self.alarm_tasks.set_alarm,
    'open_app': self.system_tasks.open_app,
}
```

## Testing Architecture

- **`run_tests.py`** - Master test runner executing frontend + backend tests
- **Frontend**: Jest with Electron mocking (`__mocks__/electron.js`)
- **Backend**: pytest with async support, coverage reporting, and mocking
- **Dependencies**: Install test deps via `pip install -r tests/requirements.txt`

## Security Considerations

- Command whitelisting prevents dangerous operations
- Permission prompts for destructive actions
- Local processing (no external API calls for LLM)
- Input validation before task execution
- Comprehensive logging for all system interactions