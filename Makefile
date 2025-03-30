.PHONY: all setup lint format check install dev clean run

# Default target - installs dependencies, runs lint and format, then starts the app
all: install dev lint-all run

# Python executable (uv run)
PYTHON := uv run

# Install dependencies
install:
	uv pip install hatchling
	uv pip install -e .

# Install development dependencies
dev:
	uv pip install hatchling
	uv pip install -e ".[dev]"

# Run linting checks
check:
	ruff check .

# Run linting fixes
lint:
	ruff check --fix . || true

# Run formatter
format:
	ruff format . || true

# Run both linting and formatting
lint-all: lint format

# Setup environment - install all dependencies
setup: install dev

# Run the application
run:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Please install it first."; exit 1; }
	$(PYTHON) -m livetranslate.main

# Clean temporary files and caches
clean:
	rm -rf **/__pycache__
	rm -rf .ruff_cache
	rm -rf .pytest_cache