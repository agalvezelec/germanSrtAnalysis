#!/bin/bash

# --- Configuration ---
# !!! ADJUST THIS PATH !!!
PROJECT_DIR="$HOME/Documents/prj/Python/germanSrtAnalysis"
# --- End Configuration ---

# Full paths based on project directory
PYTHON_VENV="$PROJECT_DIR/.venv/bin/python"
SCRIPT_PY="$PROJECT_DIR/germanSrtAnalysis.py"

# Check if files exist
if [ ! -f "$PYTHON_VENV" ]; then
    echo "Error: Python interpreter not found at $PYTHON_VENV" >&2
    exit 1
fi

if [ ! -f "$SCRIPT_PY" ]; then
    echo "Error: Python script not found at $SCRIPT_PY" >&2
    exit 1
fi

# Execute the Python script using the venv interpreter,
# passing ALL arguments received by this wrapper to the script.
"$PYTHON_VENV" "$SCRIPT_PY" "$@"
