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

# Install enhanced Python REPLs with colored syntax highlighting
echo "Installing enhanced Python REPLs..."

# Install ptpython (preferred)
PTPYTHON_SUCCESS=false
if python3 -m pip install --user ptpython 2>/dev/null; then
    echo "ptpython installed - best colored REPL available"
    PTPYTHON_SUCCESS=true
elif /usr/bin/python3 -m pip install --user ptpython 2>/dev/null; then
    echo "ptpython installed with system Python"
    PTPYTHON_SUCCESS=true
elif python -m pip install --user ptpython 2>/dev/null; then
    echo "ptpython installed with python"
    PTPYTHON_SUCCESS=true
fi

# Install IPython as fallback
IPYTHON_SUCCESS=false
if [ "$PTPYTHON_SUCCESS" = false ]; then
    if python3 -m pip install --user ipython 2>/dev/null; then
        echo "IPython installed as fallback REPL"
        IPYTHON_SUCCESS=true
    elif /usr/bin/python3 -m pip install --user ipython 2>/dev/null; then
        echo "IPython installed with system Python"
        IPYTHON_SUCCESS=true
    elif python -m pip install --user ipython 2>/dev/null; then
        echo "IPython installed with python"
        IPYTHON_SUCCESS=true
    fi
fi

# Summary
echo ""
echo "Enhanced REPL Installation Summary:"
if [ "$PTPYTHON_SUCCESS" = true ]; then
    echo "  * ptpython - Primary colored REPL with syntax highlighting"
elif [ "$IPYTHON_SUCCESS" = true ]; then
    echo "  * IPython - Fallback REPL with syntax highlighting"
else
    echo "  * Warning: No enhanced REPLs installed - will use standard Python"
    echo "  * Install manually: pip install ptpython"
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
            # Check for enhanced REPLs
            if $python_cmd -c "import ptpython" 2>/dev/null; then
                export CLAUDE_REPL_ENHANCED="ptpython"
            elif $python_cmd -c "import IPython" 2>/dev/null; then
                export CLAUDE_REPL_ENHANCED="ipython"
            fi
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

# Configure tmux colors for ClaudeBuddy
echo "Setting up tmux color configuration..."

# Create the tmux-claude.conf file
cat > ~/.tmux-claude.conf << 'EOF'
# ClaudeBuddy tmux color configuration
# Colors for command execution feedback: blue=commands, green=success, red=errors

# Status bar colors
set -g status-style 'bg=colour24,fg=colour15'  # Blue background, white text
set -g status-left-style 'bg=colour24,fg=colour15,bold'
set -g status-right-style 'bg=colour24,fg=colour15'

# Window status colors
set -g window-status-style 'bg=colour24,fg=colour15'
set -g window-status-current-style 'bg=colour28,fg=colour15,bold'  # Green for active
set -g window-status-activity-style 'bg=colour196,fg=colour15'  # Red for activity
set -g window-status-bell-style 'bg=colour196,fg=colour15,bold'  # Red for bell

# Pane border colors
set -g pane-border-style 'fg=colour240'  # Gray for inactive
set -g pane-active-border-style 'fg=colour28'  # Green for active

# Message colors (for tmux command feedback)
set -g message-style 'bg=colour28,fg=colour15,bold'  # Green background
set -g message-command-style 'bg=colour24,fg=colour15,bold'  # Blue background

# Mode colors (copy mode, etc.)
set -g mode-style 'bg=colour24,fg=colour15,bold'  # Blue background

# Clock color
set -g clock-mode-colour colour28  # Green

# Status bar content with better formatting
set -g status-left '[#{session_name}] '
set -g status-left-length 20
set -g status-right '#{?window_bigger,[#{window_offset_x}#,#{window_offset_y}] ,}"#{=21:pane_title}" %H:%M %d-%b-%y'
set -g status-right-length 50

# Enable visual notification of activity in other windows
setw -g monitor-activity on
set -g visual-activity off

# Set window notifications
set -g window-status-format ' #I:#W#{?window_flags,#{window_flags}, } '
set -g window-status-current-format ' #I:#W#{?window_flags,#{window_flags}, } '

# Copy mode colors
set -g copy-mode-match-style 'bg=colour24,fg=colour15'
set -g copy-mode-current-match-style 'bg=colour28,fg=colour15,bold'
EOF

# Safely configure tmux to source our color config
TMUX_CONF="$HOME/.tmux.conf"
SOURCE_LINE="source-file ~/.tmux-claude.conf"

if [ -f "$TMUX_CONF" ]; then
    # Check if our config is already sourced
    if ! grep -q "tmux-claude.conf" "$TMUX_CONF"; then
        echo "" >> "$TMUX_CONF"
        echo "# ClaudeBuddy color configuration" >> "$TMUX_CONF"
        echo "$SOURCE_LINE" >> "$TMUX_CONF"
        echo "Added ClaudeBuddy colors to existing tmux config"
    else
        echo "ClaudeBuddy colors already configured in tmux"
    fi
else
    # Create minimal tmux config that sources our colors
    cat > "$TMUX_CONF" << EOF
# Minimal tmux configuration with ClaudeBuddy colors
$SOURCE_LINE
EOF
    echo "Created new tmux config with ClaudeBuddy colors"
fi

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