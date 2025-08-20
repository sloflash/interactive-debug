# ML Debugging with Progressive Development

Start an interactive ML debugging session for collaborative problem-solving without restart penalties.

## Context: $ARGUMENTS

The user is experiencing: $ARGUMENTS

## Actions to Take

1. **Start Interactive Session**: Use `claude-repl start` to create persistent Python environment
2. **Load Models Once**: Import and load ML models/data in the persistent session  
3. **Debug Iteratively**: Use the session for step-by-step debugging without reloading
4. **Create Checkpoints**: Save state before risky operations for instant rollback
5. **Collaborate**: Both user and Claude monitor the same session via `tmux attach -t claude`

## Key Benefits

- ⚡ **No Restart Penalties**: Models stay loaded across debugging attempts
- 🔄 **Checkpoint/Rollback**: Save state, try approaches, rollback instantly
- 👥 **Real-time Collaboration**: Shared session monitoring
- 🧠 **Context Preservation**: Debugging state persists across iterations

## Common ML Debugging Scenarios

- FSDP shape mismatches
- Memory allocation errors  
- Training loop instabilities
- Model architecture experiments
- Data loading issues

Start the interactive session using `claude-repl start` and begin collaborative ML debugging for: $ARGUMENTS

If claude-repl command is not found, install the system:
```bash
curl -sSL https://raw.githubusercontent.com/sloflash/interactive-debug/main/src/install_universal.py | python3
```