@echo off
REM Bruno AI Server Development Script (Windows)
REM Runs the FastAPI server with hot reload for development

echo Starting Bruno AI Server in development mode...

REM Change to server directory
cd /d "%~dp0\..\server"

REM Check if Poetry is available
py -m poetry --version >nul 2>&1
if errorlevel 1 (
    echo Poetry not found. Please install Poetry first.
    echo Visit: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

REM Install dependencies if not already installed
if not exist "poetry.lock" (
    echo Installing dependencies...
    py -m poetry install
)

REM Start the development server
echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop the server
py -m poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
