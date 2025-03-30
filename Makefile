.PHONY: all lint format check install dev clean pip-install

# Default target - only runs lint and format
all: lint-all

# Python executable (for running scripts if needed)
PYTHON := python

# Install dependencies
install:
	uv pip install setuptools wheel
	uv pip install -e .

# Install development dependencies
dev:
	uv pip install setuptools wheel
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

# Alternative installation using pip instead of uv
pip-install:
	pip install setuptools wheel
	pip install -e .
	pip install -e ".[dev]"

# Clean temporary files and caches
clean:
	rm -rf **/__pycache__
	rm -rf .ruff_cache
	rm -rf .pytest_cache