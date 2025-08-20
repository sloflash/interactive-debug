# Progressive ML Development Interactive Session

You are now using the Progressive ML Development system for collaborative debugging without restart penalties.

## Command: $ARGUMENTS

Handle the interactive command: $ARGUMENTS

Available commands:
- **start** - Start persistent Python session using `claude-repl start`
- **stop** - Stop the session using `claude-repl stop`  
- **status** - Check session health using `claude-repl status`
- **attach** - Show monitoring instructions using `claude-repl attach`
- **send "code"** - Send Python code to session using `claude-repl send "code"`
- **read** - Read session output using `claude-repl read`
- **help** - Show all available commands using `claude-repl help`

## How This Works

When you use /interactive commands:
1. I run the corresponding `claude-repl` command via the Bash tool
2. Both you and I can monitor the same Python environment  
3. Models stay loaded across debugging sessions (no restart penalties)
4. Create checkpoints before risky operations, rollback instantly

## Session Monitoring

You can monitor the session in real-time with:
```bash
tmux attach -t claude
```

Both you and I can observe the same execution environment simultaneously.

## Example Usage

```
/interactive start
/interactive send "import torch; model = load_large_model()"  
/interactive read
# Model stays loaded for iterative debugging
```

Execute the requested $ARGUMENTS command using `claude-repl $ARGUMENTS`.

If claude-repl is not found, the system needs to be installed first:
```bash
curl -sSL https://raw.githubusercontent.com/yourrepo/main/src/install_universal.py | python3
```