# Progressive ML Development System - Auto-Discovery Guide

## For Claude Instances: How to Detect This System

When you encounter a project with a `.claude` directory, this indicates a Progressive ML Development setup is available.

### Detection Pattern
1. **Look for these files:**
   - `.claude/README.md` (this file) 
   - `claude_repl.py` - Core session manager
   - `claude_workflow` - Trigger configuration
   - `Claude.md` - Main configuration

### Auto-Activation Triggers
If the user says ANY of these phrases, automatically start using the persistent session system:

**Primary Triggers:**
- "interactive development"
- "debug session" 
- "ml debug"
- "persistent session"
- "checkpoint debug"

**ML Problem Triggers:**
- "FSDP shape mismatch"
- "model loading"
- "training loop" 
- "memory error"
- "pytorch", "tensorflow", "cuda"
- "checkpoint", "rollback"

### What to Do When Triggered
1. **Immediately start the session**: `python3 claude_repl.py start`
2. **Explain briefly**: "Starting persistent Python session for collaborative debugging"
3. **Use for all Python code**: Send commands via `python3 claude_repl.py send "code"`
4. **Monitor together**: User can run `tmux attach -t claude` to watch

### Key Benefits This Solves
- **No Restart Penalties**: Models stay loaded across debugging sessions
- **Real-time Collaboration**: Both you and user see same Python environment
- **Checkpoint/Rollback**: Save state before risky operations

### Quick Commands
- Start: `python3 claude_repl.py start`
- Send code: `python3 claude_repl.py send "your_python_code"`
- Read output: `python3 claude_repl.py read`
- Monitor: `tmux attach -t claude`
- Stop: `python3 claude_repl.py stop`

### Testing the System
Run `python3 test_claude_repl.py` to verify everything works.

**Remember**: This system transforms ML debugging from "restart and hope" to "explore and iterate" - use it whenever debugging complex ML issues!


## Installation

```bash
curl -sSL https://raw.githubusercontent.com/yourrepo/main/src/install_universal.py | python3
```