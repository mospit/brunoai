.PHONY: help install-hooks format lint test server flutter clean

# Default target
help:
	@echo "Available commands:"
	@echo "  install-hooks    Install pre-commit hooks"
	@echo "  format          Format code (black, isort, ruff, dart format)"
	@echo "  lint            Run linters (ruff, flake8)"
	@echo "  test            Run tests"
	@echo "  server          Run Bruno AI server"
	@echo "  flutter         Run Flutter app" 
	@echo "  clean           Clean build artifacts"

# Install pre-commit hooks
install-hooks:
	@echo "Installing pre-commit hooks..."
	pre-commit install

# Format code
format:
	@echo "Formatting Python code..."
	cd server && black .
	cd server && isort .
	cd server && ruff format .
	@echo "Formatting Dart code..."
	flutter format lib/

# Run linters
lint:
	@echo "Running Python linters..."
	cd server && ruff check . --fix
	cd server && flake8 .

# Run tests
test:
	@echo "Running Python tests..."
	cd server && python -m pytest
	@echo "Running Flutter tests..."
	flutter test

# Run server
server:
	@echo "Starting Bruno AI server..."
	cd server && python main.py

# Run Flutter app
flutter:
	@echo "Starting Flutter app..."
	flutter run

# Clean build artifacts
clean:
	@echo "Cleaning Python build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "Cleaning Flutter build artifacts..."
	flutter clean
