#!/bin/bash
"""
Auto-test script for claude_repl.py
Watches for changes and automatically runs tests
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run tests
run_tests() {
    echo -e "${BLUE}[$(date)] Running tests...${NC}"
    echo "=" * 60
    
    if python3 test_claude_repl.py; then
        echo -e "${GREEN}[$(date)] ✓ Tests PASSED${NC}"
        return 0
    else
        echo -e "${RED}[$(date)] ✗ Tests FAILED${NC}"
        return 1
    fi
}

# Function to watch files
watch_files() {
    echo -e "${YELLOW}Watching claude_repl.py and test_claude_repl.py for changes...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    
    # Run tests initially
    run_tests
    echo ""
    
    # Check if fswatch is available (macOS)
    if command -v fswatch >/dev/null 2>&1; then
        echo -e "${BLUE}Using fswatch for file monitoring${NC}"
        fswatch -o claude_repl.py test_claude_repl.py | while read f; do
            echo -e "${YELLOW}[$(date)] File changed, running tests...${NC}"
            run_tests
            echo ""
        done
    # Check if inotifywait is available (Linux)
    elif command -v inotifywait >/dev/null 2>&1; then
        echo -e "${BLUE}Using inotifywait for file monitoring${NC}"
        while inotifywait -e modify claude_repl.py test_claude_repl.py; do
            echo -e "${YELLOW}[$(date)] File changed, running tests...${NC}"
            run_tests
            echo ""
        done
    else
        # Fallback: polling method
        echo -e "${YELLOW}No file watcher found, using polling method${NC}"
        last_mod_repl=$(stat -f %m claude_repl.py 2>/dev/null || stat -c %Y claude_repl.py)
        last_mod_test=$(stat -f %m test_claude_repl.py 2>/dev/null || stat -c %Y test_claude_repl.py)
        
        while true; do
            sleep 2
            
            current_mod_repl=$(stat -f %m claude_repl.py 2>/dev/null || stat -c %Y claude_repl.py)
            current_mod_test=$(stat -f %m test_claude_repl.py 2>/dev/null || stat -c %Y test_claude_repl.py)
            
            if [[ "$current_mod_repl" != "$last_mod_repl" ]] || [[ "$current_mod_test" != "$last_mod_test" ]]; then
                echo -e "${YELLOW}[$(date)] File changed, running tests...${NC}"
                run_tests
                echo ""
                last_mod_repl=$current_mod_repl
                last_mod_test=$current_mod_test
            fi
        done
    fi
}

# Function to just run tests once
run_once() {
    run_tests
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [watch|test|help]"
    echo ""
    echo "Commands:"
    echo "  watch  - Watch files and auto-run tests on changes (default)"
    echo "  test   - Run tests once and exit"
    echo "  help   - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./watch_and_test.sh        # Start watching files"
    echo "  ./watch_and_test.sh test   # Run tests once"
    echo "  ./watch_and_test.sh watch  # Same as default"
}

# Parse command line arguments
case "${1:-watch}" in
    "watch")
        watch_files
        ;;
    "test")
        run_once
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac