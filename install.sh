#!/bin/bash
set -e

echo "Progressive ML Development - One-Command Install"
echo "================================================"

# Detect Python
PYTHON_CMD=""
for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8; do
    if command -v $cmd >/dev/null 2>&1; then
        VERSION=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if [[ "$VERSION" > "3.7" ]] || [[ "$VERSION" == "3.8" ]] || [[ "$VERSION" == "3.9" ]] || [[ "$VERSION" == "3.10" ]] || [[ "$VERSION" == "3.11" ]] || [[ "$VERSION" == "3.12" ]]; then
            PYTHON_CMD=$cmd
            echo "Found compatible Python: $cmd (version $VERSION)"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo "No compatible Python found. Need Python 3.8+"
    exit 1
fi

# Install/upgrade package
echo "Installing progressive-ml-dev..."
$PYTHON_CMD -m pip install --upgrade progressive-ml-dev

# Find where it was installed
USER_BIN=$($PYTHON_CMD -c "import site, os; print(os.path.join(site.getuserbase(), 'bin'))" 2>/dev/null || echo "")
SYSTEM_BIN=$($PYTHON_CMD -c "import sys, os; print(os.path.dirname(sys.executable))" 2>/dev/null || echo "")

# Try to find claude-repl
CLAUDE_REPL_PATH=""
for bin_dir in "$USER_BIN" "$SYSTEM_BIN" "/usr/local/bin" "/opt/homebrew/bin"; do
    if [[ -f "$bin_dir/claude-repl" ]]; then
        CLAUDE_REPL_PATH="$bin_dir/claude-repl"
        echo "Found claude-repl at: $CLAUDE_REPL_PATH"
        break
    fi
done

# If not in standard locations, create symlink
if [[ -z "$CLAUDE_REPL_PATH" ]] && [[ -f "$USER_BIN/claude-repl" ]]; then
    echo "Creating symlink to /usr/local/bin..."
    if sudo ln -sf "$USER_BIN/claude-repl" /usr/local/bin/claude-repl 2>/dev/null; then
        echo "Symlink created successfully"
        CLAUDE_REPL_PATH="/usr/local/bin/claude-repl"
    else
        echo "Warning: Could not create symlink (continuing anyway)"
        CLAUDE_REPL_PATH="$USER_BIN/claude-repl"
    fi
fi

# Test if accessible
if command -v claude-repl >/dev/null 2>&1; then
    echo "SUCCESS: claude-repl is accessible"
    claude-repl setup
    echo ""
    echo "Installation complete!"
    echo "Usage:"
    echo "  claude-repl start"
    echo "  claude-repl install  # In any project to add slash commands"
elif [[ -n "$CLAUDE_REPL_PATH" ]]; then
    echo "claude-repl installed at: $CLAUDE_REPL_PATH"
    $CLAUDE_REPL_PATH setup
    echo ""
    echo "Installation complete!"
    echo "Usage:"
    echo "  $CLAUDE_REPL_PATH start"
    echo "  $CLAUDE_REPL_PATH install  # In any project"
    echo ""
    echo "To make globally accessible, add to PATH or create alias:"
    echo "  alias claude-repl='$CLAUDE_REPL_PATH'"
else
    echo "Installation completed but claude-repl location unclear"
    echo "Try: python3 -m progressive_ml_dev.cli help"
fi