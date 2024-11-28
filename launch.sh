#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create and activate virtual environment if it doesn't exist
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/venv"
fi

# Activate virtual environment
source "$PROJECT_ROOT/venv/bin/activate"

# Install requirements
echo "Installing/updating requirements..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Verify streamlit installation
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit not found, installing..."
    pip install streamlit
fi

# Install package in development mode
echo "Installing computer_use package..."
pip install -e "$PROJECT_ROOT"

# Set environment variables
export ANTHROPIC_API_KEY="your_api_key_here"
export WIDTH=1280
export HEIGHT=800

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Change to project root directory
cd "$PROJECT_ROOT"

# Run the app
python -m computer_use.run 