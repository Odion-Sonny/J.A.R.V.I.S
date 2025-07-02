# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a local JARVIS-like AI assistant built with ElectronJS (frontend) and Python backend. The system uses GPT4All as the local LLM and implements a Model Control Protocol (MCP) for command routing and OS integration.

## Architecture

The application follows a three-layer architecture:
- **Electron Frontend**: Cross-platform desktop UI with chat interface
- **Python MCP Layer**: Command routing and intent parsing
- **GPT4All + Task Handlers**: Local LLM with Python function executors

Communication between layers uses IPC via WebSocket or child_process.

## Project Structure

The project is organized into two main components:
- `electron-app/` - Frontend ElectronJS application
- `python-backend/` - Backend MCP with modules:
  - `llm_interface.py` - GPT4All integration
  - `intent_parser.py` - Extracts actionable intent from LLM output
  - `task_router.py` - Routes parsed intents to handlers
  - `tasks/` - Task execution modules (file operations, alarms, system tasks)
  - `ipc_server.py` - Handles Electron communication

## Development Phases

1. **Phase 1**: Core CLI prototype (Python only)
2. **Phase 2**: Add Electron UI with IPC connection
3. **Phase 3**: Expand task capabilities
4. **Phase 4**: Voice integration and system tray
5. **Phase 5**: Plugin system (optional)

## Intent Parsing

The system supports two approaches:
- Simple keyword + regex matching on LLM responses
- Structured JSON output from LLM for deterministic parsing

Example JSON structure:
```json
{
  "action": "create_document",
  "params": {
    "name": "meeting.txt",
    "content": "Project begins next week."
  }
}
```

## Security Considerations

- Implement command whitelisting to prevent dangerous operations
- Add permission prompts for destructive actions
- Maintain logging for all system interactions
- Validate all user inputs before execution

## Task Categories

The system handles several task types:
- File operations (create, search, read, delete)
- System integration (open apps, get system info)
- Alarms and reminders
- Voice synthesis (optional)