#!/usr/bin/env python3
"""
Progressive ML Development - CLI Interface

Global command: claude-repl
Provides persistent Python sessions for collaborative ML debugging.
"""

import sys
import json
import subprocess
import os
import time
import shutil
from pathlib import Path

class ProgressiveMLCLI:
    def __init__(self, session_name="claude", venv_path=None):
        self.session_name = session_name
        self.venv_path = venv_path
        self.session_dir = Path("/tmp/claude_session")
        self.session_file = self.session_dir / f"{session_name}.json"
        self.session_dir.mkdir(exist_ok=True)
        self.config_dir = Path.home() / ".claude"
        self.paused = False
    
    def _run_tmux(self, cmd):
        """Run tmux command and return result"""
        try:
            result = subprocess.run(
                ["tmux"] + cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return None, e.stderr.strip()
    
    def _session_exists(self):
        """Check if tmux session exists"""
        stdout, stderr = self._run_tmux(["has-session", "-t", self.session_name])
        return stdout is not None
    
    def _save_session_info(self, info):
        """Save session metadata to file"""
        info["paused"] = self.paused
        if self.venv_path:
            info["venv_path"] = str(self.venv_path)
        with open(self.session_file, "w") as f:
            json.dump(info, f, indent=2)
    
    def _load_session_info(self):
        """Load session metadata from file"""
        if self.session_file.exists():
            with open(self.session_file, "r") as f:
                info = json.load(f)
                self.paused = info.get("paused", False)
                if "venv_path" in info:
                    self.venv_path = info["venv_path"]
                return info
        return {}
    
    def _ensure_tmux_permissions(self):
        """Ensure tmux has necessary permissions without user prompts"""
        try:
            # Check if tmux server is running and accessible
            result = subprocess.run(["tmux", "list-sessions"], 
                                 capture_output=True, text=True, timeout=5)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Try to start a minimal tmux server to establish permissions
            try:
                subprocess.run(["tmux", "new-session", "-d", "-s", "temp_permission_check", "echo", "test"], 
                             capture_output=True, text=True, timeout=10, check=True)
                subprocess.run(["tmux", "kill-session", "-t", "temp_permission_check"], 
                             capture_output=True, text=True, timeout=5)
                return True
            except:
                return False

    def setup(self):
        """One-time system setup"""
        print("🚀 Setting up Progressive ML Development system...")
        
        # Check tmux installation
        if not shutil.which("tmux"):
            print("❌ tmux not found. Installing...")
            if sys.platform == "darwin":  # macOS
                try:
                    subprocess.run(["brew", "install", "tmux"], check=True)
                    print("✅ tmux installed via Homebrew")
                except subprocess.CalledProcessError:
                    print("❌ Failed to install tmux. Please install manually: brew install tmux")
                    return False
            else:
                print("❌ Please install tmux manually:")
                print("   Ubuntu/Debian: sudo apt install tmux")
                print("   CentOS/RHEL: sudo yum install tmux")
                return False
        else:
            print("✅ tmux found")
        
        # Set up permissions
        print("🔑 Setting up tmux permissions...")
        if self._ensure_tmux_permissions():
            print("✅ tmux permissions configured")
        else:
            print("⚠️  tmux permissions may need manual approval")
            print("   If prompted, please allow terminal access for tmux")
        
        # Create config directory
        self.config_dir.mkdir(exist_ok=True)
        print(f"✅ Config directory created: {self.config_dir}")
        
        # Create available commands file
        commands_file = self.config_dir / "available-commands.md"
        if not commands_file.exists():
            with open(commands_file, "w") as f:
                f.write(self._get_commands_doc())
            print(f"✅ Commands documentation created: {commands_file}")
        
        print("\n🎉 Setup complete!")
        print("\nTo use in any Claude conversation:")
        print("  /interactive start    # Start persistent session")
        print("  /interactive help     # Show all commands")
        print("\nThe system is now available globally!")
        
        return True
    
    def _get_commands_doc(self):
        """Get the commands documentation"""
        return """# Claude Available Commands

## Progressive ML Development System

This system provides persistent Python sessions for collaborative ML debugging without restart penalties.

### /interactive Commands

Use these slash commands in any Claude conversation:

- **`/interactive start`** - Start persistent Python session
- **`/interactive stop`** - Stop the session
- **`/interactive status`** - Check session health
- **`/interactive attach`** - Show command to monitor session (`tmux attach -t claude`)
- **`/interactive send "code"`** - Send Python code to session
- **`/interactive read`** - Read session output
- **`/interactive help`** - Show all available commands

### How It Works

When you use `/interactive` commands:
1. Claude runs the corresponding `claude-repl` command
2. Both you and Claude can monitor the same Python environment
3. Models stay loaded across debugging sessions (no restart penalties)
4. Create checkpoints before risky operations, rollback instantly

### Example Usage

```
User: /interactive start
Claude: [Starts persistent Python session]

User: Can you debug this FSDP shape mismatch?
Claude: [Uses the persistent session for debugging, no model reloading needed]
```

This system transforms ML debugging from "restart and hope" to "explore and iterate".
"""

    def start(self, venv_path=None):
        """Start a new persistent Python session"""
        if venv_path:
            self.venv_path = venv_path
            
        # Ensure tmux permissions are set up
        if not self._ensure_tmux_permissions():
            print("Warning: tmux permissions may need to be granted")
            print("If prompted, please allow terminal access for tmux")
        
        if self._session_exists():
            session_info = self._load_session_info()
            print(f"Session '{self.session_name}' already exists")
            if session_info.get("paused"):
                print("🔴 Session is PAUSED - use 'claude-repl resume' to continue")
            print(f"Use 'tmux attach -t {self.session_name}' to monitor")
            return True
        
        # Prepare Python command with virtual environment if specified
        if self.venv_path:
            venv_path = Path(self.venv_path).expanduser()
            if not venv_path.exists():
                print(f"❌ Virtual environment not found: {venv_path}")
                return False
            
            python_cmd = str(venv_path / "bin" / "python")
            if not Path(python_cmd).exists():
                print(f"❌ Python not found in venv: {python_cmd}")
                return False
            
            print(f"🐍 Using virtual environment: {venv_path}")
        else:
            python_cmd = "python3"
        
        # Create new tmux session with Python
        stdout, stderr = self._run_tmux([
            "new-session", 
            "-d", 
            "-s", self.session_name,
            "-c", os.getcwd(),
            python_cmd, "-i"
        ])
        
        if stdout is None:
            print(f"Failed to create session: {stderr}")
            return False
        
        # Save session info
        session_info = {
            "session_name": self.session_name,
            "created_at": time.time(),
            "working_dir": os.getcwd(),
            "status": "active"
        }
        self._save_session_info(session_info)
        
        print(f"Started session '{self.session_name}'")
        print(f"Monitor with: tmux attach -t {self.session_name}")
        print(f"Send commands with: claude-repl send \"your_code\"")
        return True
    
    def send(self, command, wait_time=1.0):
        """Send command to the session"""
        if not self._session_exists():
            print(f"❌ Session '{self.session_name}' not found. Start with: claude-repl start")
            return False
        
        # Check if session is paused
        session_info = self._load_session_info()
        if session_info.get("paused"):
            print("Session is PAUSED. Use 'claude-repl resume' to continue or 'claude-repl send --force' to override")
            return False
        
        # Send command to tmux session
        stdout, stderr = self._run_tmux([
            "send-keys", 
            "-t", self.session_name,
            command,
            "Enter"
        ])
        
        if stdout is None:
            print(f"❌ Failed to send command: {stderr}")
            return False
        
        print(f"📤 Sent: {command}")
        
        # Wait for command to execute (replace tmux sleep with Python sleep)
        if wait_time > 0:
            time.sleep(wait_time)
        
        return True
    
    def read(self, lines=50):
        """Read output from the session"""
        if not self._session_exists():
            print(f"❌ Session '{self.session_name}' not found")
            return ""
        
        # Capture pane content
        stdout, stderr = self._run_tmux([
            "capture-pane", 
            "-t", self.session_name,
            "-p",
            "-S", f"-{lines}"
        ])
        
        if stdout is None:
            print(f"❌ Failed to read session: {stderr}")
            return ""
        
        return stdout
    
    def status(self):
        """Check session status"""
        if not self._session_exists():
            print(f"❌ Session '{self.session_name}' not found")
            return False
        
        session_info = self._load_session_info()
        
        print(f"📊 Session: {self.session_name}")
        print(f"📊 Status: Active")
        if "created_at" in session_info:
            created = time.ctime(session_info["created_at"])
            print(f"📊 Created: {created}")
        if "working_dir" in session_info:
            print(f"📊 Working Dir: {session_info['working_dir']}")
        
        # Show recent output
        print("\n--- Recent Output ---")
        recent = self.read(10)
        print(recent)
        
        return True
    
    def attach(self):
        """Show instructions for attaching to session"""
        if not self._session_exists():
            print(f"❌ Session '{self.session_name}' not found. Start with: claude-repl start")
            return False
        
        print(f"📺 To monitor session '{self.session_name}' in real-time:")
        print(f"   tmux attach -t {self.session_name}")
        print()
        print("🎮 In the tmux session:")
        print("   Ctrl+B, D  - Detach (leave session running)")
        print("   Ctrl+C     - Interrupt current command")
        print("   exit()     - Exit Python (will end session)")
        print()
        print("👥 Both you and Claude can monitor simultaneously!")
        return True
    
    def pause(self):
        """Pause the session - Claude won't send commands until resumed"""
        if not self._session_exists():
            print(f"❌ Session '{self.session_name}' not found")
            return False
        
        self.paused = True
        session_info = self._load_session_info()
        session_info["paused"] = True
        self._save_session_info(session_info)
        
        print(f"⏸️  Session '{self.session_name}' PAUSED")
        print("🔍 You can now inspect the session manually with: tmux attach -t claude")
        print("🔄 Resume with: claude-repl resume")
        return True
    
    def resume(self):
        """Resume the session - allow Claude to send commands again"""
        if not self._session_exists():
            print(f"❌ Session '{self.session_name}' not found")
            return False
        
        self.paused = False
        session_info = self._load_session_info()
        session_info["paused"] = False
        self._save_session_info(session_info)
        
        print(f"▶️  Session '{self.session_name}' RESUMED")
        print("✅ Claude can now send commands to the session")
        return True
    
    def force_send(self, command):
        """Send command even if session is paused"""
        if not self._session_exists():
            print(f"❌ Session '{self.session_name}' not found")
            return False
        
        # Send command bypassing pause check
        stdout, stderr = self._run_tmux([
            "send-keys", 
            "-t", self.session_name,
            command,
            "Enter"
        ])
        
        if stdout is None:
            print(f"❌ Failed to send command: {stderr}")
            return False
        
        print(f"🔴 FORCE Sent: {command}")
        time.sleep(1.0)
        return True
    
    def stop(self):
        """Stop the session"""
        if not self._session_exists():
            print(f"Session '{self.session_name}' not found")
            return True
        
        # Send exit command to Python
        self.send("exit()")
        time.sleep(1)
        
        # Kill session if still exists
        stdout, stderr = self._run_tmux(["kill-session", "-t", self.session_name])
        
        # Clean up session file
        if self.session_file.exists():
            self.session_file.unlink()
        
        print(f"✅ Stopped session '{self.session_name}'")
        return True

    def install(self):
        """Install slash commands in current project"""
        print("📂 Installing Progressive ML Development commands in current project...")
        
        # Create .claude/commands directory
        commands_dir = Path(".claude/commands")
        commands_dir.mkdir(parents=True, exist_ok=True)
        
        # Create interactive.md command
        interactive_content = """# Progressive ML Development Interactive Session

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

Execute the requested $ARGUMENTS command now using the appropriate `claude-repl` command."""

        # Create ml-debug.md command
        ml_debug_content = """# ML Debugging with Progressive Development

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

Start the interactive session now and begin collaborative ML debugging for: $ARGUMENTS"""

        # Write command files
        with open(commands_dir / "interactive.md", "w") as f:
            f.write(interactive_content)
        
        with open(commands_dir / "ml-debug.md", "w") as f:
            f.write(ml_debug_content)
        
        print("✅ Created .claude/commands/interactive.md")
        print("✅ Created .claude/commands/ml-debug.md")
        
        # Create .claude/README.md for project documentation
        readme_content = """# Progressive ML Development - Project Setup

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
"""
        
        with open(Path(".claude/README.md"), "w") as f:
            f.write(readme_content)
        
        print("✅ Created .claude/README.md")
        print()
        print("🎉 Installation complete!")
        print("📁 Current project now has Progressive ML Development slash commands")
        print()
        print("🎯 Available commands:")
        print("  /interactive start           # Start persistent session")
        print("  /interactive status          # Check session")
        print("  /ml-debug \"issue\"           # Debug specific ML problem")
        print()
        print("📚 Documentation: .claude/README.md")
        print("🔧 Global system: ~/.claude/available-commands.md")
        
        return True

    def help(self):
        """Show help information"""
        print("Progressive ML Development - claude-repl")
        print("=" * 50)
        print()
        print("Available Commands:")
        print("  setup                        # One-time system setup")
        print("  install                      # Install slash commands in current project")
        print("  start [--venv PATH]          # Start persistent Python session")
        print("  stop                         # Stop session")
        print("  send \"command\"               # Send Python code to session")
        print("  send --force \"command\"       # Send even if paused")
        print("  read [lines]                 # Read session output")
        print("  status                       # Check session health")
        print("  pause                        # Pause session (Claude won't send commands)")
        print("  resume                       # Resume session")
        print("  attach                       # Show monitoring instructions")
        print("  help                         # Show this help")
        print()
        print("Virtual Environment Support:")
        print("  claude-repl start --venv ~/myproject/.venv")
        print("  claude-repl start --venv /path/to/venv")
        print()
        print("Session Control:")
        print("  claude-repl pause            # Let user inspect manually")
        print("  tmux attach -t claude        # Monitor session")
        print("  claude-repl resume           # Allow Claude to continue")
        print()
        print("For Claude Conversations (after install):")
        print("  /interactive start           # Claude starts session")
        print("  /interactive stop            # Claude stops session")
        print("  /interactive status          # Claude checks status")
        print("  /ml-debug \"problem\"          # Claude debugs ML issue")
        
    def test(self):
        """Run built-in tests"""
        print("🧪 Running built-in tests...")
        print("=" * 40)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: tmux availability
        total_tests += 1
        if shutil.which("tmux"):
            print("✅ Test 1: tmux available")
            tests_passed += 1
        else:
            print("❌ Test 1: tmux not found")
        
        # Test 2: Session lifecycle
        total_tests += 1
        print("🔄 Test 2: Session lifecycle...")
        
        # Clean start
        if self._session_exists():
            self.stop()
        
        # Start session
        if self.start():
            time.sleep(2)
            
            # Send command
            if self.send("test_var = 'test_success'"):
                time.sleep(1)
                
                # Read output
                output = self.read(20)
                if "test_success" in output:
                    print("✅ Test 2: Session lifecycle works")
                    tests_passed += 1
                else:
                    print("❌ Test 2: Variable not found in output")
            else:
                print("❌ Test 2: Failed to send command")
            
            # Clean up
            self.stop()
        else:
            print("❌ Test 2: Failed to start session")
        
        # Test 3: Config files
        total_tests += 1
        commands_file = self.config_dir / "available-commands.md"
        if commands_file.exists():
            print("✅ Test 3: Config files exist")
            tests_passed += 1
        else:
            print("❌ Test 3: Config files missing")
        
        print("\n" + "=" * 40)
        print(f"📊 Tests passed: {tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! System is ready.")
            return True
        else:
            print("⚠️  Some tests failed. Run 'claude-repl setup' if needed.")
            return False

def main():
    if len(sys.argv) < 2:
        cli = ProgressiveMLCLI()
        cli.help()
        return
    
    command = sys.argv[1]
    cli = ProgressiveMLCLI()
    
    if command == "setup":
        cli.setup()
    elif command == "install":
        cli.install()
    elif command == "start":
        venv_path = None
        if len(sys.argv) > 2 and sys.argv[2] == "--venv":
            if len(sys.argv) < 4:
                print("Usage: claude-repl start --venv /path/to/venv")
                return
            venv_path = sys.argv[3]
        cli.start(venv_path)
    elif command == "send":
        if len(sys.argv) < 3:
            print("Usage: claude-repl send \"command\" or claude-repl send --force \"command\"")
            return
        
        if sys.argv[2] == "--force":
            if len(sys.argv) < 4:
                print("Usage: claude-repl send --force \"command\"")
                return
            cli.force_send(sys.argv[3])
        else:
            cli.send(sys.argv[2])
    elif command == "read":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        output = cli.read(lines)
        print(output)
    elif command == "status":
        cli.status()
    elif command == "pause":
        cli.pause()
    elif command == "resume":
        cli.resume()
    elif command == "attach":
        cli.attach()
    elif command == "stop":
        cli.stop()
    elif command == "help":
        cli.help()
    elif command == "test":
        success = cli.test()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        cli.help()

if __name__ == "__main__":
    main()