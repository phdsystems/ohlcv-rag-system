# Quick Start Guide

## Fastest Setup (3 commands)

```bash
# 1. Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
uv sync

# 3. Run the system
uv run python main.py
```

## Using Make Commands

```bash
# Full automated setup
make setup

# Run the system
make run

# Other useful commands
make help           # Show all available commands
make install        # Install dependencies
make install-dev    # Install with dev tools
make clean          # Clean cache files
make format         # Format code with black
make lint           # Lint with ruff
make test           # Run tests
make fetch-data     # Fetch fresh OHLCV data
make shell          # Interactive Python shell
```

## Manual Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates venv automatically)
uv sync

# Copy environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run the system
uv run python main.py
```

## Key Points

- `uv sync` automatically creates and manages the virtual environment
- No need for `pip` - uv handles everything
- Use `uv run <command>` to run commands in the project environment
- The Makefile provides convenient shortcuts for common tasks