# Progressive ML Development - Project Setup

This project includes Progressive ML Development slash commands for collaborative debugging without restart penalties.

## Available Slash Commands

- `/interactive start` - Start persistent Python session
- `/interactive stop` - Stop the session
- `/interactive status` - Check session health
- `/interactive attach` - Show monitoring instructions  
- `/interactive send "code"` - Send Python code to session
- `/interactive read` - Read session output
- `/interactive help` - Show all commands
- `/ml-debug "problem"` - Start ML debugging for specific issue

## How It Works

These commands use the global `claude-repl` system to create persistent Python sessions where:
- Models stay loaded across debugging attempts (no restart penalties)
- Both you and Claude monitor the same environment
- Create checkpoints before risky operations, rollback instantly
- Real-time collaboration via `tmux attach -t claude`

## System Requirements

Ensure the global system is installed:
```bash
pip install progressive-ml-dev
claude-repl setup
```

## Usage Example

```
User: /interactive start
Claude: [Starts persistent session]

User: Let's debug this FSDP shape mismatch
Claude: [Uses persistent session, loads model once, debugs iteratively]

User: tmux attach -t claude  # Monitor in real-time
```

This transforms ML debugging from "restart and hope" to "explore and iterate".
