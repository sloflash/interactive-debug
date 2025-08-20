#!/usr/bin/env python3
"""
Test suite for claude_repl.py - Progressive ML Development Session Manager
"""

import subprocess
import time
import json
import os
from pathlib import Path

def run_repl_command(cmd_list):
    """Run claude_repl command and return output"""
    try:
        result = subprocess.run(
            ["python3", "claude_repl.py"] + cmd_list,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"

def test_session_lifecycle():
    """Test complete session lifecycle: start -> send -> read -> stop"""
    print("=== Testing Session Lifecycle ===")
    
    # 1. Start session
    print("1. Starting session...")
    returncode, stdout, stderr = run_repl_command(["start"])
    print(f"Start result: {returncode}")
    print(f"Start output: {stdout}")
    if stderr:
        print(f"Start stderr: {stderr}")
    
    # Wait a moment for session to initialize
    time.sleep(2)
    
    # 2. Send basic Python command
    print("\n2. Sending test command...")
    returncode, stdout, stderr = run_repl_command(["send", "x = 42; print(f'Test value: {x}')"])
    print(f"Send result: {returncode}")
    print(f"Send output: {stdout}")
    
    # Wait for command to execute
    time.sleep(1)
    
    # 3. Read output
    print("\n3. Reading session output...")
    returncode, stdout, stderr = run_repl_command(["read", "20"])
    print(f"Read result: {returncode}")
    print(f"Read output:\n{stdout}")
    
    # 4. Check status
    print("\n4. Checking session status...")
    returncode, stdout, stderr = run_repl_command(["status"])
    print(f"Status result: {returncode}")
    print(f"Status output: {stdout}")
    
    # 5. Send more complex command
    print("\n5. Testing Python functionality...")
    returncode, stdout, stderr = run_repl_command(["send", "import sys; print(f'Python version: {sys.version}')"])
    print(f"Python test result: {returncode}")
    
    time.sleep(1)
    
    # Read the result
    returncode, stdout, stderr = run_repl_command(["read", "10"])
    print(f"Python test output:\n{stdout}")
    
    # 6. Stop session
    print("\n6. Stopping session...")
    returncode, stdout, stderr = run_repl_command(["stop"])
    print(f"Stop result: {returncode}")
    print(f"Stop output: {stdout}")
    
    return True

def test_session_persistence():
    """Test that variables persist across commands"""
    print("\n=== Testing Session Persistence ===")
    
    # Start session
    run_repl_command(["start"])
    time.sleep(2)
    
    # Set a variable
    print("1. Setting variable...")
    run_repl_command(["send", "test_var = 'persistence_test'"])
    time.sleep(1)
    
    # Use the variable in another command
    print("2. Using variable...")
    run_repl_command(["send", "print(f'Variable persists: {test_var}')"])
    time.sleep(1)
    
    # Read result
    returncode, stdout, stderr = run_repl_command(["read", "10"])
    print(f"Persistence test output:\n{stdout}")
    
    # Check if persistence worked
    if "persistence_test" in stdout:
        print("✓ Variable persistence works!")
    else:
        print("✗ Variable persistence failed!")
    
    # Clean up
    run_repl_command(["stop"])
    return "persistence_test" in stdout

def test_ml_simulation():
    """Test ML-like workflow with imports and data"""
    print("\n=== Testing ML Workflow Simulation ===")
    
    # Start session
    run_repl_command(["start"])
    time.sleep(2)
    
    # Import common libraries (that should be available)
    print("1. Testing imports...")
    run_repl_command(["send", "import json, os, sys, time"])
    time.sleep(1)
    
    # Create some data structures
    print("2. Creating data structures...")
    run_repl_command(["send", "data = {'model': 'test', 'epochs': 10, 'batch_size': 32}"])
    time.sleep(1)
    
    # Simulate model training loop
    print("3. Simulating training loop...")
    training_code = """
for epoch in range(3):
    loss = 1.0 / (epoch + 1)
    print(f'Epoch {epoch+1}/3, Loss: {loss:.4f}')
"""
    run_repl_command(["send", training_code])
    time.sleep(2)
    
    # Read results
    returncode, stdout, stderr = run_repl_command(["read", "20"])
    print(f"ML simulation output:\n{stdout}")
    
    # Test checkpoint simulation
    print("4. Simulating checkpoint...")
    run_repl_command(["send", "checkpoint = {'model_state': data, 'epoch': 3}; print(f'Checkpoint saved: {checkpoint}')"])
    time.sleep(1)
    
    # Read final results
    returncode, stdout, stderr = run_repl_command(["read", "15"])
    print(f"Final output:\n{stdout}")
    
    # Clean up
    run_repl_command(["stop"])
    
    return "Epoch" in stdout and "checkpoint" in stdout.lower()

def test_error_handling():
    """Test error handling and recovery"""
    print("\n=== Testing Error Handling ===")
    
    # Start session
    run_repl_command(["start"])
    time.sleep(2)
    
    # Send invalid Python code
    print("1. Testing syntax error handling...")
    run_repl_command(["send", "print('missing closing quote"])
    time.sleep(1)
    
    # Read error
    returncode, stdout, stderr = run_repl_command(["read", "10"])
    print(f"Error output:\n{stdout}")
    
    # Send valid code after error
    print("2. Testing recovery after error...")
    run_repl_command(["send", "print('Recovery successful!')"])
    time.sleep(1)
    
    # Read recovery
    returncode, stdout, stderr = run_repl_command(["read", "10"])
    print(f"Recovery output:\n{stdout}")
    
    # Clean up
    run_repl_command(["stop"])
    
    return "Recovery successful" in stdout

def run_all_tests():
    """Run all tests and report results"""
    print("Starting claude_repl.py test suite...")
    print("=" * 50)
    
    tests = [
        ("Session Lifecycle", test_session_lifecycle),
        ("Session Persistence", test_session_persistence),
        ("ML Workflow Simulation", test_ml_simulation),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}")
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
            print(f"Result: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            results.append((test_name, f"ERROR: {e}"))
            print(f"Result: ERROR - {e}")
        
        print("-" * 30)
    
    # Final report
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    for test_name, result in results:
        status_icon = "✓" if result == "PASS" else "✗"
        print(f"{status_icon} {test_name}: {result}")
    
    passed = sum(1 for _, result in results if result == "PASS")
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)