#!/usr/bin/env python3
"""
Progressive ML Development - Persistent Python Session Manager

Manages persistent tmux sessions for collaborative ML debugging without restart penalties.
Both Claude and user can access the same Python environment for real-time collaboration.
"""

import sys
import json
import subprocess
import os
import time
from pathlib import Path

class ClaudeREPL:
    def __init__(self, session_name="claude"):
        self.session_name = session_name
        self.session_dir = Path("/tmp/claude_session")
        self.session_file = self.session_dir / f"{session_name}.json"
        self.session_dir.mkdir(exist_ok=True)
    
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
    
    def _get_best_repl(self):
        """Detect the best available Python REPL"""
        repls = [
            ("ptpython", ["ptpython", "--config-file", self._create_ptpython_config()]),
            ("ipython", ["ipython"]),
            ("python-rich", ["python3", "-i", "-c", self._get_rich_init()]),
            ("python", ["python3", "-i"])
        ]
        
        for name, cmd in repls:
            try:
                if name == "ptpython":
                    result = subprocess.run(["ptpython", "--version"], 
                                         capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return name, cmd
                elif name == "ipython":
                    result = subprocess.run(["ipython", "--version"], 
                                         capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return name, cmd
                elif name == "python-rich":
                    result = subprocess.run(["python3", "-c", "import rich"], 
                                         capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return name, cmd
                else:
                    return name, cmd
            except:
                continue
        
        return "python", ["python3", "-i"]
    
    def _create_ptpython_config(self):
        """Create a ptpython config file with good dark theme"""
        config_dir = Path("/tmp/claude_ptpython")
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.py"
        
        config_content = '''"""
ptpython configuration for better dark theme coding
"""
from ptpython.repl import PythonRepl

def configure(repl: PythonRepl) -> None:
    """
    Configuration method. This is called during the start-up of ptpython.
    """
    # Use a dark-friendly color scheme
    repl.use_code_colorscheme("monokai")
    
    # Enable syntax highlighting
    repl.highlight_matching_parenthesis = True
    
    # Show function signature while typing
    repl.show_signature = True
    
    # Show docstring in a popup
    repl.show_docstring = True
    
    # Enable auto-completion
    repl.enable_auto_suggest = True
    
    # Show line numbers
    repl.show_line_numbers = True
    
    # Wrap lines instead of scrolling horizontally
    repl.wrap_lines = True
    
    # Enable mouse support
    repl.enable_mouse_support = True
    
    # Better prompt style
    repl.prompt_style = "classic"  # Options: 'classic', 'ipython'
    
    # Set max brightness for better dark background readability
    repl.max_brightness = 0.6
'''
        
        with open(config_file, "w") as f:
            f.write(config_content)
        
        return str(config_file)
    
    def _get_rich_init(self):
        """Get Rich initialization command for fallback"""
        return (
            "try:\n"
            "    from rich import pretty, traceback, console\n"
            "    pretty.install()\n"
            "    traceback.install(show_locals=True)\n"
            "    import sys\n"
            "    sys.ps1 = '\\x01\\x1b[1;34m\\x02>>> \\x01\\x1b[0m\\x02'\n"
            "    sys.ps2 = '\\x01\\x1b[1;36m\\x02... \\x01\\x1b[0m\\x02'\n"
            "    console = console.Console()\n"
            "    print('Rich enhanced REPL activated!')\n"
            "except ImportError:\n"
            "    import sys\n"
            "    sys.ps1 = '\\x01\\x1b[1;34m\\x02>>> \\x01\\x1b[0m\\x02'\n"
            "    sys.ps2 = '\\x01\\x1b[1;36m\\x02... \\x01\\x1b[0m\\x02'\n"
            "    print('\\x1b[33mColored prompts activated\\x1b[0m')\n"
        )
    
    def _session_exists(self):
        """Check if tmux session exists"""
        stdout, stderr = self._run_tmux(["has-session", "-t", self.session_name])
        return stdout is not None
    
    def _save_session_info(self, info):
        """Save session metadata to file"""
        with open(self.session_file, "w") as f:
            json.dump(info, f, indent=2)
    
    def _load_session_info(self):
        """Load session metadata from file"""
        if self.session_file.exists():
            with open(self.session_file, "r") as f:
                return json.load(f)
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

    def start(self):
        """Start a new persistent Python session"""
        # Ensure tmux permissions are set up
        if not self._ensure_tmux_permissions():
            print("Warning: tmux permissions may need to be granted")
            print("If prompted, please allow terminal access for tmux")
        
        if self._session_exists():
            print(f"Session '{self.session_name}' already exists")
            print(f"Use 'tmux attach -t {self.session_name}' to monitor")
            return True
        
        # Detect and use the best available REPL
        repl_name, repl_cmd = self._get_best_repl()
        
        print(f"Using {repl_name} for enhanced Python experience")
        
        # Create new tmux session with best available REPL
        stdout, stderr = self._run_tmux([
            "new-session", 
            "-d", 
            "-s", self.session_name,
            "-c", os.getcwd(),
        ] + repl_cmd)
        
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
        print(f"Send commands with: python3 claude_repl.py send \"your_code\"")
        return True
    
    def send(self, command):
        """Send command to the session"""
        if not self._session_exists():
            print(f"Session '{self.session_name}' not found. Start with: python3 claude_repl.py start")
            return False
        
        # Add extra spacing before command for better visual separation
        self._run_tmux([
            "send-keys", 
            "-t", self.session_name,
            "print()",
            "Enter"
        ])
        
        # Send command to tmux session
        stdout, stderr = self._run_tmux([
            "send-keys", 
            "-t", self.session_name,
            command,
            "Enter"
        ])
        
        if stdout is None:
            print(f"Failed to send command: {stderr}")
            return False
        
        print(f"\033[94mSent:\033[0m {command}")
        return True
    
    def read(self, lines=50):
        """Read output from the session"""
        if not self._session_exists():
            print(f"Session '{self.session_name}' not found")
            return ""
        
        # Capture pane content
        stdout, stderr = self._run_tmux([
            "capture-pane", 
            "-t", self.session_name,
            "-p",
            "-S", f"-{lines}"
        ])
        
        if stdout is None:
            print(f"Failed to read session: {stderr}")
            return ""
        
        return stdout
    
    def status(self):
        """Check session status"""
        if not self._session_exists():
            print(f"Session '{self.session_name}' not found")
            return False
        
        # Get session info
        stdout, stderr = self._run_tmux([
            "list-sessions", 
            "-F", "#{session_name}: #{session_created} #{session_attached}"
        ])
        
        if stdout is None:
            print(f"Failed to get status: {stderr}")
            return False
        
        session_info = self._load_session_info()
        
        print(f"Session: {self.session_name}")
        print(f"Status: Active")
        if "created_at" in session_info:
            created = time.ctime(session_info["created_at"])
            print(f"Created: {created}")
        if "working_dir" in session_info:
            print(f"Working Dir: {session_info['working_dir']}")
        
        # Show recent output
        print("\n--- Recent Output ---")
        recent = self.read(10)
        print(recent)
        
        return True
    
    def monitor(self):
        """Instructions for monitoring the session"""
        if not self._session_exists():
            print(f"Session '{self.session_name}' not found. Start with: python3 claude_repl.py start")
            return False
        
        print(f"To monitor session '{self.session_name}' in real-time:")
        print(f"  tmux attach -t {self.session_name}")
        print()
        print("In the tmux session:")
        print("  Ctrl+B, D  - Detach (leave session running)")
        print("  Ctrl+C     - Interrupt current command")
        print("  exit()     - Exit Python (will end session)")
        print()
        print("Both you and Claude can monitor simultaneously!")
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
        
        print(f"Stopped session '{self.session_name}'")
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 claude_repl.py start                 # Start persistent session")
        print("  python3 claude_repl.py send \"command\"        # Send command to session")
        print("  python3 claude_repl.py read [lines]          # Read session output")
        print("  python3 claude_repl.py status                # Check session status")
        print("  python3 claude_repl.py monitor               # Show monitoring instructions")
        print("  python3 claude_repl.py stop                  # Stop session")
        print()
        print("For real-time monitoring: tmux attach -t claude")
        return
    
    repl = ClaudeREPL()
    command = sys.argv[1]
    
    if command == "start":
        repl.start()
    elif command == "send":
        if len(sys.argv) < 3:
            print("Usage: python3 claude_repl.py send \"command\"")
            return
        repl.send(sys.argv[2])
    elif command == "read":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        output = repl.read(lines)
        print(output)
    elif command == "status":
        repl.status()
    elif command == "monitor":
        repl.monitor()
    elif command == "stop":
        repl.stop()
    else:
        print(f"Unknown command: {command}")
        print("Valid commands: start, send, read, status, monitor, stop")

if __name__ == "__main__":
    main()