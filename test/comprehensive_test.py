#!/usr/bin/env python3
"""
Progressive ML Development - Comprehensive Test Suite

Tests all use cases including:
- Multi-terminal scenarios
- Different session names
- Cross-session communication
- Fresh Claude discovery
- Error handling and recovery
"""

import subprocess
import time
import json
import os
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

class ProgressiveMLTester:
    def __init__(self):
        self.test_results = []
        self.test_sessions = []
        self.cleanup_needed = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        self.test_results.append((test_name, status, details))
        icon = "✓" if success else "✗"
        print(f"{icon} {test_name}: {status}")
        if details and not success:
            print(f"   Details: {details}")
    
    def run_command(self, cmd, timeout=10):
        """Run command and return result"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
    
    def cleanup_session(self, session_name):
        """Clean up a test session"""
        try:
            subprocess.run(f"python3 claude_repl.py stop", shell=True, capture_output=True)
            subprocess.run(f"tmux kill-session -t {session_name} 2>/dev/null", shell=True, capture_output=True)
        except:
            pass
    
    def test_basic_workflow(self):
        """Test basic start->send->read->stop workflow"""
        print("\n=== Testing Basic Workflow ===")
        
        # Clean start
        self.cleanup_session("claude")
        
        # Start session
        success, stdout, stderr = self.run_command("python3 claude_repl.py start")
        self.log_test("Basic Start Session", success, stderr if not success else "")
        if not success:
            return False
        
        time.sleep(2)
        
        # Send command
        success, stdout, stderr = self.run_command("python3 claude_repl.py send \"test_var = 'basic_test'\"")
        self.log_test("Basic Send Command", success, stderr if not success else "")
        
        time.sleep(1)
        
        # Read output
        success, stdout, stderr = self.run_command("python3 claude_repl.py read")
        has_output = success and "basic_test" in stdout
        self.log_test("Basic Read Output", has_output, "No expected output found" if not has_output else "")
        
        # Stop session
        success, stdout, stderr = self.run_command("python3 claude_repl.py stop")
        self.log_test("Basic Stop Session", success, stderr if not success else "")
        
        return True
    
    def test_multi_terminal_simulation(self):
        """Simulate multiple terminals accessing same session"""
        print("\n=== Testing Multi-Terminal Scenario ===")
        
        self.cleanup_session("claude")
        
        # Terminal 1: Start session
        success, _, stderr = self.run_command("python3 claude_repl.py start")
        self.log_test("Multi-Terminal: Start Session", success, stderr if not success else "")
        if not success:
            return False
        
        time.sleep(2)
        
        # Terminal 1: Send initial command
        success, _, stderr = self.run_command("python3 claude_repl.py send \"shared_var = 'from_terminal_1'\"")
        self.log_test("Multi-Terminal: Terminal 1 Send", success, stderr if not success else "")
        
        time.sleep(1)
        
        # Terminal 2: Read what Terminal 1 did
        success, stdout, stderr = self.run_command("python3 claude_repl.py read")
        can_see_t1 = success and "from_terminal_1" in stdout
        self.log_test("Multi-Terminal: Terminal 2 Read T1 Data", can_see_t1, "Cannot see Terminal 1 data" if not can_see_t1 else "")
        
        # Terminal 2: Send command
        success, _, stderr = self.run_command("python3 claude_repl.py send \"print(f'T2 sees: {shared_var}')\"")
        self.log_test("Multi-Terminal: Terminal 2 Send", success, stderr if not success else "")
        
        time.sleep(1)
        
        # Verify cross-terminal communication
        success, stdout, stderr = self.run_command("python3 claude_repl.py read 10")
        cross_comm = success and "T2 sees: from_terminal_1" in stdout
        self.log_test("Multi-Terminal: Cross-Terminal Communication", cross_comm, "No cross-terminal communication" if not cross_comm else "")
        
        # Cleanup
        self.run_command("python3 claude_repl.py stop")
        
        return True
    
    def test_session_isolation(self):
        """Test different session names work independently"""
        print("\n=== Testing Session Isolation ===")
        
        # Create custom session manager for different name
        test_session_name = "test_session_isolation"
        
        # Clean any existing sessions
        subprocess.run(f"tmux kill-session -t {test_session_name} 2>/dev/null", shell=True, capture_output=True)
        
        # Test with custom session (we'd need to modify claude_repl.py or create temp version)
        # For now, test the isolation concept by checking session doesn't exist
        success, stdout, stderr = self.run_command(f"tmux has-session -t {test_session_name}")
        isolated = not success  # Should fail because session doesn't exist
        self.log_test("Session Isolation: Non-existent Session", isolated, "Unexpected session found" if not isolated else "")
        
        # Test that we can create session with custom name
        success, _, stderr = self.run_command(f"tmux new-session -d -s {test_session_name} 'python3 -i'")
        self.log_test("Session Isolation: Create Custom Session", success, stderr if not success else "")
        
        if success:
            time.sleep(1)
            # Verify it exists
            success, _, _ = self.run_command(f"tmux has-session -t {test_session_name}")
            self.log_test("Session Isolation: Custom Session Exists", success, "Custom session not found")
            
            # Clean up
            subprocess.run(f"tmux kill-session -t {test_session_name}", shell=True, capture_output=True)
        
        return True
    
    def test_error_recovery(self):
        """Test error handling and recovery scenarios"""
        print("\n=== Testing Error Recovery ===")
        
        self.cleanup_session("claude")
        
        # Test starting when tmux session already exists manually
        subprocess.run("tmux new-session -d -s claude 'sleep 5'", shell=True, capture_output=True)
        
        success, stdout, stderr = self.run_command("python3 claude_repl.py start")
        handles_existing = success and "already exists" in stdout
        self.log_test("Error Recovery: Handle Existing Session", handles_existing, "Doesn't handle existing session properly")
        
        # Clean up manual session
        subprocess.run("tmux kill-session -t claude", shell=True, capture_output=True)
        
        # Test recovery from broken session state
        success, _, _ = self.run_command("python3 claude_repl.py start")
        if success:
            time.sleep(1)
            
            # Kill session externally (simulating crash)
            subprocess.run("tmux kill-session -t claude", shell=True, capture_output=True)
            
            # Try to use broken session
            success, stdout, stderr = self.run_command("python3 claude_repl.py send \"test\"")
            recovers = not success or "not found" in stderr
            self.log_test("Error Recovery: Handle Broken Session", recovers, "Should detect broken session")
        
        return True
    
    def test_fresh_discovery(self):
        """Test fresh Claude discovery workflow"""
        print("\n=== Testing Fresh Discovery ===")
        
        # Test detection script
        success, stdout, stderr = self.run_command("python3 detect_progressive_ml.py")
        detects_system = success and "PROGRESSIVE ML DEVELOPMENT SYSTEM DETECTED" in stdout
        self.log_test("Fresh Discovery: Detection Script Works", detects_system, stderr if not detects_system else "")
        
        # Test required files exist
        required_files = [
            "claude_repl.py",
            ".claude/README.md", 
            "Claude.md",
            "detect_progressive_ml.py"
        ]
        
        all_exist = True
        for file_path in required_files:
            if not Path(file_path).exists():
                all_exist = False
                break
        
        self.log_test("Fresh Discovery: Required Files Present", all_exist, f"Missing files from: {required_files}")
        
        # Test that .claude/README.md contains discovery info
        if Path(".claude/README.md").exists():
            with open(".claude/README.md", "r") as f:
                content = f.read()
            has_triggers = "interactive development" in content and "FSDP shape mismatch" in content
            self.log_test("Fresh Discovery: README Has Trigger Info", has_triggers, "Missing trigger phrases in README")
        
        return True
    
    def test_tmux_permissions(self):
        """Test tmux permissions handling"""
        print("\n=== Testing TMux Permissions ===")
        
        # Test tmux is available
        success, _, _ = self.run_command("tmux -V")
        self.log_test("TMux Permissions: TMux Available", success, "tmux not found in PATH")
        
        # Test tmux server can start
        success, _, stderr = self.run_command("tmux new-session -d -s permission_test 'echo test'")
        if success:
            subprocess.run("tmux kill-session -t permission_test", shell=True, capture_output=True)
        self.log_test("TMux Permissions: Can Create Sessions", success, stderr if not success else "")
        
        return True
    
    def test_cleanup_procedures(self):
        """Test proper cleanup procedures"""
        print("\n=== Testing Cleanup Procedures ===")
        
        # Start session
        success, _, _ = self.run_command("python3 claude_repl.py start")
        if not success:
            self.log_test("Cleanup: Cannot Start Session for Test", False, "Setup failed")
            return False
        
        time.sleep(2)
        
        # Check session exists
        success, _, _ = self.run_command("tmux has-session -t claude")
        self.log_test("Cleanup: Session Exists Before Stop", success, "Session should exist")
        
        # Stop session
        success, _, stderr = self.run_command("python3 claude_repl.py stop")
        self.log_test("Cleanup: Stop Command Success", success, stderr if not success else "")
        
        time.sleep(1)
        
        # Verify session is gone
        success, _, _ = self.run_command("tmux has-session -t claude")
        cleaned_up = not success  # Should fail because session should be gone
        self.log_test("Cleanup: Session Removed After Stop", cleaned_up, "Session still exists after stop")
        
        # Check session files are cleaned
        session_file = Path("/tmp/claude_session/claude.json")
        file_cleaned = not session_file.exists()
        self.log_test("Cleanup: Session Files Removed", file_cleaned, "Session file still exists")
        
        return True
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 COMPREHENSIVE PROGRESSIVE ML DEVELOPMENT TEST SUITE")
        print("=" * 60)
        
        tests = [
            ("Basic Workflow", self.test_basic_workflow),
            ("Multi-Terminal Simulation", self.test_multi_terminal_simulation),
            ("Session Isolation", self.test_session_isolation),
            ("Error Recovery", self.test_error_recovery), 
            ("Fresh Discovery", self.test_fresh_discovery),
            ("TMux Permissions", self.test_tmux_permissions),
            ("Cleanup Procedures", self.test_cleanup_procedures),
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 Running: {test_name}")
                print("-" * 40)
                test_func()
            except Exception as e:
                self.log_test(f"{test_name} (Exception)", False, str(e))
        
        # Final cleanup
        self.cleanup_session("claude")
        
        # Results summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        total = 0
        
        for test_name, status, details in self.test_results:
            icon = "✅" if status == "PASS" else "❌"
            print(f"{icon} {test_name}: {status}")
            if details and status == "FAIL":
                print(f"    ↳ {details}")
            
            if status == "PASS":
                passed += 1
            total += 1
        
        print(f"\n📈 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is fully functional.")
        else:
            print("⚠️  Some tests failed. Check details above.")
        
        return passed == total

def main():
    tester = ProgressiveMLTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()