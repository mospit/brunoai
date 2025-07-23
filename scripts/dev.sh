#!/bin/bash

# Bruno AI Server Development Script
# Runs the FastAPI server with hot reload for development

echo "Starting Bruno AI Server in development mode..."

# Change to server directory
cd "$(dirname "$0")/../server"

# Check if Poetry is available
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Please install Poetry first."
    echo "Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Install dependencies if not already installed
if [ ! -d ".venv" ] && [ ! -f "poetry.lock" ]; then
    echo "Installing dependencies..."
    poetry install
fi

# Start the development server
echo "Starting server at http://localhost:8000"
echo "Press Ctrl+C to stop the server"
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
