#!/usr/bin/env python3
"""
Progressive ML Development - Universal Installer
Works with any Python version (3.8+) and automatically handles PATH

Usage: curl -sSL https://raw.githubusercontent.com/yourrepo/main/install_universal.py | python3
"""

import sys
import subprocess
import os
import site
from pathlib import Path

def run_command(cmd, check=True):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def get_user_bin_path():
    """Get the correct user bin path for any Python version"""
    try:
        # Get user site-packages directory
        user_base = site.getuserbase()
        user_bin = Path(user_base) / "bin"
        return user_bin
    except:
        # Fallback method
        success, output, _ = run_command("python3 -m site --user-base", check=False)
        if success:
            user_base = output.strip()
            return Path(user_base) / "bin"
    
    return None

def ensure_claude_repl_accessible():
    """Ensure claude-repl is accessible from PATH"""
    # First check if it's already accessible
    success, _, _ = run_command("claude-repl --help", check=False)
    if success:
        print("✅ claude-repl already accessible")
        return True
    
    # Try to find claude-repl in user bin
    user_bin = get_user_bin_path()
    if user_bin:
        claude_repl_path = user_bin / "claude-repl"
        if claude_repl_path.exists():
            # Create symlink in /usr/local/bin (standard PATH location)
            try:
                subprocess.run(["sudo", "ln", "-sf", str(claude_repl_path), "/usr/local/bin/claude-repl"], 
                             check=True, capture_output=True)
                print("✅ Created symlink to /usr/local/bin/claude-repl")
                return True
            except:
                print("⚠️  Could not create symlink (need sudo)")
        
        # Fallback: Add to PATH temporarily and permanently
        current_path = os.environ.get("PATH", "")
        if str(user_bin) not in current_path:
            print(f"⚠️  Adding {user_bin} to PATH")
            
            # Update current session
            os.environ["PATH"] = f"{user_bin}:{current_path}"
            
            # Add to shell profile
            shell = os.environ.get("SHELL", "")
            profile_file = "~/.zshrc" if "zsh" in shell else "~/.bashrc"
            profile_path = Path.home() / profile_file.replace("~/", "")
            
            try:
                export_line = f'export PATH="{user_bin}:$PATH"\n'
                
                # Check if already there
                if profile_path.exists():
                    with open(profile_path, "r") as f:
                        if str(user_bin) in f.read():
                            print("✅ PATH already in profile")
                            return True
                
                # Add to profile
                with open(profile_path, "a") as f:
                    f.write(f"\n# Progressive ML Development\n{export_line}")
                print(f"✅ Added to {profile_file}")
                return True
                
            except Exception as e:
                print(f"⚠️  Could not update profile: {e}")
    
    return False

def test_claude_repl_command():
    """Test if claude-repl command works"""
    # First try direct command
    success, _, _ = run_command("claude-repl help", check=False)
    if success:
        print("✅ claude-repl command works")
        return True
    
    # Try with python module
    success, _, _ = run_command("python3 -m progressive_ml_dev.cli help", check=False)
    if success:
        print("✅ claude-repl works via python module")
        return True
    
    print("❌ claude-repl command not accessible")
    return False

def check_python():
    """Check Python version compatibility"""
    version = sys.version_info
    if version < (3, 8):
        print(f"❌ Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} compatible")
    return True

def install_package():
    """Install progressive-ml-dev package"""
    print("📦 Installing progressive-ml-dev...")
    
    # Use the same Python interpreter that's running this script
    python_cmd = sys.executable
    
    # Try system-wide install first (will be in standard PATH)
    success, stdout, stderr = run_command(f"{python_cmd} -m pip install progressive-ml-dev", check=False)
    
    if success:
        print("✅ Package installed system-wide")
        return True
    else:
        print("⚠️  System install failed, trying user install...")
        # Fallback to user install
        success, stdout, stderr = run_command(f"{python_cmd} -m pip install --user progressive-ml-dev", check=False)
        
        if success:
            print("✅ Package installed to user directory")
            return True
        else:
            print(f"❌ Installation failed: {stderr}")
            return False

def run_setup():
    """Run system setup"""
    print("🔧 Running system setup...")
    
    # Try direct command first
    success, stdout, stderr = run_command("claude-repl setup", check=False)
    
    if not success:
        # Try with the same Python interpreter that's running this script
        python_cmd = sys.executable
        success, stdout, stderr = run_command(f"{python_cmd} -m progressive_ml_dev.cli setup", check=False)
    
    if success:
        print("✅ Setup completed")
        return True
    else:
        print(f"❌ Setup failed: {stderr}")
        return False

def run_tests():
    """Run verification tests"""
    print("🧪 Running tests...")
    
    # Try direct command first
    success, stdout, stderr = run_command("claude-repl test", check=False)
    
    if not success:
        # Try with the same Python interpreter
        python_cmd = sys.executable
        success, stdout, stderr = run_command(f"{python_cmd} -m progressive_ml_dev.cli test", check=False)
    
    if success:
        print("✅ All tests passed")
        return True
    else:
        print(f"⚠️  Some tests failed: {stderr}")
        return False

def show_final_info():
    """Show final usage information"""
    print("\n" + "="*60)
    print("🎉 INSTALLATION COMPLETE!")
    print("="*60)
    
    print(f"\n🐍 Installed for Python {sys.version.split()[0]}")
    
    user_bin = get_user_bin_path()
    if user_bin:
        print(f"📁 Binary location: {user_bin}/claude-repl")
    
    print("\n🎯 Usage in any project:")
    print("  claude-repl install   # Add slash commands to project")
    print("  /interactive start    # Start persistent session")
    print("  /interactive status   # Check session")
    print("  /ml-debug \"issue\"     # Debug ML problems")
    
    print("\n💻 Direct commands:")
    print("  claude-repl help      # Show all options")
    print("  claude-repl test      # Verify system")
    
    print("\n📚 Documentation:")
    print("  ~/.claude/available-commands.md")
    
    print("\n🚀 To use in a new project:")
    print("  1. cd your-project")
    print("  2. claude-repl install")
    print("  3. Use /interactive commands with Claude")
    
    print("\n✨ Ready for ML debugging without restart penalties!")

def main():
    print("🧠 Progressive ML Development - Universal Installer")
    print("="*60)
    
    # Check Python compatibility
    if not check_python():
        sys.exit(1)
    
    # Install package
    if not install_package():
        print("\n❌ Installation failed")
        sys.exit(1)
    
    # Ensure claude-repl is accessible
    path_setup = ensure_claude_repl_accessible()
    
    # Run system setup
    if not run_setup():
        print("\n❌ Setup failed")
        sys.exit(1)
    
    # Test the installation
    run_tests()
    
    # Test command accessibility
    command_works = test_claude_repl_command()
    
    # Show final info
    show_final_info()
    
    if not command_works and not path_setup:
        print("\n⚠️  You may need to restart your terminal for the PATH to take effect")
        print("Then test with: claude-repl help")
    
    print("\n✨ Installation successful!")

if __name__ == "__main__":
    main()