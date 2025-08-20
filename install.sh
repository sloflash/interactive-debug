#!/bin/bash

echo "Progressive ML Development - Universal Install"
echo "=============================================="

# Install the package - try multiple Python environments
echo "Installing progressive-ml-dev..."

INSTALL_SUCCESS=false

# Try current Python first
if python3 -m pip install --user --upgrade progressive-ml-dev 2>/dev/null; then
    echo "Installed with current Python"
    INSTALL_SUCCESS=true
elif /usr/bin/python3 -m pip install --user --upgrade progressive-ml-dev 2>/dev/null; then
    echo "Installed with system Python"
    INSTALL_SUCCESS=true
elif python -m pip install --user --upgrade progressive-ml-dev 2>/dev/null; then
    echo "Installed with python"
    INSTALL_SUCCESS=true
fi

if [ "$INSTALL_SUCCESS" = false ]; then
    echo "Warning: Could not install with pip, but continuing..."
    echo "You may need to install manually: pip install progressive-ml-dev"
fi

# Create universal wrapper that works with any Python
echo "Creating universal claude-repl command..."
cat > /tmp/claude-repl << 'EOF'
#!/bin/bash
# Universal claude-repl - works with any Python environment

# Determine which Python to use
PYTHON_CMD="python3"
if [[ -n "$VIRTUAL_ENV" ]]; then
    PYTHON_CMD="$VIRTUAL_ENV/bin/python"
elif [[ -n "$CONDA_DEFAULT_ENV" ]]; then
    PYTHON_CMD="python"
fi

# Try current Python first, then others
for python_cmd in $PYTHON_CMD python3 python python3.12 python3.11 python3.10 python3.9 python3.8; do
    if command -v $python_cmd >/dev/null 2>&1; then
        if $python_cmd -c "import progressive_ml_dev" 2>/dev/null; then
            exec $python_cmd -m progressive_ml_dev.cli "$@"
        fi
    fi
done

echo "progressive-ml-dev not found in any Python environment"
echo "Install with: pip install progressive-ml-dev"
exit 1
EOF

chmod +x /tmp/claude-repl

# Create ~/.local/bin if it doesn't exist
mkdir -p ~/.local/bin

# Install to user bin (no sudo needed)
cp /tmp/claude-repl ~/.local/bin/claude-repl
chmod +x ~/.local/bin/claude-repl

echo "SUCCESS: claude-repl installed to ~/.local/bin"

# Test if it's accessible
if command -v claude-repl >/dev/null 2>&1; then
    echo "claude-repl is accessible globally"
    claude-repl setup
else
    echo "Note: ~/.local/bin may not be in PATH"
    echo "Add this to your shell profile if needed:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "DONE! Usage:"
echo "  claude-repl start        # Works with any Python"
echo "  claude-repl install      # Add to any project"

rm -f /tmp/claude-repl